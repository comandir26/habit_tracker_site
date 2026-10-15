from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Guild, GuildHabit, GuildMember
from .serializers import GuildHabitSerializer, GuildSerializer, TodayHabitSerializer


class GuildListCreateView(generics.ListCreateAPIView):
    """Lists only the authenticated user's guilds and creates a guild with its owner."""

    serializer_class = GuildSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Guild.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .prefetch_related("memberships__user")
            .distinct()
        )

    @transaction.atomic
    def perform_create(self, serializer):
        guild = serializer.save(owner=self.request.user)
        GuildMember.objects.create(
            guild=guild,
            user=self.request.user,
            role=GuildMember.Role.OWNER,
        )


class GuildDetailView(generics.RetrieveAPIView):
    """A guild is visible only to users who are members of it."""

    serializer_class = GuildSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Guild.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .prefetch_related("memberships__user")
            .distinct()
        )


class GuildHabitListCreateView(generics.ListCreateAPIView):
    serializer_class = GuildHabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_guild(self):
        if not hasattr(self, "guild"):
            self.guild = get_object_or_404(
                Guild.objects.filter(memberships__user=self.request.user),
                pk=self.kwargs["guild_id"],
            )
        return self.guild

    def get_queryset(self):
        return GuildHabit.objects.filter(guild=self.get_guild())

    def create(self, request, *args, **kwargs):
        if self.get_guild().owner_id != request.user.pk:
            raise PermissionDenied("Only the guild owner can create habits.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(guild=self.get_guild())


class HabitDifficultyListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response([
            {"value": value, "label": label, "base_xp": GuildHabit.BASE_XP[value]}
            for value, label in GuildHabit.Difficulty.choices
        ])


class TodayHabitListView(APIView):
    """Returns only the request user's habits scheduled for their local day."""

    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get_user_timezone(user):
        try:
            return ZoneInfo(user.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            # Existing accounts may contain an old invalid value. Falling back
            # keeps the list usable until the profile can be corrected.
            return ZoneInfo(settings.TIME_ZONE)

    def get(self, request):
        user_timezone = self.get_user_timezone(request.user)
        local_date = timezone.localdate(timezone=user_timezone)
        local_weekday = local_date.isoweekday()
        accessible_habits = (
            GuildHabit.objects.filter(guild__memberships__user=request.user)
            .select_related("guild")
            .distinct()
        )
        today_habits = [
            habit for habit in accessible_habits
            if habit.schedule == GuildHabit.Schedule.DAILY or local_weekday in habit.weekdays
        ]

        return Response({
            "date": local_date.isoformat(),
            "timezone": str(user_timezone),
            "habits": TodayHabitSerializer(today_habits, many=True).data,
        })

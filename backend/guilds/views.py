from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Guild, GuildHabit, GuildMember, HabitCompletion
from .serializers import GuildHabitSerializer, GuildSerializer, HabitCompletionSerializer


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


class HabitCompletionCreateView(APIView):
    """Mark a habit complete once per user and calendar day, awarding XP once."""

    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, habit_id):
        habit = get_object_or_404(
            GuildHabit.objects.select_related("guild"),
            pk=habit_id,
            guild__memberships__user=request.user,
        )
        serializer = HabitCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        completed_on = serializer.validated_data.get("completed_on", timezone.localdate())

        completion, created = HabitCompletion.objects.get_or_create(
            habit=habit,
            user=request.user,
            completed_on=completed_on,
        )
        membership = GuildMember.objects.get(guild=habit.guild, user=request.user)
        if created:
            GuildMember.objects.filter(pk=membership.pk).update(xp=F("xp") + habit.xp_reward)
            membership.refresh_from_db(fields=("xp",))

        return Response({
            "habit_id": habit.pk,
            "completed_on": completion.completed_on,
            "created": created,
            "awarded_xp": habit.xp_reward if created else 0,
            "member_id": membership.pk,
            "member_xp": membership.xp,
        })

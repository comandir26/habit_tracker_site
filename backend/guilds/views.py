from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import INVITE_CODE_ALPHABET, INVITE_CODE_LENGTH, Guild, GuildHabit, GuildInvite, GuildMember, HabitCompletion
from .serializers import (
    GuildHabitSerializer, GuildInviteSerializer, GuildSerializer, HabitCompletionSerializer, InvitePreviewSerializer,
    TodayHabitSerializer,
)


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


class GuildInviteListCreateView(generics.ListCreateAPIView):
    """Only the owner manages invites; members get 403 and outsiders do not see the guild."""

    serializer_class = GuildInviteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_guild(self):
        if not hasattr(self, "guild"):
            self.guild = get_object_or_404(
                Guild.objects.filter(memberships__user=self.request.user),
                pk=self.kwargs["guild_id"],
            )
        return self.guild

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.get_guild().owner_id != request.user.pk:
            raise PermissionDenied("Only the guild owner can manage invites.")

    def get_queryset(self):
        return GuildInvite.objects.filter(guild=self.get_guild(), expires_at__gt=timezone.now())

    def perform_create(self, serializer):
        serializer.save(guild=self.get_guild(), created_by=self.request.user)


class InviteDetailView(APIView):
    """Any signed-in user holding a valid code may preview the guild it leads to."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, code):
        invite = get_object_or_404(
            GuildInvite.objects.select_related("guild__owner"),
            code=GuildInvite.normalize_code(code),
        )
        if invite.is_expired:
            return Response({"detail": "This invite has expired."}, status=status.HTTP_410_GONE)
        return Response(InvitePreviewSerializer(invite, context={"request": request}).data)


class InviteJoinView(APIView):
    """Redeem a valid invitation without changing an existing membership."""

    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, code):
        code = GuildInvite.normalize_code(code)
        if len(code) != INVITE_CODE_LENGTH or any(char not in INVITE_CODE_ALPHABET for char in code):
            raise ValidationError({"code": "Use the eight-character code from your invitation."})
        invite = get_object_or_404(GuildInvite.objects.select_for_update(), code=code)
        if invite.is_expired:
            return Response({"detail": "This invite has expired."}, status=status.HTTP_410_GONE)

        # get_or_create and unique_guild_member also protect simultaneous joins
        # through different invitations to the same guild.
        _membership, created = GuildMember.objects.get_or_create(
            guild_id=invite.guild_id,
            user=request.user,
            defaults={"role": GuildMember.Role.MEMBER, "xp": 0},
        )
        return Response(
            {"guild_id": invite.guild_id, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


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

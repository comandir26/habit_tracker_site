from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Guild, GuildHabit, GuildMember
from .serializers import GuildHabitSerializer, GuildSerializer


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

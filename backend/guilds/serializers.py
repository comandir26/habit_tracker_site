import re

from django.utils import timezone

from rest_framework import serializers

from .models import Guild, GuildHabit, GuildMember, HabitCompletion


class GuildMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GuildMember
        fields = ("id", "username", "role", "xp", "joined_at")
        read_only_fields = fields


class GuildSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="owner.username", read_only=True)
    members = GuildMemberSerializer(source="memberships", many=True, read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Guild
        fields = (
            "id", "name", "description", "color", "is_private", "owner",
            "created_at", "members", "is_owner",
        )
        read_only_fields = ("id", "owner", "created_at", "members")

    def validate_color(self, value):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise serializers.ValidationError("Color must be a six-digit hexadecimal value, e.g. #5b5bd6.")
        return value.lower()

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.pk == obj.owner_id)


class GuildHabitSerializer(serializers.ModelSerializer):
    xp_reward = serializers.IntegerField(read_only=True)
    weekdays = serializers.JSONField(required=False)

    class Meta:
        model = GuildHabit
        fields = ("id", "guild", "name", "schedule", "weekdays", "difficulty", "xp_weight", "xp_reward", "created_at")
        read_only_fields = ("id", "guild", "xp_reward", "created_at")

    def validate_xp_weight(self, value):
        raw_value = self.initial_data.get("xp_weight")
        if isinstance(raw_value, bool) or isinstance(raw_value, float):
            raise serializers.ValidationError("XP weight must be an integer from 1 to 10.")
        return value

    def validate(self, attrs):
        days = attrs.get("weekdays", [])
        if not isinstance(days, list) or any(type(day) is not int or not 1 <= day <= 7 for day in days):
            raise serializers.ValidationError({"weekdays": "Use a list of ISO weekday integers from 1 (Monday) to 7 (Sunday)."})
        if len(days) != len(set(days)):
            raise serializers.ValidationError({"weekdays": "Weekdays must not contain duplicates."})
        if attrs.get("schedule", GuildHabit.Schedule.DAILY) == GuildHabit.Schedule.WEEKDAYS:
            if not days:
                raise serializers.ValidationError({"weekdays": "Select at least one weekday."})
            attrs["weekdays"] = sorted(days)
        else:
            attrs["weekdays"] = []
        return attrs


class HabitCompletionSerializer(serializers.ModelSerializer):
    completed_on = serializers.DateField(required=False)

    class Meta:
        model = HabitCompletion
        fields = ("completed_on",)

    def validate_completed_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("A habit cannot be completed in the future.")
        return value

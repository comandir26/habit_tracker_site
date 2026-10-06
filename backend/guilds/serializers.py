import re

from rest_framework import serializers

from .models import Guild, GuildMember


class GuildMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GuildMember
        fields = ("id", "username", "role", "joined_at")
        read_only_fields = fields


class GuildSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="owner.username", read_only=True)
    members = GuildMemberSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Guild
        fields = (
            "id", "name", "description", "color", "is_private", "owner",
            "created_at", "members",
        )
        read_only_fields = ("id", "owner", "created_at", "members")

    def validate_color(self, value):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise serializers.ValidationError("Color must be a six-digit hexadecimal value, e.g. #5b5bd6.")
        return value.lower()

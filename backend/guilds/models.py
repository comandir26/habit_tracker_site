from django.conf import settings
from django.db import models


class Guild(models.Model):
    """A team space owned by the user who created it."""

    name = models.CharField(max_length=48)
    description = models.CharField(max_length=180, blank=True)
    color = models.CharField(max_length=7, default="#5b5bd6")
    is_private = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_guilds",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class GuildMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MEMBER = "member", "Member"

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="guild_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("guild", "user"), name="unique_guild_member"),
        ]

    def __str__(self):
        return f"{self.user} in {self.guild}"

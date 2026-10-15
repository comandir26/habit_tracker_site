from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
    xp = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("guild", "user"), name="unique_guild_member"),
        ]

    def __str__(self):
        return f"{self.user} in {self.guild}"


class GuildHabit(models.Model):
    class Schedule(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKDAYS = "weekdays", "Selected weekdays"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    BASE_XP = {Difficulty.EASY: 10, Difficulty.MEDIUM: 20, Difficulty.HARD: 30}

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name="habits")
    name = models.CharField(max_length=120)
    schedule = models.CharField(max_length=16, choices=Schedule.choices, default=Schedule.DAILY)
    weekdays = models.JSONField(default=list, blank=True)
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices, default=Difficulty.EASY)
    xp_weight = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(condition=models.Q(xp_weight__gte=1, xp_weight__lte=10), name="habit_xp_weight_range"),
        ]

    @property
    def xp_reward(self):
        return self.BASE_XP[self.difficulty] * self.xp_weight

    def __str__(self):
        return self.name


class HabitCompletion(models.Model):
    """One user's completion of one habit on one calendar day.

    The database constraint is deliberately the source of truth for
    idempotency: retries of the same request cannot produce a second reward.
    """

    habit = models.ForeignKey(GuildHabit, on_delete=models.CASCADE, related_name="completions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habit_completions")
    completed_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-completed_on", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("habit", "user", "completed_on"),
                name="unique_habit_completion_per_day",
            ),
        ]

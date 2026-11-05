from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from guilds.models import Guild, GuildHabit, GuildMember, HabitCompletion
from .models import User
from .progress import level_progress


class LevelProgressTests(SimpleTestCase):
    def test_level_boundaries_and_large_totals(self):
        for xp, level, remainder in ((0, 1, 0), (99, 1, 99), (100, 2, 0),
                                     (101, 2, 1), (200, 3, 0), (10**12, 10**10 + 1, 0)):
            with self.subTest(xp=xp):
                self.assertEqual(level_progress(xp), {
                    "level": level, "xp_in_level": remainder, "xp_per_level": 100,
                    "xp_to_next_level": 100 - remainder,
                })


class ProfileApiTests(APITestCase):
    TODAY = date(2026, 10, 29)

    def setUp(self):
        self.user = User.objects.create_user(username="alex")
        self.other = User.objects.create_user(username="other")
        self.guild = Guild.objects.create(name="Focus", owner=self.user)
        self.membership = GuildMember.objects.create(guild=self.guild, user=self.user, xp=99)
        self.habit = GuildHabit.objects.create(guild=self.guild, name="Read")
        self.url = reverse("auth-profile")
        self.client.force_authenticate(self.user)
        clock = patch("users.views.timezone.now", return_value=datetime(2026, 10, 29, 12, tzinfo=timezone.utc))
        clock.start()
        self.addCleanup(clock.stop)

    def complete(self, offset, habit=None, user=None):
        HabitCompletion.objects.create(user=user or self.user, habit=habit or self.habit,
                                       completed_on=self.TODAY + timedelta(days=offset))

    def profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_authentication_required_and_only_own_profile_returned(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.user)
        result = self.client.get(self.url, {"user_id": self.other.pk}).data
        self.assertEqual(result["id"], self.user.pk)
        self.assertEqual(result["username"], "alex")
        self.assertNotIn("email", result)

    def test_no_memberships_starts_at_level_one(self):
        self.client.force_authenticate(self.other)
        result = self.profile()
        self.assertEqual((result["total_xp"], result["level"], result["streak"]), (0, 1, 0))
        self.assertEqual(result["xp_to_next_level"], 100)

    def test_xp_sums_memberships_without_other_users_or_completion_join_multiplication(self):
        second = Guild.objects.create(name="Walkers", owner=self.other)
        GuildMember.objects.create(guild=second, user=self.user, xp=101)
        GuildMember.objects.create(guild=self.guild, user=self.other, xp=999)
        self.complete(0)
        self.complete(-1)
        self.habit.difficulty = "hard"
        self.habit.save()
        result = self.profile()
        self.assertEqual((result["total_xp"], result["level"], result["xp_in_level"]), (200, 3, 0))

    def test_streak_combines_guilds_and_deduplicates_days(self):
        second = Guild.objects.create(name="Walkers", owner=self.user)
        GuildMember.objects.create(guild=second, user=self.user)
        habit = GuildHabit.objects.create(guild=second, name="Walk")
        self.complete(0)
        self.complete(0, habit)
        self.complete(-1, habit)
        self.complete(-2)
        self.complete(1)
        self.assertEqual(self.profile()["streak"], 3)

    def test_yesterday_grace_gap_and_future_dates(self):
        self.complete(-1)
        self.complete(-2)
        self.complete(-4)
        self.complete(1)
        self.assertEqual(self.profile()["streak"], 2)
        self.complete(0)
        self.assertEqual(self.profile()["streak"], 3)
        HabitCompletion.objects.filter(user=self.user, completed_on__gte=self.TODAY - timedelta(days=1)).delete()
        self.assertEqual(self.profile()["streak"], 0)

    def test_other_users_and_nonmember_guilds_do_not_affect_streak(self):
        self.complete(-1, user=self.other)
        outside = Guild.objects.create(name="Outside", owner=self.other)
        habit = GuildHabit.objects.create(guild=outside, name="Other")
        self.complete(0, habit)
        self.assertEqual(self.profile()["streak"], 0)

    def test_timezone_boundary_and_invalid_timezone_fallback(self):
        self.complete(0)
        self.complete(1)
        self.user.timezone = "Pacific/Auckland"
        self.user.save()
        self.assertEqual(self.profile()["streak"], 2)
        self.user.timezone = "Invalid/Zone"
        self.user.save()
        self.assertEqual(self.profile()["streak"], 1)

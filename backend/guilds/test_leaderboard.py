from datetime import date, datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User
from .models import Guild, GuildHabit, GuildMember, HabitCompletion


class GuildLeaderboardApiTests(APITestCase):
    NOW = datetime(2026, 10, 27, 12, tzinfo=datetime_timezone.utc)
    TODAY = date(2026, 10, 27)

    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.member = User.objects.create_user(username="member")
        self.outsider = User.objects.create_user(username="outsider")
        self.guild = Guild.objects.create(name="Focus", owner=self.owner)
        self.owner_membership = GuildMember.objects.create(
            guild=self.guild, user=self.owner, role="owner", xp=100,
        )
        self.membership = GuildMember.objects.create(guild=self.guild, user=self.member, xp=50)
        self.habit = GuildHabit.objects.create(guild=self.guild, name="Read")
        self.url = reverse("guild-leaderboard", args=(self.guild.pk,))
        self.client.force_authenticate(self.member)
        self.clock = patch("guilds.views.timezone.now", return_value=self.NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def complete(self, user, *offsets, habit=None):
        for offset in offsets:
            HabitCompletion.objects.create(
                user=user, habit=habit or self.habit,
                completed_on=self.TODAY + timedelta(days=offset),
            )

    def get_members(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response.data["members"]

    def test_default_xp_sort_contract_and_current_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["guild_id"], self.guild.pk)
        self.assertEqual(response.data["guild_name"], "Focus")
        self.assertEqual(response.data["sort"], "xp")
        self.assertEqual(response.data["members"], [{
            "member_id": self.owner_membership.pk, "user_id": self.owner.pk,
            "username": "owner", "xp": 100, "streak": 0, "rank": 1, "is_current_user": False,
        }, {
            "member_id": self.membership.pk, "user_id": self.member.pk,
            "username": "member", "xp": 50, "streak": 0, "rank": 2, "is_current_user": True,
        }])

    def test_authentication_and_membership_required_even_for_private_guilds(self):
        self.guild.is_private = True
        self.guild.save(update_fields=["is_private"])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(self.url, {"sort": "invalid"}).status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(reverse("guild-leaderboard", args=(99999,))).status_code, 404)

    def test_invalid_sort_is_rejected(self):
        for sort in ("", "name", "XP", "-xp"):
            response = self.client.get(self.url, {"sort": sort})
            self.assertEqual(response.status_code, 400)
            self.assertIn("sort", response.data)

    def test_selected_metric_secondary_metric_and_user_id_produce_stable_ranks(self):
        third = User.objects.create_user(username="third")
        GuildMember.objects.create(guild=self.guild, user=third, xp=50)
        self.complete(self.owner, -1)
        self.complete(self.member, 0, -1, -2)
        self.complete(third, 0, -1, -2)
        xp_members = self.get_members(sort="xp")
        streak_members = self.get_members(sort="streak")
        self.assertEqual([row["user_id"] for row in xp_members], [self.owner.pk, self.member.pk, third.pk])
        self.assertEqual([row["user_id"] for row in streak_members], [self.member.pk, third.pk, self.owner.pk])
        self.assertEqual([row["rank"] for row in streak_members], [1, 2, 3])
        # Equal streaks use XP before the stable user-id tie breaker.
        self.membership.xp = 150
        self.membership.save(update_fields=["xp"])
        self.assertEqual(self.get_members(sort="streak")[0]["user_id"], self.member.pk)

    def test_xp_ties_use_streak_and_streak_ties_use_xp(self):
        self.owner_membership.xp = 50
        self.owner_membership.save(update_fields=["xp"])
        self.complete(self.member, -1)
        self.assertEqual(self.get_members(sort="xp")[0]["user_id"], self.member.pk)
        self.complete(self.owner, 0)
        self.owner_membership.xp = 60
        self.owner_membership.save(update_fields=["xp"])
        self.assertEqual(self.get_members(sort="streak")[0]["user_id"], self.owner.pk)

    def test_today_yesterday_duplicates_and_future_completions(self):
        self.complete(self.owner, 0, -1, -2, 1)
        self.complete(self.member, -1, -2, 1)
        second_habit = GuildHabit.objects.create(guild=self.guild, name="Walk")
        self.complete(self.owner, 0, -1, habit=second_habit)
        rows = {row["user_id"]: row for row in self.get_members()}
        self.assertEqual(rows[self.owner.pk]["streak"], 3)
        self.assertEqual(rows[self.member.pk]["streak"], 2)

    def test_gap_breaks_streak_and_old_or_future_activity_has_no_current_streak(self):
        self.complete(self.owner, 0, -2, -3)
        self.complete(self.member, -2, -3, 1)
        rows = {row["user_id"]: row for row in self.get_members()}
        self.assertEqual(rows[self.owner.pk]["streak"], 1)
        self.assertEqual(rows[self.member.pk]["streak"], 0)

    def test_streak_and_xp_are_scoped_to_guild_and_xp_is_not_recalculated(self):
        other = Guild.objects.create(name="Other", owner=self.owner)
        GuildMember.objects.create(guild=other, user=self.member, xp=9999)
        other_habit = GuildHabit.objects.create(guild=other, name="Other habit")
        self.complete(self.member, 0, -1, -2, habit=other_habit)
        self.complete(self.member, 0)
        self.complete(self.outsider, 0, -1)
        self.habit.difficulty = "hard"
        self.habit.xp_weight = 10
        self.habit.save(update_fields=["difficulty", "xp_weight"])
        rows = {row["user_id"]: row for row in self.get_members()}
        self.assertEqual(set(rows), {self.owner.pk, self.member.pk})
        self.assertEqual(rows[self.member.pk]["streak"], 1)
        self.assertEqual(rows[self.member.pk]["xp"], 50)

    def test_each_members_timezone_controls_midnight_and_invalid_timezone_uses_utc(self):
        self.member.timezone = "Pacific/Auckland"  # Already October 28 at NOW.
        self.member.save(update_fields=["timezone"])
        self.owner.timezone = "Not/A_Timezone"
        self.owner.save(update_fields=["timezone"])
        self.complete(self.member, 0, 1)
        self.complete(self.owner, 0, 1)
        rows = {row["user_id"]: row for row in self.get_members()}
        self.assertEqual(rows[self.member.pk]["streak"], 2)
        self.assertEqual(rows[self.owner.pk]["streak"], 1)
        with patch("guilds.views.timezone.now", return_value=datetime(2026, 10, 28, 0, tzinfo=datetime_timezone.utc)):
            rows = {row["user_id"]: row for row in self.get_members()}
        self.assertEqual(rows[self.owner.pk]["streak"], 2)

    def test_query_count_does_not_grow_with_member_count(self):
        with self.assertNumQueries(3):
            self.get_members()
        for number in range(8):
            user = User.objects.create_user(username=f"extra-{number}")
            GuildMember.objects.create(guild=self.guild, user=user)
            self.complete(user, 0, -1)
        with self.assertNumQueries(3):
            rows = self.get_members()
        self.assertEqual(len(rows), 10)

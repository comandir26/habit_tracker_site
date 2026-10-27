from datetime import timedelta


from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APITestCase

from users.models import User

from . import models as guild_models
from .models import INVITE_CODE_ALPHABET, Guild, GuildHabit, GuildInvite, GuildMember, HabitCompletion


class GuildApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="secure-password")
        self.member = User.objects.create_user(username="member", password="secure-password")
        self.outsider = User.objects.create_user(username="outsider", password="secure-password")
        self.owner_token = str(AccessToken.for_user(self.owner))
        self.member_token = str(AccessToken.for_user(self.member))
        self.outsider_token = str(AccessToken.for_user(self.outsider))

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def create_guild(self, **overrides):
        values = {
            "name": "Early birds",
            "description": "Building better mornings together",
            "color": "#5B5BD6",
            "is_private": True,
        }
        values.update(overrides)
        return Guild.objects.create(owner=self.owner, **values)

    def test_create_makes_request_user_owner_and_member(self):
        self.authenticate(self.owner_token)

        response = self.client.post(
            reverse("guild-list-create"),
            {"name": "Focus", "description": "Daily focus", "color": "#0F9F81"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        guild = Guild.objects.get(pk=response.data["id"])
        self.assertEqual(guild.owner, self.owner)
        self.assertEqual(guild.color, "#0f9f81")
        self.assertTrue(
            GuildMember.objects.filter(
                guild=guild, user=self.owner, role=GuildMember.Role.OWNER
            ).exists()
        )

    def test_create_requires_token_and_valid_color(self):
        response = self.client.post(reverse("guild-list-create"), {"name": "Focus"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.authenticate(self.owner_token)
        response = self.client.post(
            reverse("guild-list-create"),
            {"name": "Focus", "color": "blue"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("color", response.data)

    def test_detail_is_available_to_owner_and_member(self):
        guild = self.create_guild()
        GuildMember.objects.create(guild=guild, user=self.owner, role=GuildMember.Role.OWNER)
        GuildMember.objects.create(guild=guild, user=self.member)
        url = reverse("guild-detail", args=(guild.pk,))

        self.authenticate(self.owner_token)
        owner_response = self.client.get(url)
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_response.data["owner"], "owner")
        self.assertTrue(owner_response.data["is_owner"])
        self.assertEqual(len(owner_response.data["members"]), 2)

        self.authenticate(self.member_token)
        member_response = self.client.get(url)
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertFalse(member_response.data["is_owner"])


    def test_detail_and_list_hide_unrelated_guilds(self):
        guild = self.create_guild()
        GuildMember.objects.create(guild=guild, user=self.owner, role=GuildMember.Role.OWNER)
        self.authenticate(self.outsider_token)

        detail_response = self.client.get(reverse("guild-detail", args=(guild.pk,)))
        list_response = self.client.get(reverse("guild-list-create"))

        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])

    def test_list_contains_only_guilds_where_user_is_a_member(self):
        accessible_guild = self.create_guild(name="Accessible")
        hidden_guild = self.create_guild(name="Hidden")
        GuildMember.objects.create(
            guild=accessible_guild, user=self.member, role=GuildMember.Role.MEMBER
        )
        GuildMember.objects.create(
            guild=hidden_guild, user=self.owner, role=GuildMember.Role.OWNER
        )
        self.authenticate(self.member_token)

        response = self.client.get(reverse("guild-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [accessible_guild.id])


class GuildHabitApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.member = User.objects.create_user(username="member")
        self.outsider = User.objects.create_user(username="outsider")
        self.guild = Guild.objects.create(name="Focus", owner=self.owner)
        GuildMember.objects.create(guild=self.guild, user=self.owner, role=GuildMember.Role.OWNER)
        GuildMember.objects.create(guild=self.guild, user=self.member)
        self.url = reverse("guild-habit-list-create", args=(self.guild.pk,))
        self.client.force_authenticate(self.owner)

    def test_owner_creation_and_server_calculated_xp(self):
        response = self.client.post(self.url, {
            "name": "  Read  ", "schedule": "weekdays", "weekdays": [7, 1, 3],
            "difficulty": "hard", "xp_weight": 4, "xp_reward": 999,
            "guild": 999,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Read")
        self.assertEqual(response.data["weekdays"], [1, 3, 7])
        self.assertEqual(response.data["xp_reward"], 120)
        self.assertEqual(GuildHabit.objects.get().guild_id, self.guild.pk)

    def test_daily_defaults_and_canonical_weekdays(self):
        for payload in ({"name": "Read"}, {"name": "Walk", "weekdays": [1, 2]}):
            response = self.client.post(self.url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["schedule"], "daily")
            self.assertEqual(response.data["weekdays"], [])
            self.assertEqual(response.data["difficulty"], "easy")
            self.assertEqual(response.data["xp_reward"], 10)

    def test_member_can_list_but_cannot_create(self):
        habit = GuildHabit.objects.create(guild=self.guild, name="Read")
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get(self.url).data[0]["id"], habit.pk)
        response = self.client.post(self.url, {"name": "Walk"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GuildHabit.objects.count(), 1)

    def test_unrelated_guild_and_missing_guild_are_hidden(self):
        self.client.force_authenticate(self.outsider)
        for url in (self.url, reverse("guild-habit-list-create", args=(99999,))):
            self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(self.client.post(url, {"name": "Read"}, format="json").status_code, status.HTTP_404_NOT_FOUND)

    def test_listing_is_scoped_to_guild(self):
        other_guild = Guild.objects.create(name="Other", owner=self.owner)
        GuildMember.objects.create(guild=other_guild, user=self.owner)
        GuildHabit.objects.create(guild=other_guild, name="Hidden")
        self.assertEqual(self.client.get(self.url).data, [])

    def test_authentication_is_required_for_habits_and_difficulties(self):
        self.client.force_authenticate(None)
        for url in (self.url, reverse("habit-difficulty-list")):
            self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.url, {"name": "Read"}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_habits_do_not_persist(self):
        invalid_payloads = [
            ({"name": ""}, "name"), ({"name": "   "}, "name"),
            ({"name": "x" * 121}, "name"),
            ({"schedule": "monthly"}, "schedule"),
            ({"schedule": "weekdays"}, "weekdays"),
            ({"schedule": "weekdays", "weekdays": []}, "weekdays"),
            ({"weekdays": [1, 1]}, "weekdays"),
            ({"weekdays": [0]}, "weekdays"), ({"weekdays": [8]}, "weekdays"),
            ({"weekdays": [True]}, "weekdays"), ({"weekdays": [1.5]}, "weekdays"),
            ({"weekdays": ["1"]}, "weekdays"), ({"weekdays": "Monday"}, "weekdays"),
            ({"weekdays": None}, "weekdays"),
            ({"difficulty": "extreme"}, "difficulty"),
            ({"xp_weight": 0}, "xp_weight"), ({"xp_weight": -1}, "xp_weight"),
            ({"xp_weight": 11}, "xp_weight"), ({"xp_weight": True}, "xp_weight"),
            ({"xp_weight": 1.5}, "xp_weight"),
        ]
        for invalid, field in invalid_payloads:
            with self.subTest(payload=invalid):
                payload = {"name": "Read", **invalid}
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
        self.assertFalse(GuildHabit.objects.exists())

    def test_all_difficulties_have_consistent_xp_and_weight_limits(self):
        expected = [("easy", "Easy", 10), ("medium", "Medium", 20), ("hard", "Hard", 30)]
        response = self.client.get(reverse("habit-difficulty-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"value": value, "label": label, "base_xp": xp} for value, label, xp in expected])
        for value, _, base_xp in expected:
            for weight in (1, 10):
                response = self.client.post(self.url, {"name": "Read", "difficulty": value, "xp_weight": weight}, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["xp_reward"], base_xp * weight)


class HabitCompletionApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.member = User.objects.create_user(username="member")
        self.outsider = User.objects.create_user(username="outsider")
        self.guild = Guild.objects.create(name="Focus", owner=self.owner)
        self.owner_membership = GuildMember.objects.create(
            guild=self.guild, user=self.owner, role=GuildMember.Role.OWNER,
        )
        self.member_membership = GuildMember.objects.create(guild=self.guild, user=self.member)
        self.habit = GuildHabit.objects.create(guild=self.guild, name="Read", difficulty="medium", xp_weight=2)
        self.url = reverse("habit-complete", args=(self.habit.pk,))

    def test_completion_awards_xp_once_for_same_user_and_day(self):
        self.client.force_authenticate(self.member)

        first = self.client.post(self.url, {"completed_on": "2026-10-07"}, format="json")
        second = self.client.post(self.url, {"completed_on": "2026-10-07"}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["created"])
        self.assertEqual(first.data["awarded_xp"], 40)
        self.assertEqual(first.data["member_id"], self.member_membership.pk)
        self.assertEqual(first.data["member_xp"], 40)
        self.assertFalse(second.data["created"])
        self.assertEqual(second.data["awarded_xp"], 0)
        self.assertEqual(second.data["member_xp"], 40)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.xp, 40)
        self.assertEqual(HabitCompletion.objects.count(), 1)

    def test_each_member_has_own_completion_and_xp(self):
        self.client.force_authenticate(self.owner)
        self.client.post(self.url, {"completed_on": "2026-10-07"}, format="json")
        self.client.force_authenticate(self.member)
        response = self.client.post(self.url, {"completed_on": "2026-10-07"}, format="json")

        self.assertTrue(response.data["created"])
        self.owner_membership.refresh_from_db()
        self.member_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.xp, 40)
        self.assertEqual(self.member_membership.xp, 40)
        self.assertEqual(HabitCompletion.objects.count(), 2)

    def test_completion_requires_membership_and_valid_date(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.member)
        response = self.client.post(self.url, {"completed_on": "not-a-date"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(HabitCompletion.objects.exists())

    def test_completion_cannot_be_recorded_for_a_future_date(self):
        self.client.force_authenticate(self.member)
        tomorrow = timezone.localdate() + timedelta(days=1)

        response = self.client.post(self.url, {"completed_on": tomorrow.isoformat()}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(HabitCompletion.objects.exists())
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.xp, 0)


class TodayHabitApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveller", timezone="Pacific/Auckland")
        self.other_user = User.objects.create_user(username="outsider", timezone="UTC")
        self.guild = Guild.objects.create(name="Morning team", color="#0f9f81", owner=self.user)
        self.other_guild = Guild.objects.create(name="Private team", owner=self.other_user)
        GuildMember.objects.create(guild=self.guild, user=self.user, role=GuildMember.Role.OWNER)
        GuildMember.objects.create(guild=self.other_guild, user=self.other_user, role=GuildMember.Role.OWNER)
        self.daily = GuildHabit.objects.create(guild=self.guild, name="Daily", schedule="daily")
        self.tuesday = GuildHabit.objects.create(guild=self.guild, name="Tuesday", schedule="weekdays", weekdays=[2])
        self.wednesday = GuildHabit.objects.create(guild=self.guild, name="Wednesday", schedule="weekdays", weekdays=[3])
        GuildHabit.objects.create(guild=self.other_guild, name="Hidden", schedule="daily")
        self.client.force_authenticate(self.user)

    @patch("guilds.views.timezone.now", return_value=datetime(2026, 10, 6, 12, tzinfo=datetime_timezone.utc))
    def test_list_uses_the_users_local_weekday_and_includes_guild_context(self, _mock_now):
        response = self.client.get(reverse("today-habit-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # It is Wednesday in Pacific/Auckland at the mocked UTC instant.
        self.assertEqual(response.data["date"], "2026-10-07")
        self.assertEqual(response.data["timezone"], "Pacific/Auckland")
        self.assertEqual(
            [habit["id"] for habit in response.data["habits"]],
            [self.daily.id, self.wednesday.id],
        )
        self.assertEqual(response.data["habits"][0]["guild_name"], "Morning team")
        self.assertEqual(response.data["habits"][0]["guild_color"], "#0f9f81")

    @patch("guilds.views.timezone.now", return_value=datetime(2026, 10, 6, 12, tzinfo=datetime_timezone.utc))
    def test_invalid_timezone_falls_back_to_project_timezone(self, _mock_now):
        self.user.timezone = "Not/A_Real_Timezone"
        self.user.save(update_fields=["timezone"])

        response = self.client.get(reverse("today-habit-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["timezone"], "UTC")
        self.assertEqual(response.data["date"], "2026-10-06")
        self.assertEqual([habit["id"] for habit in response.data["habits"]], [self.daily.id, self.tuesday.id])

    def test_authentication_is_required_for_today_list(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("today-habit-list")).status_code, status.HTTP_401_UNAUTHORIZED)


class GuildInviteApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.member = User.objects.create_user(username="member")
        self.outsider = User.objects.create_user(username="outsider")
        self.guild = Guild.objects.create(name="Focus", description="Deep work", color="#0f9f81", owner=self.owner)
        GuildMember.objects.create(guild=self.guild, user=self.owner, role=GuildMember.Role.OWNER)
        GuildMember.objects.create(guild=self.guild, user=self.member)
        self.url = reverse("guild-invite-list-create", args=(self.guild.pk,))
        self.client.force_authenticate(self.owner)

    def create_invite(self, **overrides):
        values = {"guild": self.guild, "created_by": self.owner, "expires_at": timezone.now() + timedelta(days=7)}
        values.update(overrides)
        return GuildInvite.objects.create(**values)

    def test_owner_creates_invite_with_default_week_lifetime(self):
        before = timezone.now()
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite = GuildInvite.objects.get(pk=response.data["id"])
        self.assertEqual(invite.guild, self.guild)
        self.assertEqual(invite.created_by, self.owner)
        self.assertEqual(response.data["code"], invite.code)
        self.assertFalse(response.data["is_expired"])
        self.assertEqual(len(invite.code), 8)
        self.assertTrue(set(invite.code) <= set(INVITE_CODE_ALPHABET))
        self.assertAlmostEqual(invite.expires_at, before + timedelta(days=7), delta=timedelta(seconds=5))

    def test_lifetime_must_be_one_of_allowed_values(self):
        response = self.client.post(self.url, {"expires_in_days": 30}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite = GuildInvite.objects.get(pk=response.data["id"])
        self.assertGreater(invite.expires_at, timezone.now() + timedelta(days=29))

        for value in (0, 5, 365, True, "week"):
            response = self.client.post(self.url, {"expires_in_days": value}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, value)
            self.assertIn("expires_in_days", response.data)
        self.assertEqual(GuildInvite.objects.count(), 1)

    def test_client_cannot_choose_code_or_guild(self):
        other_guild = Guild.objects.create(name="Other", owner=self.outsider)
        response = self.client.post(
            self.url, {"code": "AAAAAAAA", "guild": other_guild.pk, "expires_at": "2000-01-01T00:00:00Z"}, format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite = GuildInvite.objects.get(pk=response.data["id"])
        self.assertNotEqual(invite.code, "AAAAAAAA")
        self.assertEqual(invite.guild, self.guild)
        self.assertFalse(invite.is_expired)

    def test_member_cannot_create_or_list_invites(self):
        self.create_invite()
        self.client.force_authenticate(self.member)

        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GuildInvite.objects.count(), 1)

    def test_outsider_and_missing_guild_are_hidden(self):
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.owner)
        missing_url = reverse("guild-invite-list-create", args=(self.guild.pk + 100,))
        self.assertEqual(self.client.post(missing_url, {}, format="json").status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_lists_only_active_invites_of_the_guild(self):
        active = self.create_invite()
        self.create_invite(expires_at=timezone.now() - timedelta(seconds=1))
        other_guild = Guild.objects.create(name="Other", owner=self.owner)
        GuildMember.objects.create(guild=other_guild, user=self.owner, role=GuildMember.Role.OWNER)
        self.create_invite(guild=other_guild)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([invite["id"] for invite in response.data], [active.pk])

    def test_authentication_is_required(self):
        invite = self.create_invite()
        self.client.force_authenticate(None)

        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
        detail_url = reverse("invite-detail", args=(invite.code,))
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_any_signed_in_user_can_preview_invite_case_insensitively(self):
        invite = self.create_invite()
        self.client.force_authenticate(self.outsider)

        response = self.client.get(reverse("invite-detail", args=(invite.code.lower(),)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], invite.code)
        self.assertFalse(response.data["is_member"])
        self.assertEqual(response.data["guild"], {
            "id": self.guild.pk,
            "name": "Focus",
            "description": "Deep work",
            "color": "#0f9f81",
            "owner": "owner",
            "members_count": 2,
        })
        self.assertNotIn("members", response.data["guild"])

        self.client.force_authenticate(self.member)
        self.assertTrue(self.client.get(reverse("invite-detail", args=(invite.code,))).data["is_member"])

    def test_unknown_and_expired_codes_are_rejected(self):
        expired = self.create_invite(expires_at=timezone.now() - timedelta(seconds=1))

        expired_response = self.client.get(reverse("invite-detail", args=(expired.code,)))
        missing_response = self.client.get(reverse("invite-detail", args=("NOPE2345",)))

        self.assertEqual(expired_response.status_code, status.HTTP_410_GONE)
        self.assertNotIn("guild", expired_response.data)
        self.assertEqual(missing_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_code_collision_is_regenerated_before_saving(self):
        existing = self.create_invite()
        generated = iter([existing.code, "FRESH234"])

        with patch.object(guild_models, "generate_invite_code", lambda: next(generated)):
            invite = self.create_invite(code=existing.code)

        self.assertEqual(invite.code, "FRESH234")
        self.assertEqual(GuildInvite.objects.filter(code=existing.code).count(), 1)


class InviteJoinApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.guest = User.objects.create_user(username="guest")
        self.guild = Guild.objects.create(name="Focus", owner=self.owner, is_private=True)
        self.owner_membership = GuildMember.objects.create(
            guild=self.guild, user=self.owner, role=GuildMember.Role.OWNER, xp=50,
        )
        self.habit = GuildHabit.objects.create(guild=self.guild, name="Read")
        self.invite = GuildInvite.objects.create(
            guild=self.guild, created_by=self.owner, code="ABCD2345",
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.url = reverse("invite-join", args=(self.invite.code,))
        self.client.force_authenticate(self.guest)

    def test_join_grants_guild_and_habit_access_without_extra_privileges(self):
        guild_url = reverse("guild-detail", args=(self.guild.pk,))
        habits_url = reverse("guild-habit-list-create", args=(self.guild.pk,))
        self.assertEqual(self.client.get(guild_url).status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"guild_id": self.guild.pk, "created": True})
        membership = GuildMember.objects.get(guild=self.guild, user=self.guest)
        self.assertEqual(membership.role, GuildMember.Role.MEMBER)
        self.assertEqual(membership.xp, 0)
        self.assertEqual(self.client.get(guild_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(habits_url).data[0]["id"], self.habit.pk)
        self.assertEqual(self.client.post(habits_url, {"name": "Walk"}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(self.guild.pk, [guild["id"] for guild in self.client.get(reverse("guild-list-create")).data])

    def test_join_normalizes_case_and_surrounding_whitespace(self):
        response = self.client.post(reverse("invite-join", args=(" abcd2345 ",)), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GuildMember.objects.filter(guild=self.guild, user=self.guest).exists())

    def test_retries_and_different_invites_do_not_duplicate_or_reset_membership(self):
        self.client.post(self.url, {}, format="json")
        membership = GuildMember.objects.get(guild=self.guild, user=self.guest)
        membership.xp = 75
        membership.save(update_fields=["xp"])
        other = GuildInvite.objects.create(
            guild=self.guild, created_by=self.owner,
            expires_at=timezone.now() + timedelta(days=1),
        )
        for url in (self.url, reverse("invite-join", args=(other.code,))):
            response = self.client.post(url, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {"guild_id": self.guild.pk, "created": False})
        self.assertEqual(GuildMember.objects.filter(guild=self.guild, user=self.guest).count(), 1)
        membership.refresh_from_db()
        self.assertEqual(membership.xp, 75)

    def test_owner_keeps_role_and_xp(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["created"])
        self.owner_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.role, GuildMember.Role.OWNER)
        self.assertEqual(self.owner_membership.xp, 50)

    def test_join_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(GuildMember.objects.filter(guild=self.guild, user=self.guest).exists())

    def test_invalid_and_unknown_codes_do_not_create_membership(self):
        for code in ("short", "ABCD23456", "ABCD23!5", "ABCD2305"):
            with self.subTest(code=code):
                response = self.client.post(reverse("invite-join", args=(code,)), {}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("code", response.data)
        response = self.client.post(reverse("invite-join", args=("ZZZZ9999",)), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(GuildMember.objects.filter(guild=self.guild, user=self.guest).exists())

    def test_expired_invite_including_exact_boundary_does_not_create_membership(self):
        now = timezone.now()
        for expires_at in (now - timedelta(seconds=1), now):
            self.invite.expires_at = expires_at
            self.invite.save(update_fields=["expires_at"])
            with patch("guilds.models.timezone.now", return_value=now):
                response = self.client.post(self.url, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_410_GONE)
            self.assertNotIn("guild_id", response.data)
        self.assertFalse(GuildMember.objects.filter(guild=self.guild, user=self.guest).exists())

    def test_client_cannot_choose_guild_role_xp_or_user(self):
        other = Guild.objects.create(name="Other", owner=self.owner)
        response = self.client.post(self.url, {
            "guild_id": other.pk, "role": "owner", "xp": 10000, "user": self.owner.pk,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        membership = GuildMember.objects.get(guild=self.guild, user=self.guest)
        self.assertEqual(membership.role, GuildMember.Role.MEMBER)
        self.assertEqual(membership.xp, 0)
        self.assertFalse(GuildMember.objects.filter(guild=other, user=self.guest).exists())

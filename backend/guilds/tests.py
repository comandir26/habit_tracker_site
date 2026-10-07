from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.models import User

from .models import Guild, GuildHabit, GuildMember


class GuildApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="secure-password")
        self.member = User.objects.create_user(username="member", password="secure-password")
        self.outsider = User.objects.create_user(username="outsider", password="secure-password")
        self.owner_token = Token.objects.create(user=self.owner)
        self.member_token = Token.objects.create(user=self.member)
        self.outsider_token = Token.objects.create(user=self.outsider)

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

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

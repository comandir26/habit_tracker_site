from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.models import User

from .models import Guild, GuildMember


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
        self.assertEqual(len(owner_response.data["members"]), 2)

        self.authenticate(self.member_token)
        member_response = self.client.get(url)
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)

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

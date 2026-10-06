from django.urls import path

from .views import GuildDetailView, GuildListCreateView


urlpatterns = [
    path("guilds/", GuildListCreateView.as_view(), name="guild-list-create"),
    path("guilds/<int:pk>/", GuildDetailView.as_view(), name="guild-detail"),
]

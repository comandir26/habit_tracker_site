from django.urls import path

from .views import (
    GuildDetailView, GuildHabitListCreateView, GuildInviteListCreateView, GuildListCreateView, HabitCompletionCreateView,
    HabitDifficultyListView, InviteDetailView, TodayHabitListView,
)


urlpatterns = [
    path("guilds/", GuildListCreateView.as_view(), name="guild-list-create"),
    path("guilds/<int:pk>/", GuildDetailView.as_view(), name="guild-detail"),
    path("guilds/<int:guild_id>/habits/", GuildHabitListCreateView.as_view(), name="guild-habit-list-create"),
    path("guilds/<int:guild_id>/invites/", GuildInviteListCreateView.as_view(), name="guild-invite-list-create"),
    path("invites/<str:code>/", InviteDetailView.as_view(), name="invite-detail"),
    path("habits/<int:habit_id>/complete/", HabitCompletionCreateView.as_view(), name="habit-complete"),
    path("habit-difficulties/", HabitDifficultyListView.as_view(), name="habit-difficulty-list"),
    path("habits/today/", TodayHabitListView.as_view(), name="today-habit-list"),
]

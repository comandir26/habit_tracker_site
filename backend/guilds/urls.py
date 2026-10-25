from django.urls import path

from .views import (
    GuildDetailView, GuildHabitListCreateView, GuildInviteCreateView, GuildListCreateView, HabitCompletionCreateView,
    HabitDifficultyListView, TodayHabitListView,
)


urlpatterns = [
    path("guilds/", GuildListCreateView.as_view(), name="guild-list-create"),
    path("guilds/<int:pk>/", GuildDetailView.as_view(), name="guild-detail"),
    path("guilds/<int:guild_id>/habits/", GuildHabitListCreateView.as_view(), name="guild-habit-list-create"),
    path("guilds/<int:guild_id>/invites/", GuildInviteCreateView.as_view(), name="guild-invite-create"),
    path("habits/<int:habit_id>/complete/", HabitCompletionCreateView.as_view(), name="habit-complete"),
    path("habit-difficulties/", HabitDifficultyListView.as_view(), name="habit-difficulty-list"),
    path("habits/today/", TodayHabitListView.as_view(), name="today-habit-list"),
]

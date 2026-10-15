from django.urls import path

from .views import GuildDetailView, GuildListCreateView, GuildHabitListCreateView, HabitDifficultyListView, TodayHabitListView


urlpatterns = [
    path("guilds/", GuildListCreateView.as_view(), name="guild-list-create"),
    path("guilds/<int:pk>/", GuildDetailView.as_view(), name="guild-detail"),
    path("guilds/<int:guild_id>/habits/", GuildHabitListCreateView.as_view(), name="guild-habit-list-create"),
    path("habit-difficulties/", HabitDifficultyListView.as_view(), name="habit-difficulty-list"),
    path("habits/today/", TodayHabitListView.as_view(), name="today-habit-list"),
]

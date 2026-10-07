import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("guilds", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="GuildHabit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("schedule", models.CharField(choices=[("daily", "Daily"), ("weekdays", "Selected weekdays")], default="daily", max_length=16)),
                ("weekdays", models.JSONField(blank=True, default=list)),
                ("difficulty", models.CharField(choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], default="easy", max_length=16)),
                ("xp_weight", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("guild", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="habits", to="guilds.guild")),
            ],
            options={
                "ordering": ("created_at", "id"),
                "constraints": [models.CheckConstraint(condition=models.Q(xp_weight__gte=1, xp_weight__lte=10), name="habit_xp_weight_range")],
            },
        ),
    ]

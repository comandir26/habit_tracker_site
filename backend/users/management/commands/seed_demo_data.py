from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from users.models import User


class Command(BaseCommand):
    help = "Создаёт тестового пользователя с токеном для ручного тестирования API"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            user.set_password("demo12345")
            user.save()
            self.stdout.write(self.style.SUCCESS("Создан пользователь demo"))
        else:
            self.stdout.write("Пользователь demo уже существует")

        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f"Токен пользователя demo: {token.key}"))
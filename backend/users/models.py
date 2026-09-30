from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Минимальная модель пользователя для приложения, является расширением 
    стандартной модели пользователя Django, у которой есть все нужное username, 
    email, password, first_name, last_name и т.д.
    """
    timezone = models.CharField(max_length=64, default="UTC")

    def __str__(self):
        return self.username
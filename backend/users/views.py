from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import RegisterSerializer, UserSerializer
from guilds.models import HabitCompletion
from guilds.progress import current_streak, user_local_date
from .progress import level_progress


def token_payload_for(user):
    refresh = TokenObtainPairSerializer.get_token(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh), "user": UserSerializer(user).data}


class RegisterView(generics.CreateAPIView):
    """Create an account and return a short-lived access JWT plus refresh JWT."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(token_payload_for(user), status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # ``get_serializer`` creates a fresh serializer each time.  Keep the
        # validated instance so that its authenticated user can be included in
        # the same response as the JWT pair.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {**serializer.validated_data, "user": UserSerializer(serializer.user).data},
            status=status.HTTP_200_OK,
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"refresh": ["Это поле обязательно."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            if str(token.get("user_id")) != str(request.user.pk):
                return Response({"detail": "Токен принадлежит другому пользователю."}, status=status.HTTP_403_FORBIDDEN)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Недействительный refresh-токен."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        total_xp = user.guild_memberships.aggregate(total=Sum("xp"))["total"] or 0
        today = user_local_date(user.timezone, timezone.now())
        dates = HabitCompletion.objects.filter(
            user=user, habit__guild__memberships__user=user, completed_on__lte=today,
        ).order_by("completed_on").values_list("completed_on", flat=True).distinct()
        return Response({
            "id": user.pk, "username": user.username,
            "total_xp": total_xp, **level_progress(total_xp),
            "streak": current_streak(dates, today),
        })

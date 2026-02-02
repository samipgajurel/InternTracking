from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

User = get_user_model()


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    """
    ✅ When refreshing:
    - checks token_version (tv) matches user.token_version
    - writes tv into new access token
    """
    def validate(self, attrs):
        refresh_str = attrs.get("refresh")
        if not refresh_str:
            raise InvalidToken("No refresh token provided")

        refresh = RefreshToken(refresh_str)

        # refresh contains user_id claim
        user_id = refresh.get("user_id", None)
        if not user_id:
            raise InvalidToken("Invalid refresh token")

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise InvalidToken("User not found")

        token_tv = int(refresh.get("tv", 0))
        user_tv = int(getattr(user, "token_version", 0))

        # ✅ if password changed/reset -> token_version increased -> reject old refresh
        if token_tv != user_tv:
            raise InvalidToken("Token expired (password changed). Please login again.")

        data = super().validate(attrs)

        # ✅ also ensure new access includes current tv
        # super().validate returns {"access": "..."} and maybe new refresh depending settings
        # we can regenerate access with tv claim:
        new_access = refresh.access_token
        new_access["tv"] = user_tv
        data["access"] = str(new_access)

        return data


class MyTokenRefreshView(TokenRefreshView):
    serializer_class = MyTokenRefreshSerializer

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class TokenVersionJWTAuthentication(JWTAuthentication):
    """
    ✅ Reject access tokens if token_version doesn't match user.token_version
    """
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        token_tv = int(validated_token.get("tv", 0))
        user_tv = int(getattr(user, "token_version", 0))

        if token_tv != user_tv:
            raise InvalidToken("Token expired (password changed). Please login again.")

        return user

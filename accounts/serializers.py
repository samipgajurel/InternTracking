from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=120)
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["intern", "supervisor"], default="intern")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "staff_id", "email", "full_name", "role", "is_verified", "created_at"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        if not user.is_verified:
            raise serializers.ValidationError({"detail": "Email not verified. Verify first."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account disabled"})
        attrs["user"] = user
        return attrs


# ---------------- Password reset/change ----------------
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    # ✅ to force logout on THIS device
    refresh = serializers.CharField(required=False, allow_blank=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    # ✅ for best-effort refresh blacklist on this device
    refresh = serializers.CharField(required=False, allow_blank=True)
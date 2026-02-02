from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    SignupSerializer, LoginSerializer, UserSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer
)
from .tokens import make_verify_token, read_verify_token
from .permissions import IsAdmin
from internships.models import SupervisorIntern

token_generator = PasswordResetTokenGenerator()


def blacklist_refresh_if_possible(refresh_token_str: str) -> bool:
    """
    Best-effort: blacklist refresh token if blacklist app is enabled.
    If blacklist isn't enabled, it just returns False (no crash).
    """
    if not refresh_token_str:
        return False
    try:
        token = RefreshToken(refresh_token_str)
        token.blacklist()
        return True
    except Exception:
        return False


# ---------------- AUTH ----------------
class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = SignupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        email = data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email already exists"}, status=400)

        user = User.objects.create_user(
            email=email,
            full_name=data["full_name"],
            password=data["password"],
            role=data["role"],
            is_verified=False,
        )

        token = make_verify_token(user.id)
        verify_link = f"{settings.FRONTEND_BASE_URL}/verify.html?token={token}"

        send_mail(
            subject="Verify your MigdauWeb InternTrack account",
            message=(
                f"Hi {user.full_name},\n\n"
                f"Welcome to MigdauWeb InternTrack.\n"
                f"Please verify your email:\n{verify_link}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        # ✅ frontend will redirect user to Migadu webmail
        return Response({
            "detail": "Signup success. Verification email sent.",
            "redirect_url": "https://webmail.migadu.com/",
            "email": user.email
        }, status=201)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required"}, status=400)
        try:
            uid = read_verify_token(token)
            user = User.objects.get(id=uid)
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            return Response({"detail": "Email verified ✅"})
        except Exception:
            return Response({"detail": "Invalid or expired token"}, status=400)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        # ✅ IMPORTANT: include token_version claim so we can force logout later
        refresh["tv"] = int(getattr(user, "token_version", 0))
        refresh.access_token["tv"] = int(getattr(user, "token_version", 0))

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ---------------- FORGOT PASSWORD ----------------
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ForgotPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        email = s.validated_data["email"].lower().strip()
        user = User.objects.filter(email=email).first()

        # security: always same message
        if not user:
            return Response({"detail": "If the email exists, a reset link was sent."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        reset_link = f"{settings.FRONTEND_BASE_URL}/reset_password.html?uid={uid}&token={token}"

        send_mail(
            subject="Reset your password",
            message=f"Click to reset your password:\n{reset_link}\n\nThis link expires soon.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "If the email exists, a reset link was sent."})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(s.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid reset link"}, status=400)

        if not token_generator.check_token(user, s.validated_data["token"]):
            return Response({"detail": "Invalid or expired token"}, status=400)

        user.set_password(s.validated_data["new_password"])
        user.save(update_fields=["password"])

        # ✅ FORCE LOGOUT ALL DEVICES (invalidate JWTs)
        if hasattr(user, "bump_token_version"):
            user.bump_token_version()

        return Response({"detail": "✅ Password reset successful. Please login again."})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        if not request.user.check_password(s.validated_data["current_password"]):
            return Response({"detail": "Current password incorrect"}, status=400)

        request.user.set_password(s.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        # ✅ FORCE LOGOUT ALL DEVICES
        if hasattr(request.user, "bump_token_version"):
            request.user.bump_token_version()

        # ✅ Force logout THIS device too (best effort blacklist)
        refresh = (s.validated_data.get("refresh") or "").strip()
        blacklisted = blacklist_refresh_if_possible(refresh)

        return Response({
            "detail": "✅ Password changed. Please login again.",
            "refresh_blacklisted": bool(blacklisted)
        })


# ---------------- ADMIN ----------------
class AdminCreateUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        full_name = (request.data.get("full_name") or "").strip()
        password = request.data.get("password") or ""
        role = (request.data.get("role") or "").lower().strip()

        if role not in ["intern", "supervisor"]:
            return Response({"detail": "role must be intern/supervisor"}, status=400)

        # you can keep 6 here because admin creates company creds;
        # frontend signup will enforce 8+strong
        if not email or not full_name or len(password) < 6:
            return Response({"detail": "Invalid data"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email exists"}, status=400)

        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password,
            role=role,
            is_verified=True,
        )
        return Response({"detail": "User created", "user": UserSerializer(user).data}, status=201)


class AdminAssignInternView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        intern_id = request.data.get("intern_id")
        supervisor_id = request.data.get("supervisor_id")

        if not intern_id or not supervisor_id:
            return Response({"detail": "intern_id and supervisor_id required"}, status=400)

        try:
            intern = User.objects.get(id=intern_id, role="intern")
        except User.DoesNotExist:
            return Response({"detail": "Invalid intern_id"}, status=400)

        try:
            supervisor = User.objects.get(id=supervisor_id, role="supervisor")
        except User.DoesNotExist:
            return Response({"detail": "Invalid supervisor_id"}, status=400)

        SupervisorIntern.objects.update_or_create(intern=intern, defaults={"supervisor": supervisor})
        return Response({"detail": "✅ Intern assigned to supervisor"})


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        role = (request.query_params.get("role") or "").strip().lower()
        qs = User.objects.all().order_by("created_at")

        if role:
            if role not in ["admin", "supervisor", "intern"]:
                return Response({"detail": "role must be admin/supervisor/intern"}, status=400)
            qs = qs.filter(role=role)

        return Response([
            {
                "id": u.id,
                "staff_id": u.staff_id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_verified": u.is_verified,
            }
            for u in qs
        ])

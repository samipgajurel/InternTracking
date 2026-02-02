from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, role="intern", **extra):
        if not email:
            raise ValueError("Email required")

        email = self.normalize_email(email).lower().strip()
        full_name = (full_name or "").strip()

        user = self.model(email=email, full_name=full_name, role=role, **extra)
        user.set_password(password)

        # ✅ Save first so user.pk exists
        user.save(using=self._db)

        # ✅ Ensure staff_id exists (extra safety)
        if not user.staff_id:
            user.generate_staff_id()
            user.save(update_fields=["staff_id"])

        return user

    def create_superuser(self, email, full_name, password=None, **extra):
        user = self.create_user(email, full_name, password, role="admin", **extra)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_verified = True
        user.save(update_fields=["is_staff", "is_superuser", "is_active", "is_verified"])
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("supervisor", "Supervisor"),
        ("intern", "Intern"),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="intern")

    staff_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # ✅ company metadata
    company_code = models.CharField(max_length=20, blank=True, default="")
    id_card_no = models.CharField(max_length=50, blank=True, default="")

    # ✅ force logout support
    token_version = models.IntegerField(default=0)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def generate_staff_id(self):
        """
        ✅ Generates staff_id only if it doesn't exist.
        Requires pk (id) to exist.
        """
        if self.staff_id:
            return
        if not self.pk:
            return  # can't generate before first save

        prefix = "ADM" if self.role == "admin" else ("SUP" if self.role == "supervisor" else "INT")
        self.staff_id = f"{prefix}-{self.pk:05d}"

    def save(self, *args, **kwargs):
        """
        ✅ Always guarantees staff_id exists AFTER first save.
        This fixes cases like get_or_create() where manager isn't used.
        """
        creating = self.pk is None
        super().save(*args, **kwargs)

        # If created (or staff_id missing), generate & persist staff_id
        if (creating or not self.staff_id) and self.pk and not self.staff_id:
            self.generate_staff_id()
            super().save(update_fields=["staff_id"])

    def bump_token_version(self):
        """
        ✅ Call this after password reset/change to force logout.
        """
        self.token_version = (self.token_version or 0) + 1
        self.password_changed_at = timezone.now()
        self.save(update_fields=["token_version", "password_changed_at"])

    def __str__(self):
        return f"{self.email} ({self.role})"

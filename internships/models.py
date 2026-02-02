from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class SupervisorIntern(models.Model):
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_intern_links",
        # ✅ If you also want admin to be able to act as supervisor in Django admin,
        # change to: {"role__in": ["supervisor", "admin"]}
        limit_choices_to={"role": "supervisor"},
    )
    intern = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="supervisor_link",
        limit_choices_to={"role": "intern"},
    )

    # ✅ Supervisor progress + feedback (0..5)
    progress_rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    feedback = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.supervisor} -> {self.intern}"


class Task(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    )

    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": "intern"},
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_assigned",
        # ✅ If admin can assign tasks too, use role__in below
        limit_choices_to={"role": "supervisor"},
        # limit_choices_to={"role__in": ["supervisor", "admin"]},
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.intern} - {self.title} ({self.status})"


class Attendance(models.Model):
    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, default="present")  # present/absent/leave
    note = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["intern", "date"], name="uniq_attendance_per_day")
        ]

    def __str__(self):
        return f"{self.intern} {self.date} {self.status}"


class MonthlyReport(models.Model):
    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    month = models.CharField(max_length=7)  # YYYY-MM
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month"]
        constraints = [
            models.UniqueConstraint(fields=["intern", "month"], name="uniq_report_per_month")
        ]

    def __str__(self):
        return f"{self.intern} {self.month}"


class Complaint(models.Model):
    intern = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, default="open")  # open/resolved
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.intern} {self.title} ({self.status})"


class ActivityLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internship_activity_logs",
    )
    action = models.CharField(max_length=120)
    entity = models.CharField(max_length=120, blank=True, default="")
    entity_id = models.IntegerField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = getattr(self.actor, "email", None) if self.actor else None
        who = who or "System"
        return f"{self.created_at} {who} {self.action}"

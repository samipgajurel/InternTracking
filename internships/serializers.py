from datetime import date
from rest_framework import serializers
from .models import Task, Attendance, MonthlyReport, Complaint


# ---------------- TASKS ----------------
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "intern",
            "supervisor",
            "title",
            "description",
            "status",
            "due_date",
            "created_at",
            "updated_at",
        ]
        # ✅ supervisor is set from request.user in the view
        # ✅ intern is allowed when creating (admin/supervisor chooses intern)
        read_only_fields = ["id", "supervisor", "created_at", "updated_at"]


class InternTaskUpdateSerializer(serializers.ModelSerializer):
    """
    ✅ Use this for intern update endpoint (/tasks/my/<pk>/)
    Intern should ONLY update status (and maybe description if you want).
    """
    class Meta:
        model = Task
        fields = ["status"]
        # keep it strict


# ---------------- ATTENDANCE ----------------
class AttendanceSerializer(serializers.ModelSerializer):
    # ✅ Make date optional so POST without date won't 400
    date = serializers.DateField(required=False)

    class Meta:
        model = Attendance
        fields = ["id", "date", "status", "note"]
        read_only_fields = ["id"]

    def validate_status(self, value):
        value = (value or "").strip().lower()
        allowed = {"present", "absent", "leave"}
        if value not in allowed:
            raise serializers.ValidationError("status must be present/absent/leave")
        return value

    def create(self, validated_data):
        """
        ✅ Default date to today if not provided.
        ✅ Enforce unique per day by update_or_create.
        """
        request = self.context.get("request")
        intern = getattr(request, "user", None)

        if "date" not in validated_data:
            validated_data["date"] = date.today()

        obj, _ = Attendance.objects.update_or_create(
            intern=intern,
            date=validated_data["date"],
            defaults={
                "status": validated_data.get("status", "present"),
                "note": validated_data.get("note", ""),
            },
        )
        return obj


# ---------------- REPORTS ----------------
class MonthlyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReport
        fields = ["id", "month", "summary", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_month(self, value):
        """
        ✅ Enforce YYYY-MM format.
        """
        value = (value or "").strip()
        if len(value) != 7 or value[4] != "-":
            raise serializers.ValidationError("month must be in YYYY-MM format")
        return value


# ---------------- COMPLAINTS ----------------
class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ["id", "title", "message", "status", "created_at"]
        # ✅ Intern cannot set status; admin/supervisor will update separately
        read_only_fields = ["id", "status", "created_at"]


class ComplaintStatusUpdateSerializer(serializers.ModelSerializer):
    """
    ✅ Use for admin/supervisor endpoint: update complaint status.
    """
    class Meta:
        model = Complaint
        fields = ["status"]

    def validate_status(self, value):
        value = (value or "").strip().lower()
        allowed = {"open", "resolved"}
        if value not in allowed:
            raise serializers.ValidationError("status must be open/resolved")
        return value

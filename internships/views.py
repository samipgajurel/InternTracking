from datetime import date
from io import BytesIO
import csv

from django.http import HttpResponse
from django.utils.dateparse import parse_date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from accounts.models import User
from accounts.permissions import IsAdmin, IsAdminOrSupervisor, IsIntern

from .models import SupervisorIntern, Task, Attendance, MonthlyReport, Complaint, ActivityLog
from .serializers import (
    TaskSerializer,
    AttendanceSerializer,
    MonthlyReportSerializer,
    ComplaintSerializer,
)


# ----------------- ACTIVITY LOGGING -----------------
def log_activity(actor, action, entity="", entity_id=None, message=""):
    ActivityLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        message=message,
    )


# ----------------- HELPERS -----------------
def supervisor_owns_intern(supervisor: User, intern_id: int) -> bool:
    return SupervisorIntern.objects.filter(supervisor=supervisor, intern_id=intern_id).exists()


def compute_performance(intern: User):
    total_tasks = Task.objects.filter(intern=intern).count()
    done_tasks = Task.objects.filter(intern=intern, status="done").count()
    completion = (done_tasks / total_tasks) if total_tasks else 0.0

    att_total = Attendance.objects.filter(intern=intern).count()
    att_present = Attendance.objects.filter(intern=intern, status="present").count()
    attendance_rate = (att_present / att_total) if att_total else 0.0

    overdue = Task.objects.filter(
        intern=intern,
        status__in=["pending", "in_progress"],
        due_date__isnull=False,
        due_date__lt=date.today()
    ).count()

    score = int(round(completion * 60 + attendance_rate * 40 - min(overdue * 3, 15)))
    score = max(0, min(100, score))
    return {
        "score": score,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "attendance_total": att_total,
        "attendance_present": att_present,
        "overdue": overdue,
    }


# ----------------- ADMIN: ACTIVITY LOG -----------------
class AdminActivityLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip().lower()
        qs = ActivityLog.objects.select_related("actor").all().order_by("-created_at")[:300]

        out = []
        for a in qs:
            actor_email = (a.actor.email if a.actor else "")
            hay = f"{a.action} {a.entity} {a.message} {actor_email}".lower()
            if q and q not in hay:
                continue

            out.append({
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "action": a.action,
                "entity": a.entity,
                "entity_id": a.entity_id,
                "message": a.message,
                "actor": None if not a.actor else {
                    "id": a.actor.id,
                    "email": a.actor.email,
                    "staff_id": a.actor.staff_id,
                    "role": a.actor.role,
                }
            })
        return Response(out)


# ----------------- ADMIN: ANALYTICS -----------------
class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_tasks = Task.objects.count()
        done_tasks = Task.objects.filter(status="done").count()
        completion_rate = (done_tasks / total_tasks * 100) if total_tasks else 0

        complaints_total = Complaint.objects.count()
        complaints_open = Complaint.objects.filter(status="open").count()

        supervisors_count = User.objects.filter(role="supervisor").count()
        interns_count = User.objects.filter(role="intern").count()

        def month_key(dt):
            return dt.strftime("%Y-%m")

        months_set = set()
        tasks_series, done_series, complaints_series = {}, {}, {}

        for t in Task.objects.all().values("created_at", "status"):
            m = month_key(t["created_at"])
            months_set.add(m)
            tasks_series[m] = tasks_series.get(m, 0) + 1
            if t["status"] == "done":
                done_series[m] = done_series.get(m, 0) + 1

        for c in Complaint.objects.all().values("created_at"):
            m = month_key(c["created_at"])
            months_set.add(m)
            complaints_series[m] = complaints_series.get(m, 0) + 1

        months = sorted(months_set)[-6:]

        return Response({
            "totals": {
                "tasks": total_tasks,
                "tasks_done": done_tasks,
                "completion_rate": round(completion_rate, 2),
                "complaints": complaints_total,
                "complaints_open": complaints_open,
                "supervisors": supervisors_count,
                "interns": interns_count,
            },
            "months": months,
            "series": {
                "tasks_created": [tasks_series.get(m, 0) for m in months],
                "tasks_done": [done_series.get(m, 0) for m in months],
                "complaints_created": [complaints_series.get(m, 0) for m in months],
            }
        })


# ----------------- ADMIN: ASSIGNMENTS -----------------
class AdminAssignmentsListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip().lower()
        qs = SupervisorIntern.objects.select_related("intern", "supervisor").order_by("-created_at")

        out = []
        for link in qs:
            intern = link.intern
            sup = link.supervisor

            if q:
                hay = " ".join([
                    (intern.full_name or "").lower(),
                    (intern.email or "").lower(),
                    (intern.staff_id or "").lower(),
                    (sup.full_name or "").lower(),
                    (sup.email or "").lower(),
                    (sup.staff_id or "").lower(),
                ])
                if q not in hay:
                    continue

            out.append({
                "id": link.id,
                "created_at": link.created_at.isoformat(),
                "intern": {
                    "id": intern.id,
                    "staff_id": intern.staff_id,
                    "full_name": intern.full_name,
                    "email": intern.email
                },
                "supervisor": {
                    "id": sup.id,
                    "staff_id": sup.staff_id,
                    "full_name": sup.full_name,
                    "email": sup.email
                },
                "progress_rating": link.progress_rating,
                "feedback": link.feedback,
            })
        return Response(out)


class AdminUnassignInternView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        link_id = request.data.get("link_id")
        if not link_id:
            return Response({"detail": "link_id required"}, status=400)

        deleted, _ = SupervisorIntern.objects.filter(id=link_id).delete()
        if deleted == 0:
            return Response({"detail": "Assignment not found"}, status=404)

        log_activity(request.user, "unassign_intern", "SupervisorIntern", link_id, "Admin unassigned intern mapping")
        return Response({"detail": "✅ Unassigned successfully"})


# ----------------- SUPERVISOR: INTERN LIST -----------------
class SupervisorInternListView(APIView):
    permission_classes = [IsAdminOrSupervisor]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip().lower()

        if request.user.role == "admin":
            links = SupervisorIntern.objects.select_related("intern", "supervisor").all().order_by("-created_at")
        else:
            links = SupervisorIntern.objects.select_related("intern", "supervisor").filter(
                supervisor=request.user
            ).order_by("-created_at")

        out = []
        for link in links:
            i = link.intern
            if q:
                hay = f"{i.email} {i.full_name} {(i.staff_id or '')}".lower()
                if q not in hay:
                    continue

            out.append({
                "id": i.id,
                "staff_id": i.staff_id,
                "full_name": i.full_name,
                "email": i.email,
                "performance": compute_performance(i),
                "progress_rating": link.progress_rating,
                "feedback": link.feedback,
            })
        return Response(out)


class SupervisorUpdateInternProgressView(APIView):
    permission_classes = [IsAdminOrSupervisor]

    def post(self, request):
        intern_id = request.data.get("intern_id")
        rating = request.data.get("rating")
        feedback = (request.data.get("feedback") or "").strip()

        if not intern_id:
            return Response({"detail": "intern_id required"}, status=400)

        try:
            intern_id = int(intern_id)
        except:
            return Response({"detail": "intern_id must be integer"}, status=400)

        try:
            rating = int(rating)
        except:
            return Response({"detail": "rating must be integer 0..5"}, status=400)

        if rating < 0 or rating > 5:
            return Response({"detail": "rating must be between 0 and 5"}, status=400)

        qs = SupervisorIntern.objects.filter(intern_id=intern_id)
        if request.user.role == "supervisor":
            qs = qs.filter(supervisor=request.user)

        link = qs.first()
        if not link:
            return Response({"detail": "Not allowed or intern not assigned."}, status=403)

        link.progress_rating = rating
        link.feedback = feedback
        link.save(update_fields=["progress_rating", "feedback"])

        log_activity(request.user, "update_progress", "SupervisorIntern", link.id, f"rating={rating}")
        return Response({"detail": "✅ Progress & feedback saved"})


# ----------------- TASKS -----------------
class TaskCreate(APIView):
    permission_classes = [IsAdminOrSupervisor]

    def post(self, request):
        raw_intern = request.data.get("intern") or request.data.get("intern_id")
        try:
            intern_id = int(raw_intern)
        except:
            return Response({"detail": "intern (id) required"}, status=400)

        title = (request.data.get("title") or "").strip()
        description = (request.data.get("description") or "").strip()
        status_val = (request.data.get("status") or "pending").strip().lower()
        raw_due = request.data.get("due_date")

        if not title:
            return Response({"detail": "title required"}, status=400)

        if status_val not in ["pending", "in_progress", "done"]:
            return Response({"detail": "status must be pending/in_progress/done"}, status=400)

        if request.user.role == "supervisor" and not supervisor_owns_intern(request.user, intern_id):
            return Response({"detail": "Not allowed (ownership rule)."}, status=403)

        due_date = None
        if raw_due:
            due_date = parse_date(str(raw_due))
            if due_date is None:
                return Response({"detail": "due_date must be YYYY-MM-DD"}, status=400)

        task = Task.objects.create(
            intern_id=intern_id,
            supervisor=request.user if request.user.role == "supervisor" else None,
            title=title,
            description=description,
            status=status_val,
            due_date=due_date,
        )

        log_activity(request.user, "create_task", "Task", task.id, task.title)
        return Response(TaskSerializer(task).data, status=201)


class SupervisorTasks(generics.ListAPIView):
    permission_classes = [IsAdminOrSupervisor]
    serializer_class = TaskSerializer

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Task.objects.all().order_by("-created_at")
        return Task.objects.filter(supervisor=self.request.user).order_by("-created_at")


class InternMyTasks(generics.ListAPIView):
    permission_classes = [IsIntern]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(intern=self.request.user).order_by("-created_at")


class InternUpdateTask(generics.UpdateAPIView):
    """
    ✅ Intern should NOT be able to change title/description/supervisor/intern.
    Only allow status update.
    """
    permission_classes = [IsIntern]
    serializer_class = TaskSerializer  # keep if your frontend sends full object; otherwise create a special serializer

    def get_queryset(self):
        return Task.objects.filter(intern=self.request.user)

    def perform_update(self, serializer):
        # IMPORTANT: if you want strict update, create a new serializer with fields=["status"]
        obj = serializer.save()
        log_activity(self.request.user, "update_task", "Task", obj.id, f"status={obj.status}")


# ----------------- ATTENDANCE -----------------
class InternAttendanceListCreate(generics.ListCreateAPIView):
    permission_classes = [IsIntern]
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        return Attendance.objects.filter(intern=self.request.user).order_by("-date")

    def create(self, request, *args, **kwargs):
        """
        ✅ Fix: frontend may send only {"status": "present"}.
        We'll default date=today and upsert.
        """
        status_val = (request.data.get("status") or "present").strip().lower()
        note = (request.data.get("note") or "").strip()
        raw_date = request.data.get("date")

        if raw_date:
            d = parse_date(str(raw_date))
            if d is None:
                return Response({"detail": "date must be YYYY-MM-DD"}, status=400)
        else:
            d = date.today()

        obj, _created = Attendance.objects.update_or_create(
            intern=request.user,
            date=d,
            defaults={"status": status_val, "note": note},
        )
        log_activity(request.user, "mark_attendance", "Attendance", obj.id, f"{obj.date} {obj.status}")
        return Response(AttendanceSerializer(obj).data, status=201)


# ----------------- REPORTS -----------------
class InternReportListCreate(generics.ListCreateAPIView):
    permission_classes = [IsIntern]
    serializer_class = MonthlyReportSerializer

    def get_queryset(self):
        return MonthlyReport.objects.filter(intern=self.request.user).order_by("-month")

    def perform_create(self, serializer):
        obj = serializer.save(intern=self.request.user)
        log_activity(self.request.user, "create_report", "MonthlyReport", obj.id, obj.month)


class InternReportExportCSV(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        month = (request.query_params.get("month") or "").strip()
        qs = MonthlyReport.objects.filter(intern=request.user)
        if month:
            qs = qs.filter(month=month)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="monthly_reports.csv"'
        writer = csv.writer(response)
        writer.writerow(["month", "summary", "created_at"])
        for r in qs.order_by("-month"):
            writer.writerow([r.month, r.summary, r.created_at.isoformat()])
        return response


class InternReportExportPDF(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        month = (request.query_params.get("month") or "").strip()
        qs = MonthlyReport.objects.filter(intern=request.user)
        if month:
            qs = qs.filter(month=month)

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        y = height - 60
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, f"Monthly Reports - {request.user.full_name} ({request.user.staff_id or ''})")
        y -= 30

        for r in qs.order_by("-month"):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, r.month)
            y -= 16

            c.setFont("Helvetica", 11)
            text = r.summary or ""
            while text:
                line = text[:100]
                text = text[100:]
                c.drawString(60, y, line)
                y -= 14
                if y < 80:
                    c.showPage()
                    y = height - 60
            y -= 10

        c.showPage()
        c.save()
        buf.seek(0)

        resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="monthly_reports.pdf"'
        return resp


# ----------------- COMPLAINTS -----------------
class InternComplaintListCreate(generics.ListCreateAPIView):
    permission_classes = [IsIntern]
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        return Complaint.objects.filter(intern=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        obj = serializer.save(intern=self.request.user)
        log_activity(self.request.user, "create_complaint", "Complaint", obj.id, obj.title)


class SupervisorComplaintListView(APIView):
    permission_classes = [IsAdminOrSupervisor]

    def get(self, request):
        if request.user.role == "admin":
            qs = Complaint.objects.select_related("intern").order_by("-created_at")[:300]
        else:
            qs = Complaint.objects.select_related("intern").filter(
                intern__supervisor_link__supervisor=request.user
            ).order_by("-created_at")[:300]

        out = []
        for c in qs:
            out.append({
                "id": c.id,
                "created_at": c.created_at.isoformat(),
                "title": c.title,
                "message": c.message,
                "status": c.status,
                "intern": {
                    "id": c.intern.id,
                    "full_name": c.intern.full_name,
                    "email": c.intern.email,
                    "staff_id": c.intern.staff_id,
                }
            })
        return Response(out)


class SupervisorComplaintUpdateStatusView(APIView):
    permission_classes = [IsAdminOrSupervisor]

    def post(self, request):
        complaint_id = request.data.get("complaint_id")
        status_val = (request.data.get("status") or "").strip().lower()

        if status_val not in ["open", "resolved"]:
            return Response({"detail": "status must be open or resolved"}, status=400)

        try:
            complaint_id = int(complaint_id)
        except:
            return Response({"detail": "complaint_id required"}, status=400)

        c = Complaint.objects.select_related("intern").filter(id=complaint_id).first()
        if not c:
            return Response({"detail": "Complaint not found"}, status=404)

        if request.user.role == "supervisor":
            ok = SupervisorIntern.objects.filter(supervisor=request.user, intern=c.intern).exists()
            if not ok:
                return Response({"detail": "Not allowed"}, status=403)

        c.status = status_val
        c.save(update_fields=["status"])

        log_activity(request.user, "update_complaint", "Complaint", c.id, f"status={status_val}")
        return Response({"detail": "✅ Complaint status updated"})


# ----------------- INTERN: SUPERVISOR + FEEDBACK -----------------
class InternMySupervisorView(APIView):
    permission_classes = [IsIntern]

    def get(self, request):
        link = SupervisorIntern.objects.filter(intern=request.user).select_related("supervisor").first()
        if not link:
            return Response({"assigned": False, "detail": "No supervisor assigned yet."})

        s = link.supervisor
        return Response({
            "assigned": True,
            "supervisor": {
                "id": s.id,
                "staff_id": s.staff_id,
                "full_name": s.full_name,
                "email": s.email,
            },
            "progress_rating": link.progress_rating,
            "feedback": link.feedback,
        })

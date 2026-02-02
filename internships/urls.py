from django.urls import path
from .views import (
    AdminAnalyticsView,
    AdminAssignmentsListView,
    AdminUnassignInternView,
    AdminActivityLogView,

    SupervisorInternListView,
    SupervisorUpdateInternProgressView,

    TaskCreate,
    SupervisorTasks,
    InternMyTasks,
    InternUpdateTask,

    InternAttendanceListCreate,
    InternReportListCreate,
    InternReportExportCSV,
    InternReportExportPDF,

    InternComplaintListCreate,
    InternMySupervisorView,

    SupervisorComplaintListView,
    SupervisorComplaintUpdateStatusView,
)

urlpatterns = [
    # ---------------- ADMIN ----------------
    path("admin/analytics/", AdminAnalyticsView.as_view()),
    path("admin/assignments/", AdminAssignmentsListView.as_view()),
    path("admin/unassign/", AdminUnassignInternView.as_view()),
    path("admin/activity/", AdminActivityLogView.as_view()),

    # ---------------- SUPERVISOR ----------------
    path("supervisor/interns/", SupervisorInternListView.as_view()),
    path("supervisor/intern-progress/", SupervisorUpdateInternProgressView.as_view()),
    path("tasks/supervisor/", SupervisorTasks.as_view()),

    path("complaints/supervisor/", SupervisorComplaintListView.as_view()),
    path("complaints/update-status/", SupervisorComplaintUpdateStatusView.as_view()),

    # ---------------- TASKS ----------------
    path("tasks/create/", TaskCreate.as_view()),

    # ✅ Intern tasks (your current)
    path("tasks/my/", InternMyTasks.as_view()),
    path("tasks/my/<int:pk>/", InternUpdateTask.as_view()),

    # ✅ Alias for your frontend that calls /api/intern/tasks/
    path("intern/tasks/", InternMyTasks.as_view()),
    path("intern/tasks/<int:pk>/", InternUpdateTask.as_view()),

    # ---------------- ATTENDANCE ----------------
    path("attendance/my/", InternAttendanceListCreate.as_view()),

    # ---------------- REPORTS ----------------
    path("reports/my/", InternReportListCreate.as_view()),
    path("reports/my/export/csv/", InternReportExportCSV.as_view()),
    path("reports/my/export/pdf/", InternReportExportPDF.as_view()),

    # ---------------- COMPLAINTS ----------------
    path("complaints/my/", InternComplaintListCreate.as_view()),

    # ---------------- INTERN ----------------
    path("intern/my-supervisor/", InternMySupervisorView.as_view()),
]

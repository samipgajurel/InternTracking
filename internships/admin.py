from django.contrib import admin
from .models import SupervisorIntern, Task, Attendance, MonthlyReport, Complaint, ActivityLog

admin.site.register(SupervisorIntern)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(MonthlyReport)
admin.site.register(Complaint)
admin.site.register(ActivityLog)

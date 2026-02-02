from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "staff_id", "email", "full_name", "role", "is_verified", "is_active", "created_at")
    search_fields = ("email", "full_name", "staff_id")
    list_filter = ("role", "is_verified", "is_active")

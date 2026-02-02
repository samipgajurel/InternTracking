from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "admin")

class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "supervisor")

class IsIntern(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "intern")

class IsAdminOrSupervisor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role in ["admin", "supervisor"])

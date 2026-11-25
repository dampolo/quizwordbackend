from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    message = 'Only superusers can access company data.'

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_superuser)

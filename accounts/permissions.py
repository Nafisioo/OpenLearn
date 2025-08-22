from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        if hasattr(obj, "pk") and getattr(obj, "username", None) is not None:
            return obj == request.user

        if hasattr(obj, "user"):
            return obj.user == request.user

        return False
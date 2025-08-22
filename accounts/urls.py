from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, StudentViewSet, ParentViewSet, DepartmentHeadViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"parents", ParentViewSet, basename="parent")
router.register(r"department-heads", DepartmentHeadViewSet, basename="departmenthead")

urlpatterns = [
    path("", include(router.urls)),
]

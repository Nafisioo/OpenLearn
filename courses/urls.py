from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('', include(router.urls)),
    path('my-enrollments/', CourseViewSet.as_view({'get': 'my_courses'}), name='my_enrollments')
]

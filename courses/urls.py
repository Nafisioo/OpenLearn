from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonViewSet,
    EnrolledCoursesListView,
    MarkLessonCompleteView,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')

urlpatterns = [
    path('', include(router.urls)),
    path('my-enrollments/', EnrolledCoursesListView.as_view(), name='my_enrollments'),
    path('lessons/<int:lesson_id>/complete/', MarkLessonCompleteView.as_view(), name='mark_lesson_complete'),
]

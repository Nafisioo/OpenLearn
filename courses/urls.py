from django.urls import path
from .views import (
    CourseCreateView,
    CourseDetailView,
    EnrollInCourseView,
    EnrolledCoursesListView,
    MarkLessonCompleteView
)

urlpatterns = [
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('create/', CourseCreateView.as_view(), name='course-create'),
    path('<int:pk>/enroll/', EnrollInCourseView.as_view(), name='course-enroll'),
    path('my-enrollments/', EnrolledCoursesListView.as_view(), name='my-enrollments'),
    path('lessons/<int:lesson_id>/complete/', MarkLessonCompleteView.as_view(), name='lesson-complete'),
]

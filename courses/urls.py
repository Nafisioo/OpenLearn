from django.urls import path
from .views import (
    CourseCreateView,
    CourseDetailView,
    EnrollInCourseView,
    EnrolledCoursesListView,
    MarkLessonCompleteView,
    CourseProgressView,
)

urlpatterns = [
    path('create/', CourseCreateView.as_view(), name='course_create'),  
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('<int:pk>/enroll/', EnrollInCourseView.as_view(), name='enroll_course'),
    path('my-enrollments/', EnrolledCoursesListView.as_view(), name='my_enrollments'),
    path('lessons/<int:lesson_id>/complete/', MarkLessonCompleteView.as_view(), name='mark_lesson_complete'),
    path('<int:course_id>/progress/', CourseProgressView.as_view(), name='course_progress'),
]


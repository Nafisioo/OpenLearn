from django.urls import path
from .views import CourseCreateView, CourseDetailView, EnrollInCourseView

urlpatterns = [
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('create/', CourseCreateView.as_view(), name='course-create'),
    path('<int:pk>/enroll/', EnrollInCourseView.as_view(), name='course-enroll'),
]

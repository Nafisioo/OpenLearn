from django.urls import path
from .views import CourseDetailView

urlpatterns = [
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
]

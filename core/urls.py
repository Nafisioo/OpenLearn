from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'news', views.NewsAndEventsViewSet)
router.register(r'sessions', views.SessionViewSet)
router.register(r'semesters', views.SemesterViewSet)

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('calendar/', views.AcademicCalendarView.as_view(), name='academic_calendar'),
]
from django.urls import path
from .views import SiteFeedbackView

urlpatterns = [
    path('feedback/', SiteFeedbackView.as_view(), name='site-feedback'),
]
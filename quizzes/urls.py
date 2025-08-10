from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizAttemptViewSet

router = DefaultRouter()
router.register('attempts', QuizAttemptViewSet, basename='attempt')
router.register('', QuizViewSet, basename='quiz')

urlpatterns = router.urls
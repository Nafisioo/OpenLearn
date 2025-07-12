from rest_framework import generics, permissions
from .models import SiteFeedback
from .serializers import SiteFeedbackSerializer

class SiteFeedbackView(generics.ListCreateAPIView):
    serializer_class = SiteFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SiteFeedback.objects.filter(user=self.request.user)

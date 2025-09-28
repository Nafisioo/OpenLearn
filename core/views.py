from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import NewsAndEvents, Session, Semester, ActivityLog
from .serializers import (
    NewsAndEventsSerializer,
    SessionSerializer, 
    SemesterSerializer,
    ActivityLogSerializer
)

class NewsAndEventsViewSet(viewsets.ModelViewSet):
    queryset = NewsAndEvents.objects.all().order_by("-created_at")
    serializer_class = NewsAndEventsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.query_params.get("search")
        if query:
            # assume NewsAndEvents has a search manager/method; fallback to filtering title/summary
            try:
                qs = qs.search(query)
            except Exception:
                qs = qs.filter(title__icontains=query) | qs.filter(summary__icontains=query)
        post_type = self.request.query_params.get("type")
        if post_type:
            qs = qs.filter(posted_as=post_type)
        return qs

class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().order_by("-created_at")
    serializer_class = SessionSerializer 
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'],permission_classes=[permissions.AllowAny])
    def current(self, request):
        # expecting Session.get_current() classmethod; fallback to filter
        current = None
        try:
            current = Session.get_current()
        except Exception:
            current_qs = Session.objects.filter(is_current=True).order_by("-created_at")
            current = current_qs.first()
        if not current:
            return Response({"detail": "No current session set."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(current).data, status=status.HTTP_200_OK)

class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all().order_by("-created_at")
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def current(self, request):
        current = None
        try:
            current = Semester.get_current()
        except Exception:
            current_qs = Semester.objects.filter(is_current=True).order_by("-created_at")
            current = current_qs.first()
        if not current:
            return Response({"detail": "No current semester set."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(current).data, status=status.HTTP_200_OK)

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all().order_by("-created_at")
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAdminUser]

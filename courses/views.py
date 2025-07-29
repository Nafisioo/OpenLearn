from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Course, Enrollment, Lesson
from .serializers import (
    CourseSerializer,
    LessonSerializer,
    EnrolledCourseSerializer,
    EnrollmentSerializer,
)
from .permissions import IsAdminOrInstructorOwnerOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAdminUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrInstructorOwnerOrReadOnly()]
        if self.action in ['enroll']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll(self, request, pk=None):
        course = self.get_object()
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response({"detail": "You are already enrolled in this course."},
                            status=status.HTTP_400_BAD_REQUEST)
        Enrollment.objects.create(user=request.user, course=course)
        return Response({"message": f"Successfully enrolled in {course.title}!"},
                        status=status.HTTP_201_CREATED)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            return [
                permissions.IsAuthenticated(),
                IsAdminOrInstructorOwnerOrReadOnly()
            ]
        return [permissions.AllowAny()]


class EnrolledCoursesListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Course.objects.filter(students=request.user)
        serializer = EnrolledCourseSerializer(qs, many=True)
        return Response(serializer.data)

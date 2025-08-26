from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Course
from .serializers import CourseSerializer, EnrolledCourseSerializer
from .permissions import IsAdminOrInstructorOwnerOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related("category", "instructor").prefetch_related("students")
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAdminUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrInstructorOwnerOrReadOnly()]
        if self.action in ['enroll', 'unenroll', 'my_courses']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        if course.students.filter(pk=user.pk).exists:
            return Response({"detail": "You are already enrolled."}, status=status.HTTP_400_BAD_REQUEST)
        course.students.add(user)
        return Response({"message": f"Successfully enrolled in {course.title}."},status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"])
    def unenroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        if not course.students.filter(pk=user.pk).exists():
            return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)
        course.students.remove(user)
        return Response({"message": f"Successfully unenrolled from {course.title}."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def my_courses(self, request):
        qs = Course.objects.filter(students=request.user).select_related("category", "instructor")
        serializer = EnrolledCourseSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


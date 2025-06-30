from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, Enrollment, Lesson, UserLessonProgress
from .serializers import (
    CourseSerializer,
    EnrollmentSerializer,
    EnrolledCourseSerializer,
    UserLessonProgressSerializer
)
from rest_framework.generics import ListAPIView

class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAdminUser] 

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'pk'

class EnrollInCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)

        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response(
                {"detail": "You are already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Enrollment.objects.create(user=request.user, course=course)
        return Response(
            {"message": f"Successfully enrolled in {course.title}!"},
            status=status.HTTP_201_CREATED
        )

class EnrolledCoursesListView(ListAPIView):
    serializer_class = EnrolledCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(enrollment__user=self.request.user)

class MarkLessonCompleteView(generics.CreateAPIView):
    serializer_class = UserLessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lesson_id = kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)

        progress, created = UserLessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'completed': True}
        )

        if not created:
            progress.completed = True
            progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)

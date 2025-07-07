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

        enrollment = Enrollment.objects.filter(user=request.user, course=lesson.course).first()
        if not enrollment:
            return Response({"detail": "You are not enrolled in this course."},
                            status=status.HTTP_403_FORBIDDEN)

        progress, created = UserLessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'completed': True}
        )

        if not created and not progress.completed:
            progress.completed = True
            progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CourseProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id): 
        course = Course.objects.filter(pk=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        lessons = Lesson.objects.filter(course=course)
        total = lessons.count()
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if not enrollment:
            return Response({"detail": "You are not enrolled in this course."},
                            status=status.HTTP_403_FORBIDDEN)
        completed = UserLessonProgress.objects.filter(
            enrollment=enrollment,
            lesson__in=lessons,
            completed=True
        ).count()

        progress = int((completed / total) * 100) if total > 0 else 0

        return Response({
            "course": course.title,
            "total_lessons": total,
            "completed_lessons": completed,
            "progress_percent": progress
        })


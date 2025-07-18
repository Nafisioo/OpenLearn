from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Course, Enrollment, Lesson, UserLessonProgress
from .serializers import (
    CourseSerializer,
    LessonSerializer,
    EnrolledCourseSerializer,
    UserLessonProgressSerializer,
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
        if self.action in ['enroll', 'progress']:
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

    @action(detail=True, methods=['get'], url_path='progress')
    def progress(self, request, pk=None):
        course = self.get_object()
        lessons = course.lessons.all()
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
        percent = int((completed / total) * 100) if total else 0
        return Response({
            "course": course.title,
            "total_lessons": total,
            "completed_lessons": completed,
            "progress_percent": percent
        })


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
        qs = Course.objects.filter(enrollment__user=request.user)
        serializer = EnrolledCourseSerializer(qs, many=True)
        return Response(serializer.data)


class MarkLessonCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id=None):
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
        serializer = UserLessonProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)

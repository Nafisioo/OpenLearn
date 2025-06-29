from rest_framework import generics, permissions
from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAdminUser] 


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'pk'
 
class EnrollInCourseView(generics.CreateAPIView):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EnrollInCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)

        # Prevent duplicate enrollment
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
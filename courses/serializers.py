from rest_framework import serializers
from .models import Course, Enrollment, UserLessonProgress, Lesson

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'instructor']
        read_only_fields = ['instructor']

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'enrolled_at']

class EnrolledCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description']

class UserLessonProgressSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserLessonProgress
        fields = ['id', 'user', 'lesson', 'completed']
        read_only_fields = ['user'] 

    def get_user(self, obj):
        return {
            "id": obj.enrollment.user.id if obj.enrollment and obj.enrollment.user else None,
            "username": obj.enrollment.user.username,
        }

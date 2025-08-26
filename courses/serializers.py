from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Course

User = get_user_model


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")

class CategoryField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        return {"id": value.id, "title": getattr(value, "title", str(value))}
    
class CourseSerializer(serializers.ModelSerializer):
    instructor = SimpleUserSerializer(read_only=True)
    students = SimpleUserSerializer(many=True, read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    category = CategoryField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "category",
            "instructor",
            "students",
            "students_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["instructor", "students", "students_count", "created_at", "updated_at"]

    def get_students_count(self, obj):
        return obj.students.count()
    
class EnrolledCourseSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(source="instructor.username", read_only=True)
    category = CategoryField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "category", "instructor"]

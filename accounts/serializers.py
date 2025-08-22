from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Student, Parent, DepartmentHead

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Student
        fields = ("id", "user", "level", "program")
        read_only_fields = ("id",)


class ParentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    students = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), many=True, required=False)

    class Meta:
        model = Parent
        fields = ("id", "user", "phone", "email", "students")
        read_only_fields = ("id",)


class DepartmentHeadSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = DepartmentHead
        fields = ("id", "user", "department")
        read_only_fields = ("id",)


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentSerializer(read_only=True)
    parent_profile = ParentSerializer(read_only=True)
    dept_head_profile = DepartmentHeadSerializer(read_only=True)
    picture_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "picture",
            "picture_url",
            "role",
            "is_active",
            "is_staff",
            "date_joined",
            "student_profile",
            "parent_profile",
            "dept_head_profile",
        )
        read_only_fields = ("id", "is_staff", "date_joined")

    def get_picture_url(self, obj):
        try:
            return obj.get_picture_url()
        except Exception:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    class Meta:
        model = User
        fields = ("id", "username", "password", "email", "first_name", "last_name", "phone", "role")
        read_only_fields = ("id",)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role(self, value):
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        if "role" not in validated_data or validated_data.get("role") is None:
            validated_data["role"] = User.Role.STUDENT
        user = User.objects.create_user(password=password, **validated_data)
        return user
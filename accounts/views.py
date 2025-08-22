from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .models import Student, Parent, DepartmentHead
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    StudentSerializer,
    ParentSerializer,
    DepartmentHeadSerializer,
)
from .permissions import IsOwnerOrAdmin

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserViewSet(viewsets.ModelViewSet):
    """
    /api/accounts/users/

    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ("list", "destroy"):
            return [IsAdminUser()]
        if self.action == "create":
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        validated_data["role"] = User.Role.STUDENT

        with transaction.atomic():
            user = serializer.create(validated_data)

        Student.objects.get_or_create(user=user)

        out_serializer = UserSerializer(user, context={"request": request})
        tokens = get_tokens_for_user(user)
        data = out_serializer.data
        data.update({"tokens": tokens})
        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("search")
        if q:
            return User.objects.search(q)
        return qs

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def set_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")
        if not role:
            return Response({"detail": "role is required"}, status=status.HTTP_400_BAD_REQUEST)
        user.role = role
        user.save(update_fields=["role"])
        return Response({"detail": "role updated", "role": user.role})

    def _ids_from_request(self, request):
        ids = request.data.get("ids") or request.data.get("user_ids") or []
        if not isinstance(ids, (list, tuple)):
            return []
        return [int(i) for i in ids]

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def make_students(self, request):
        ids = self._ids_from_request(request)
        qs = User.objects.filter(id__in=ids)
        with transaction.atomic():
            updated = qs.update(role=User.Role.STUDENT)
            created = 0
            for user in qs:
                obj, was_created = Student.objects.get_or_create(user=user)
                if was_created:
                    created += 1
        return Response({"updated": updated, "created_student_profiles": created})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def make_instructors(self, request):
        ids = self._ids_from_request(request)
        updated = User.objects.filter(id__in=ids).update(role=User.Role.INSTRUCTOR)
        return Response({"updated": updated})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def make_admins(self, request):
        ids = self._ids_from_request(request)
        if not request.user.is_superuser:
            return Response({"detail": "only superusers can promote to admin"}, status=status.HTTP_403_FORBIDDEN)
        updated = User.objects.filter(id__in=ids).update(role=User.Role.ADMIN, is_staff=True)
        return Response({"updated": updated})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def enable_users(self, request):
        ids = self._ids_from_request(request)
        updated = User.objects.filter(id__in=ids).update(is_active=True)
        return Response({"updated": updated})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def disable_users(self, request):
        ids = self._ids_from_request(request)
        updated = User.objects.filter(id__in=ids).update(is_active=False)
        return Response({"updated": updated})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def create_student_profiles(self, request):
        ids = self._ids_from_request(request)
        users = User.objects.filter(id__in=ids)
        created = 0
        with transaction.atomic():
            for user in users:
                _, was_created = Student.objects.get_or_create(user=user)
                if was_created:
                    created += 1
        return Response({"created_student_profiles": created})


class StudentViewSet(viewsets.ModelViewSet):
    """
    /api/accounts/students/

    """
    queryset = Student.objects.select_related("user", "program").all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_permissions(self):
        if self.action == "list":
            return [IsAdminUser()]
        return [perm() for perm in self.permission_classes]


class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.select_related("user").prefetch_related("students").all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_permissions(self):
        if self.action == "list":
            return [IsAdminUser()]
        return [perm() for perm in self.permission_classes]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_student(self, request, pk=None):
        parent = self.get_object()
        if not (request.user.is_staff or parent.user == request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get("student")
        if not student_id:
            return Response({"detail": "student id required"}, status=status.HTTP_400_BAD_REQUEST)
        student = get_object_or_404(Student, pk=student_id)
        parent.students.add(student)
        return Response({"detail": "student added"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def remove_student(self, request, pk=None):
        parent = self.get_object()
        if not (request.user.is_staff or parent.user == request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get("student")
        if not student_id:
            return Response({"detail": "student id required"}, status=status.HTTP_400_BAD_REQUEST)
        student = get_object_or_404(Student, pk=student_id)
        parent.students.remove(student)
        return Response({"detail": "student removed"}, status=status.HTTP_200_OK)


class DepartmentHeadViewSet(viewsets.ModelViewSet):
    queryset = DepartmentHead.objects.select_related("user", "department").all()
    serializer_class = DepartmentHeadSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_permissions(self):
        if self.action in ("list",):
            return [IsAdminUser()]
        return [perm() for perm in self.permission_classes]




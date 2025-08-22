from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from ..models import Student, Parent

User = get_user_model()


class AccountsAPITestCase(APITestCase):
    def setUp(self):
        # create a superuser (also is_staff)
        self.superuser = User.objects.create_superuser(
            username="superadmin",
            email="super@example.com",
            password="SuperPass123!",
        )

        # create a staff user (not superuser)
        self.staff = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="StaffPass123!",
            is_staff=True,
        )

        # regular user
        self.user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="RegularPass123!",
        )

    def test_open_registration_creates_user_and_returns_tokens_and_student_profile(self):
        """
        POST /api/accounts/users/ should allow open registration,
        create a User, create a Student profile and return tokens.
        """
        url = reverse("user-list")
        data = {
            "username": "alice",
            "password": "ComplexPass123!",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Example",
            # even if client sends role, create view forces STUDENT
            "role": "admin",
        }
        resp = self.client.post(url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

        # tokens returned
        assert "tokens" in resp.data and "access" in resp.data["tokens"] and "refresh" in resp.data["tokens"]

        # user exists and role is forced to STUDENT
        created_user = User.objects.get(username="alice")
        assert created_user.role == User.Role.STUDENT

        # Student profile created
        assert Student.objects.filter(user=created_user).exists()

    def test_me_endpoint_returns_authenticated_user(self):
        """
        GET /api/accounts/users/me/ returns the current user's data.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("user-me")
        resp = self.client.get(url, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["username"] == self.user.username
        assert resp.data["email"] == self.user.email

    def test_user_list_is_admin_only(self):
        """
        Regular users should not be allowed to list users; staff/superuser can.
        """
        url = reverse("user-list")

        # regular user forbidden
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(url)
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

        # staff user allowed to list (is_staff True)
        self.client.force_authenticate(user=self.staff)
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK

        # superuser also allowed
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK

    def test_parent_add_and_remove_student_permissions_and_behavior(self):
        """
        Test Parent.add_student and remove_student custom actions:
        - only the parent owner or staff can add/remove
        """
        # create a parent user and parent profile
        parent_user = User.objects.create_user(username="parent1", password="ParentPass123!")
        parent_profile = Parent.objects.create(user=parent_user)

        # create a student user + student profile
        student_user = User.objects.create_user(username="stud1", password="StudPass123!")
        student_profile = Student.objects.create(user=student_user)

        add_url = reverse("parent-add-student", args=[parent_profile.pk])
        remove_url = reverse("parent-remove-student", args=[parent_profile.pk])

        # non-owner non-staff cannot add
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(add_url, {"student": student_profile.pk}, format="json")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

        # owner can add
        self.client.force_authenticate(user=parent_user)
        resp = self.client.post(add_url, {"student": student_profile.pk}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        parent_profile.refresh_from_db()
        assert student_profile in parent_profile.students.all()

        # owner can remove
        resp = self.client.post(remove_url, {"student": student_profile.pk}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        parent_profile.refresh_from_db()
        assert student_profile not in parent_profile.students.all()

        # staff can add on behalf of parent
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(add_url, {"student": student_profile.pk}, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_make_admins_only_superuser_and_make_students_creates_profiles(self):
        """
        Test user-make-admins is restricted to superusers,
        and make_students sets role and creates Student profiles
        """
        # create a target user
        target = User.objects.create_user(username="target1", password="TargetPass123!")

        make_admins_url = reverse("user-make-admins")
        make_students_url = reverse("user-make-students")

        # staff (not superuser) should be forbidden to promote to admin
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(make_admins_url, {"ids": [target.pk]}, format="json")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

        # superuser can promote
        self.client.force_authenticate(user=self.superuser)
        resp = self.client.post(make_admins_url, {"ids": [target.pk]}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.role == User.Role.ADMIN
        assert target.is_staff is True

        # test make_students creates Student profile when missing
        # create another target without student profile
        target2 = User.objects.create_user(username="target2", password="Target2Pass123!")
        # ensure no profile exists
        assert not Student.objects.filter(user=target2).exists()

        resp = self.client.post(make_students_url, {"ids": [target2.pk]}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        target2.refresh_from_db()
        assert target2.role == User.Role.STUDENT
        assert Student.objects.filter(user=target2).exists()
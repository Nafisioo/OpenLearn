from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='student')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def validate_role(self, value):
        request = self.context['request']
        if value in ['admin', 'instructor'] and (not request.user.is_authenticated or not request.user.is_superuser):
            raise serializers.ValidationError("Only admins can assign this role.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'student')
        )
        return user

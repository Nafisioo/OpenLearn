from rest_framework import serializers
from .models import NewsAndEvents, Session, Semester, ActivityLog

class NewsAndEventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsAndEvents
        fields = ['id', 'title', 'summary', 'posted_as', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session 
        fields = ['id', 'name', 'is_current', 'next_session_begins', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
        is_current = data.get("is_current", False)
        if is_current:
            qs = Session.objects.filter(is_current=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("There is already a current session. Unset it first.")
        return data


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'semester', 'is_current', 'session', 'next_semester_begins', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
        is_current = data.get("is_current", False)
        session = data.get(
            "session",
            getattr(self.instance, "session", None) if self.instance else None,
        )
        if is_current and session is not None:
            qs = Semester.objects.filter(is_current=True, session=session)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("There is already a current semester for this session.")
        return data
   
    
class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'message', 'created_at']
        read_only_fields = ['created_at']
from rest_framework.generics import RetrieveAPIView
from .models import Course
from .serializers import CourseSerializer

class CourseDetailView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
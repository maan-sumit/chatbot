from rest_framework.viewsets import ModelViewSet
from chatbot.models import Feedback
from chatbot.serializers import FeedbackSerializer, FeedbackCreateSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status,filters

class FeedbackViewSet(ModelViewSet):
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated] #Note: using custom SSOBearerAuthentication


    def create(self, request, *args, **kwargs):
        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

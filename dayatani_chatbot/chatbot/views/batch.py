import uuid
import requests

from rest_framework.viewsets import ModelViewSet
from chatbot.models import FileTrainingStatus, FileBatch, Files, Logs
from chatbot.serializers import BatchStatusSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status, filters
from django.conf import settings
from chatbot.constants import Constant
from rest_framework import serializers
from chatbot.utils import log_user_activity
from rest_framework.decorators import action


class BatchStatusViewSet(ModelViewSet):
    queryset = FileBatch.objects.all().order_by('-created_at')
    serializer_class = BatchStatusSerializer
    # Note: using custom SSOBearerAuthentication
    permission_classes = [permissions.IsAuthenticated]

    
    @action(detail=False, methods=['get'], url_name='status',
            url_path='status')
    def batch_training_status(self, request, *args, **kwargs):
        data = request.data
        try:
            batch_id = request.query_params.get('batch_id')
            file_batch = FileBatch.objects.filter(batch_id=batch_id).first()
            if not file_batch:
                return Response({"error": "Invalid process id"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = BatchStatusSerializer(file_batch)
                
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e.args[0])
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
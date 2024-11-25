from rest_framework.viewsets import ModelViewSet
from chatbot.models import Logs
from chatbot.serializers import LogsSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status, filters
from django.conf import settings
from chatbot.utils import convert_str_to_datetime

from rest_framework import serializers
from django.db.models import Q
from datetime import datetime, timedelta
import uuid


class LogsViewSet(ModelViewSet):
    queryset = Logs.objects.all().order_by('-created_at')
    serializer_class = LogsSerializer
    # Note: using custom SSOBearerAuthentication
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        sort = self.request.query_params.get('sort')
        key = self.request.query_params.get('key')
        if key == 'user':
            key = 'user__name'
        
        if start_date:
            start_date = convert_str_to_datetime(start_date)
        
        if end_date:
            end_date = convert_str_to_datetime(end_date)
            end_date = end_date + timedelta(days=1)

        queryset = self.queryset
        if start_date and end_date:
            queryset = Logs.objects.filter(created_at__range=(start_date, end_date)).order_by('-created_at')
        
            if sort and sort == 'asc' and key:
                queryset = Logs.objects.filter(created_at__range=(start_date, end_date)).order_by(f'{key}')
            elif sort and sort == 'desc' and key:
                queryset = Logs.objects.filter(created_at__range=(start_date, end_date)).order_by(f'-{key}')
        else:
            if sort and sort == 'asc' and key:
                    queryset = Logs.objects.all().order_by(f'{key}')
            elif sort and sort == 'desc' and key:
                    queryset = Logs.objects.all().order_by(f'-{key}')

        return queryset



    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = LogsSerializer(queryset, many=True)
        return Response(serializer.data)
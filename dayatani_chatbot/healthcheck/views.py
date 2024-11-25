
# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from chatbot.utils import invoke_llm_service_healthcheck
from rest_framework import status,filters
from chatbot.models import Conversation

class HealthcheckAPI(APIView):

    def get(self, request, format=None):
        try:
            Conversation.objects.all()
            data = 'hi'
            data_list = []
            for i in invoke_llm_service_healthcheck(data, None):
                data_list.append(i)
            if len(data_list) > 0:
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

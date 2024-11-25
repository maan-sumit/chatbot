from rest_framework.viewsets import ModelViewSet
from chatbot.models import Conversation
from chatbot.serializers import ConversationSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status,filters

class ConversationViewSet(ModelViewSet):
    queryset = Conversation.objects.all().order_by('-created_at')
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated] #Note: using custom SSOBearerAuthentication

    def list(self, request, *args, **kwargs):
        queryset = Conversation.objects.filter(user=request.user, whatsapp_chat=False).order_by('-conversation_detail_modified_at')
        serializer = ConversationSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

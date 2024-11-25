import os

from rest_framework.viewsets import ModelViewSet
from chatbot.models import ConversationDetail, Conversation
from chatbot.serializers import ConversationDetailSerializer, ConversationDetailCreateSerializer
from rest_framework.response import Response
from rest_framework import status,filters
from chatbot.utils import invoke_llm_service, invoke_llm_service_client
from django.http import StreamingHttpResponse
from rest_framework import viewsets, permissions
from dotenv import load_dotenv
from rest_framework.decorators import action
load_dotenv()

class ChatViewSet(ModelViewSet):
    queryset = ConversationDetail.objects.all().order_by('-created_at')
    serializer_class = ConversationDetailSerializer
    permission_classes = [permissions.IsAuthenticated] #Note: using custom SSOBearerAuthentication


    def list(self, request, *args, **kwargs):
        conversation_id = self.request.query_params.get('conversation_id')
        conversation_count = self.request.query_params.get('conversation_count')
        if not conversation_id:
            return Response({"error": "please provide a conversation id"})
        try:
            conversation = Conversation.objects.filter(id=conversation_id).first()
            if not conversation:
                return Response({"error": "invalid conversation id"})
        except:
            return Response({"error": "invalid conversation id"})
        if conversation.user != request.user:
            return Response({"error": "You cannot access other users chat"})
        queryset = ConversationDetail.objects.filter(conversation=conversation).order_by('created_at')
        if conversation_count:
            try:
                conversation_count = int(conversation_count)
            except:
                return Response({"error": "Invalid conversation count"})
            queryset = ConversationDetail.objects.filter(conversation=conversation).order_by('-created_at')[:conversation_count][::-1]
        serializer = ConversationDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    
    def create(self, request, *args, **kwargs):
        conversation_id = self.request.query_params.get('conversation_id')
        serializer = ConversationDetailCreateSerializer(data=request.data, context={'conversation_id': conversation_id if conversation_id else None, 'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        count = os.getenv('CONVERSATION_COUNT')
        chat_history = None
        if conversation_id:
            chat_history = ConversationDetail.objects.filter(conversation_id=conversation_id).values('role','conversations').order_by('-created_at')[:int(count)][::-1]
        return StreamingHttpResponse(invoke_llm_service(data, chat_history, request), content_type='text/event-stream')
    
    @action(detail=False, methods=['post'], url_name='chat_bertani',
            url_path='bertani')
    def chat_bertani(self, request, *args, **kwargs):
        conversation_id = self.request.query_params.get('conversation_id')
        serializer = ConversationDetailCreateSerializer(data=request.data, context={'conversation_id': conversation_id if conversation_id else None, 'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        count = os.getenv('CONVERSATION_COUNT')
        chat_history = None
        if conversation_id:
            chat_history = ConversationDetail.objects.filter(conversation_id=conversation_id).values('role','conversations').order_by('-created_at')[:int(count)][::-1]
        return StreamingHttpResponse(invoke_llm_service_client(data, chat_history, request), content_type='application/json')




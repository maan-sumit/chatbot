from rest_framework import serializers
from chatbot.models import Conversation, ConversationDetail

class ConversationSerializer(serializers.ModelSerializer):
    updated_at = serializers.SerializerMethodField(method_name='get_updated_at')
    user = serializers.SerializerMethodField(method_name='get_user')
    class Meta:
        model = Conversation
        fields = ['id', 'heading', 'answer', 'user', 'created_at', 'updated_at']

    
    def get_updated_at(self, obj):
        conversation_detail = ConversationDetail.objects.filter(conversation=obj).order_by('-created_at').first()
        return conversation_detail.updated_at
    
    def get_user(self, obj):
        return obj.user.sso_uid

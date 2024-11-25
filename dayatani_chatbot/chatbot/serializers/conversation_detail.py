from rest_framework import serializers
from chatbot.models import ConversationDetail, Conversation
from chatbot.constants import Constant
from datetime import datetime

class ConversationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationDetail
        fields = ['id', 'conversations', 'role',]



class ConversationDetailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationDetail
        fields = ['id', 'conversations', 'role']
    
    def validate(self, attrs):
        conversation_id = self.context.get('conversation_id')
        if conversation_id:
            try:
                conversation = Conversation.objects.filter(id=conversation_id).first()
                if not conversation:
                    raise serializers.ValidationError({"error": "Invalid conversation id"})

            except:
                raise serializers.ValidationError(
                    {
                        "error": "Invalid conversation id"
                        }
                    ,400
                )

        return super().validate(attrs)


    def create(self, validated_data):
        request =  self.context.get('request')
        conversations = validated_data.get('conversations')
        user = request.user
        conversation_id = self.context.get('conversation_id')
        if not conversation_id:
            conversation = Conversation.objects.create(heading=conversations, user=user)
        else:
            conversation = Conversation.objects.filter(id=conversation_id).first()
            conversation.heading = conversations
        
        conversation_detail = ConversationDetail.objects.create(conversation=conversation, conversations=conversations, role=Constant.USER)
        conversation.conversation_detail_modified_at = datetime.now()
        conversation.save()

        return conversation_detail

from rest_framework import serializers
from chatbot.models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Feedback
        fields = ['id', 'like', 'feedback']



class FeedbackCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = ['id', 'like', 'feedback', 'conversation_detail']


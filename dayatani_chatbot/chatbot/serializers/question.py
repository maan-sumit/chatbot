from rest_framework import serializers
from chatbot.models import Feedback


class QuestionSerializer(serializers.Serializer):
    questions = serializers.ListField(child=serializers.CharField())
    
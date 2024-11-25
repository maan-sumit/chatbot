from rest_framework import serializers
from chatbot.models import Logs

class LogsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Logs
        exclude = ('updated_at',)

    def get_user(self, obj):
        return obj.user.name


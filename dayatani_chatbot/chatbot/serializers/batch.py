from rest_framework import serializers
from chatbot.models import FileBatch

class BatchStatusSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FileBatch
        fields = ['id', 'batch_id', 'batch_processed', 'abort', 'created_at', 'updated_at']
        read_only_fields = ['batch_processed', 'abort']
        

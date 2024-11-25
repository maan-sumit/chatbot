from rest_framework import serializers
from chatbot.models import Files, FileTrainingStatus

class FileTrainingSerializer(serializers.ModelSerializer):
    files = serializers.ListField(child=serializers.UUIDField(), write_only=True)
    class Meta:
        model = FileTrainingStatus
        fields = ['files']


    def validate(self, attrs):
        for file_id in attrs.get('files'):
            if not Files.objects.filter(id=file_id).exists():
                raise serializers.ValidationError({"error": f"{file_id} does not exist"})
        return super().validate(attrs)
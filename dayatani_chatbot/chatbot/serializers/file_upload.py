from rest_framework import serializers
from chatbot.models import Files, FileTrainingStatus

class FileSerializer(serializers.ModelSerializer):
    files = serializers.ListField(child=serializers.FileField(), write_only=True)
    class Meta:
        model = Files
        fields = ['id', 'files', 'name', 'url', 'created_at']
        read_only_fields = ['name', 'url']


    def validate(self, attrs):
        files = attrs.get('files')
        for file in files:
            if not file.name.endswith('.pdf'):
                raise serializers.ValidationError({"error": "Only PDF files are allowed"})
        return super().validate(attrs)
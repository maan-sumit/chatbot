from rest_framework.viewsets import ModelViewSet
from chatbot.models import Files, FileBatch, FileTrainingStatus, Logs
from chatbot.serializers import FileSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status, filters
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from django.conf import settings
from chatbot.constants import Constant
from chatbot.utils import log_user_activity
from rest_framework import serializers
from django.db.models import Q
import uuid


class FileUploadViewSet(ModelViewSet):
    queryset = Files.objects.all().order_by('-created_at')
    serializer_class = FileSerializer
    # Note: using custom SSOBearerAuthentication
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        client_id = request.user.client_id
        files_queryset = Files.objects.filter(is_deleted=False, user__client_id=client_id)

        # if batch has started processing exclude files
        processed_batches = FileBatch.objects.filter(batch_processed=True, abort=False)
        processed_statuses = FileTrainingStatus.objects.filter(batch__in=processed_batches)
        files_queryset = files_queryset.exclude(id__in=processed_statuses.values('file'))

        # if batch could not be completed
        incompelete_batch = FileBatch.objects.filter(batch_processed=False)
        incomplete_processed_statuses = FileTrainingStatus.objects.filter(batch__in=incompelete_batch, processed=True)
        files_queryset = files_queryset.exclude(id__in=incomplete_processed_statuses.values('file'))

        queryset = files_queryset.order_by('-created_at')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)    

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            serializer = FileSerializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                return Response({"error": serializer.errors['error'][0]}, status=status.HTTP_400_BAD_REQUEST)
            files_data = serializer.validated_data['files']
            container_name = Constant.CONTAINER_NAME
            # Initialize Azure Blob Storage client
            blob_service_client = BlobServiceClient(
                account_url=settings.SAS_URL_TRAINING_MODEL, credential=settings.SAS_TOKEN_TRAINING_MODEL)

            # Upload the file to Azure Blob Storage
            file_id = None

            for file in files_data:
                split_name = file.name.split('.')
                file_name = split_name[0] + '_' + str(uuid.uuid1()) + '.' + split_name[1]
                blob_client = blob_service_client.get_blob_client(
                    container=container_name, blob=file_name)
                blob_client.upload_blob(file)
                file_obj = Files.objects.create(
                    user=request.user, name=file_name, url=blob_client.url, status='Uploaded')
                file_id = file_obj.id
            
                log_user_activity(request.user, f'{Constant.UPLOAD_FILE} {file.name}', blob_client.url)


            return Response({"message": "File uploaded successfully", 'id': file_id})

        except Exception as e:
            print(e.args[0])
            return Response({"message": "File upload failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        data = request.data
        file = self.get_object()
        try:
            if not file:
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
            file.is_deleted = True
            file.save()
            log_user_activity(request.user, f'{Constant.DELETE_FILE} {file.name}')
            return Response({"message": "File deleted successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e.args[0])
            return Response({"message": "File deletion failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

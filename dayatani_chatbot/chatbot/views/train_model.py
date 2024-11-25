import uuid
import requests
import os
import json

from rest_framework.viewsets import ModelViewSet
from chatbot.models import FileTrainingStatus, FileBatch, Files, Logs
from chatbot.serializers import FileTrainingSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status, filters
from django.conf import settings
from chatbot.constants import Constant
from rest_framework import serializers
from chatbot.utils import log_user_activity
from rest_framework.decorators import action
from chatbot.helpers import encrypt_message, decrypt_message



class TrainModelViewSet(ModelViewSet):
    queryset = FileTrainingStatus.objects.all().order_by('-created_at')
    serializer_class = FileTrainingSerializer
    # Note: using custom SSOBearerAuthentication
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            serializer = FileTrainingSerializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                return Response({"error": serializer.errors['error'][0]}, status=status.HTTP_400_BAD_REQUEST)
            files_data = data.get('files')
            file_names = []
            batch_id = str(uuid.uuid1())
            batch_status = FileBatch.objects.create(
                user=request.user, batch_id=batch_id)
            
            for file in files_data:
                file_obj = Files.objects.filter(id=file).first()
                FileTrainingStatus.objects.create(
                    batch=batch_status, file=file_obj)
                file_names.append(f'{Constant.AZURE_FILES_FOLDER_NAME}/{file_obj.name}')
            url = Constant.FILES_TRAINING_URL
            open_ai_dict = {
                'openai_api_type': request.session.get('openai_api_type', os.getenv('OPENAI_API_TYPE')),
                'openai_api_version': request.session.get('openai_api_version', os.getenv('OPENAI_API_VERSION')),
                'openai_api_base': request.session.get('openai_api_base', os.getenv('OPENAI_API_BASE')),
                'openai_api_key': request.session.get('openai_api_key', os.getenv('OPENAI_API_KEY')),
                'deployment_name_embedding': request.session.get('deployment_name_embedding', os.getenv('DEPLOYMENT_NAME_EMBEDDING')),
                'deployment_name_model': request.session.get('deployment_name_model', os.getenv('DEPLOYMENT_NAME_MODEL'))
            }

            serialized_data = json.dumps(open_ai_dict)
            encrypted_open_ai_dict = encrypt_message(serialized_data)
            client_id = request.user.client_id if request.user.client_id else os.getenv('DAYATANI_CLIENT_ID')
            data = {'file_names': file_names, 'process_id': batch_id, 'client_id': client_id, 'open_ai_dict': encrypted_open_ai_dict}
            
            response = requests.post(url, json=data)
            json_response = response.json()
            if response.status_code == 200:
                log_user_activity(request.user, Constant.TRAINED_MODEL)
                batch_status.batch_processed = True
                batch_status.save()
                return Response({"message": json_response['message'], "process_id": batch_id}, status=status.HTTP_200_OK)
            else:
                return Response({"message": json_response['message']}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e.args[0])
            return Response({"message": e.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_name='abort',
            url_path='abort')
    def abort_training(self, request, *args, **kwargs):
        data = request.data
        try:
            batch_id = data.get('batch_id')
            file_batch = FileBatch.objects.filter(batch_id=batch_id).first()
            if not file_batch:
                return Response({"error": "Invalid process id"}, status=status.HTTP_400_BAD_REQUEST)
            
            url = Constant.FILES_TRAINING_ABORT_URL
            data = {'process_id': batch_id}
            print("request_data", data, flush=True)
            response = requests.post(url, json=data)
            json_response = response.json()
            print("response_data", json_response, flush=True)
            if response.status_code == 200:
                file_batch.abort = True
                file_batch.batch_processed = False
                file_batch.save()
                log_user_activity(request.user, Constant.ABORT_TRAINING)
                
                return Response({"message": json_response['message']}, status=status.HTTP_200_OK)
            else:
                return Response({"message": json_response['message']}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e.args[0])
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
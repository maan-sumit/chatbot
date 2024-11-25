from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from chatbot.models import FileTrainingStatus, FileBatch


class WebHookViewset(ModelViewSet):
    queryset = None
    serializer_class = None
    permission_classes = [AllowAny,]

    @action(detail=False, methods=['post'], url_name='file',
            url_path='file')
    def file_training(self, request, *args, **kwargs):
        print("Recieved webhook request for file training status \n\n", request.data, flush=True)
        
        data = request.data
        batch_id = data.get('process_id')
        file_name = data.get('file_name')
        success = data.get('success')
        action = data.get('action')
        file_name = file_name.split('/')

        FileTrainingStatus.objects.filter(batch__batch_id=batch_id, file__name=file_name[-1]).update(processed=success)
        return Response({"detail": f"Recieved request for {action}"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_name='batch',
            url_path='batch')
    def batch_training(self, request, *args, **kwargs):
        print("Recieved webhook request for batch training status \n\n", request.data,  flush=True)
        data = request.data

        action = data.get('action')
        batch_id = data.get('process_id')
        success = True

        file_train = FileTrainingStatus.objects.filter(batch__batch_id=batch_id, processed=False)
        if len(file_train) > 0:
            success = False
        FileBatch.objects.filter(batch_id=batch_id).update(batch_processed=success)

        return Response({"detail": f"Recieved request for {action}"}, status=status.HTTP_200_OK)
    
        
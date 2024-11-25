from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import status, filters, permissions
from chatbot.utils import invoke_llm_service_whatsapp,remove_file, get_client
from chatbot.models import User, Conversation, ConversationDetail, UserWhatsappInfo, WhatsappFlow
from chatbot.serializers import ConversationSerializer
import requests
import os
from chatbot.constants import Constant
from datetime import datetime
import hashlib
import hmac
from django.utils.encoding import force_bytes
import json
from rest_framework.exceptions import PermissionDenied
from services import speech_to_text, text_to_speech
from requests_toolbelt.multipart.encoder import MultipartEncoder
from rq.job import Job

from rq.queue import Queue
from worker import conn
import logging
import uuid

logger = logging.getLogger("WHATSAPP")

class WhatsappModelViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    q = Queue('whatsapp_chatbot_queue',connection=conn)

    def check_permissions(self, request):
        """
        Check if the user has the necessary permissions.
        """
        if self.action == 'list':
            return  # Skip permission check for the 'list' method

        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied(detail='Permission denied.')
    
    def list(self, request, *args, **kwargs):
        body = request.body
        data = request.data
        print("Whatsapp webhook request recived. \n\n", data, flush=True)
       
         #Intial get request to verify webhook
        if request.query_params.get("hub.verify_token") == os.getenv(
            "WHATSAPP_VERIFY_TOKEN"
        ):
            return Response(
                int(request.query_params.get("hub.challenge")),
                status=status.HTTP_200_OK,
            )
        return Response("invalid token", status=status.HTTP_400_BAD_REQUEST)
    

    def enqueue_user_specific_job(self, request_obj):
        user_id = request_obj['user']['id']
        last_job_key = f"user:{user_id}:last_job_id"
        last_job_id = conn.get(last_job_key)
        depends_on = None

        if last_job_id:
            try:
                last_job = Job.fetch(last_job_id.decode('utf-8'), connection=conn)
                if last_job.get_status() in ['queued', 'started']:
                    depends_on = last_job
                else:
                    depends_on = None
            except Exception as e:
                depends_on = None
                print(f"Error fetching last job for user {user_id}: {e}")
        
        logger.info(depends_on)
        viewset_instance = WhatsappModelViewSet()
        # Enqueue the new job with dependency on the last job if it exists
        new_job = self.q.enqueue_call(
            func= viewset_instance.handle_message,
            args=(request_obj,),
            depends_on=depends_on,
            result_ttl=5000,
            timeout=180,
        )

        # Update the last job ID for the user in Redis
        res = conn.set(last_job_key, new_job.id)
        logger.info(res)

    def create(self, request, *args, **kwargs):
        try:
            request_obj = {
                'data': request.data,
                'user': {
                    'id': str(request.user.id),
                    'client_id': request.user.client_id
                },
                'open_ai_dict': {
                    'openai_api_type': request.session.get('openai_api_type', os.getenv('OPENAI_API_TYPE')),
                    'openai_api_version': request.session.get('openai_api_version', os.getenv('OPENAI_API_VERSION')),
                    'openai_api_base': request.session.get('openai_api_base', os.getenv('OPENAI_API_BASE')),
                    'openai_api_key': request.session.get('openai_api_key', os.getenv('OPENAI_API_KEY')),
                    'deployment_name_embedding': request.session.get('deployment_name_embedding', os.getenv('DEPLOYMENT_NAME_EMBEDDING')),
                    'deployment_name_model': request.session.get('deployment_name_model', os.getenv('DEPLOYMENT_NAME_MODEL'))
                }
            }

            '''
            viewset_instance = WhatsappModelViewSet()
            self.q.enqueue_call(
                func= viewset_instance.handle_message,
                args=(request_obj,),
                result_ttl=5000,
                timeout=180,
            )
            '''
            self.enqueue_user_specific_job(request_obj)
            return Response({"detail": f"acknowledged."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"detail": f"acknowledged."}, status=status.HTTP_200_OK)

    @classmethod    
    def handle_message(self,request):
        data = request['data'] 
        print("Whatsapp webhook request recived. \n\n", data, flush=True)

        if "messages" in data["entry"][0]["changes"][0]["value"]:
            phone_no = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            message_type = data["entry"][0]["changes"][0]["value"]["messages"][0]["type"]

            if message_type == 'text':
                message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
                self.handle_user_query(phone_no, message, request)
            elif message_type == 'audio':
                media_id = data["entry"][0]["changes"][0]["value"]["messages"][0]["audio"]["id"]
                self.handle_audio_query(phone_no=phone_no,media_id=media_id,request=request)
            elif message_type in ('contacts','document','sticker','video'):
                 self.send_whatsapp_messsage(phone_no=phone_no,message=Constant.WHATSAPP_UNSUPPORTED_FORMAT_MSG)
            elif message_type == 'location':
                self.handle_location_message(data["entry"][0]["changes"][0]["value"]['messages'][0],request,phone_no)
            elif message_type == 'interactive':
                self.handle_flow_message(data["entry"][0]["changes"][0]["value"]['messages'][0],request,phone_no)
            elif message_type == 'image':
                image_data = data["entry"][0]["changes"][0]["value"]['messages'][0]['image']
                self.handle_image_message(image_data,request,phone_no)
            elif message_type == 'button':
                payload = data["entry"][0]["changes"][0]["value"]['messages'][0]['button']['payload']
                self.handle_button_message(payload,request,phone_no)
    
    @classmethod
    def handle_button_message(self, payload, request, phone_no):
        user = self.get_user_from_id(request['user'])
        if payload:
            if payload in (Constant.WEATHER_UNSUBSCRIBE_PAYLOAD, Constant.CONTENT_UNSUBSCRIBE_PAYLOAD):
                user_whatsapp_info, created = UserWhatsappInfo.objects.get_or_create(user=user)
                setattr(user_whatsapp_info, 'unsubscribe', True)
                user_whatsapp_info.save()
                self.send_whatsapp_messsage(phone_no=phone_no, message=Constant.WHATSAPP_UNSUBSCRIBE_NOTIFICATION_MSG)            


    @classmethod
    def handle_image_message(self, image_data, request, phone_no):
        try:
            image_path = self.download_whatsapp_media_file(image_data['id'])
            image_blob_id = self.upload_to_blob(image_path)
            remove_file(image_path)
            caption = f'user sent an image with id={image_blob_id}'
            if 'caption' in image_data:
                caption += f"\n and asked this question: {image_data['caption']}"
            self.handle_user_query(phone_no
                                   ,caption
                                   ,request)
        except Exception as e:
            print('the exception', e)
            self.send_whatsapp_messsage(phone_no=phone_no,message=Constant.WHATSAPP_IMAGE_ERROR)


    @classmethod
    def upload_to_blob(self, image_path):
        file_name = os.path.basename(image_path)
        blob_service_client, container_client = get_client()
        with open(image_path, mode="rb") as data:
            container_client.upload_blob(name=file_name, data=data, overwrite=True)
        return file_name

    @classmethod
    def handle_location_message(self, data, request,phone_no):
        user = self.get_user_from_id(request['user'])
        try:
            latitude = data['location']['latitude']
            longitude = data['location']['longitude']
            whatsapp_info_data = {'latitude':latitude,'longitude':longitude}

            user_whatsapp_info, created = UserWhatsappInfo.objects.get_or_create(user=user)
            for key, value in whatsapp_info_data.items():
                setattr(user_whatsapp_info, key, value)
            user_whatsapp_info.save()
            self.handle_user_query(phone_no, f"user send location latitude={latitude} longitude={longitude}", request) 
        except Exception as e:
            print('the exception', e)

    @classmethod
    def handle_flow_message(self, data, request,phone_no):
        user = self.get_user_from_id(request['user'])
        try:
            json_data = data['interactive']['nfm_reply']['response_json']
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
            
            whatsapp_info_data = {}
            for field in ['name', 'profession', 'land_size', 'crop_growing', 'soil_type', 'latitude', 'longitude','unsubscribe']:
                if field in json_data:
                    whatsapp_info_data[field] = json_data[field]

            user_whatsapp_info, created = UserWhatsappInfo.objects.get_or_create(user=user)
            for key, value in whatsapp_info_data.items():
                setattr(user_whatsapp_info, key, value)
            user_whatsapp_info.save()
            if field == 'unsubscribe':
                self.send_whatsapp_messsage(phone_no=phone_no,message=Constant.WHATSAPP_UNSUBSCRIBE_NOTIFICATION_MSG)
            else:
                self.handle_user_query(phone_no, "try again", request) #send reply after save
        except Exception as e:
            print('the exception', e)

    @classmethod
    def handle_audio_query(self, phone_no, media_id,request):
        try:
            downloaded_file_path = self.download_whatsapp_media_file(media_id)
            response = speech_to_text.convert_to_text(downloaded_file_path)
            if not response:
                raise Exception
            remove_file(downloaded_file_path)
            answer = self.handle_user_query(phone_no=phone_no,question_message=response,request=request)
            output_audio_file_path = text_to_speech.text_to_speech(text=answer,dir_name=Constant.TEMP_DIR)
            self.send_whatsapp_audio(phone_no=phone_no,audio_file_path=output_audio_file_path)
            remove_file(output_audio_file_path)
        except Exception as e:
                print(e)
                self.send_whatsapp_messsage(phone_no=phone_no,message=Constant.WHATSAPP_AUDIO_ERROR)
                
    @classmethod
    def download_whatsapp_media_file(self, media_id):
        access_token = os.getenv('WHATSAPP_BEARER_TOKEN')
        media_url_endpoint = f"https://graph.facebook.com/v18.0/{media_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Step 1: Call the WhatsApp Cloud API to retrieve the media download URL
        media_response = requests.get(media_url_endpoint, headers=headers)
        if media_response.status_code != 200:
            print(f"Failed to retrieve media URL. Status code: {media_response.status_code}")
            return None
        
        media_info = media_response.json()
        download_url = media_info.get('url')
        mime_type = media_info.get('mime_type')
        
        if not download_url:
            print("Failed to get download URL from media info.")
            return None
        
        # Step 2: Create local output file in temp directory
        temp_dir = Constant.TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        mime_type_to_extension = {
            'audio/aac': '.aac',
            'audio/mp4': '.m4a',
            'audio/mpeg': '.mp3',
            'audio/amr': '.amr',
            'audio/ogg': '.ogg',
            'image/jpeg': '.jpeg',
            'image/png' : '.png'
        }
        extension = mime_type_to_extension.get(mime_type, None)
        if not extension:
            print(f"Could not determine file extension for MIME type: {mime_type}")
            return None
        
        output_filename = f"{media_id}{extension}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Step 3: Download the file from the retrieved URL
        response = requests.get(download_url, stream=True, headers=headers)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File downloaded successfully: {output_path}")
            return output_path
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return None
        

    @staticmethod
    def get_user_from_id(user_id):
        try:
            return User.objects.get(id=user_id['id'])
        except User.DoesNotExist:
            return None
    
    @classmethod
    def handle_user_query(self, phone_no, question_message, request):
        user = self.get_user_from_id(request['user'])
        user_info = self.get_user_whatsapp_info(user)
        conversation = Conversation.objects.filter(user=user, whatsapp_chat=True).first()
        count = os.getenv('CONVERSATION_COUNT')
        if not conversation:
            conversation = Conversation.objects.create(user=user, whatsapp_chat=True)
        
        ConversationDetail.objects.create(conversation=conversation, conversations=question_message, role=Constant.USER)
        conversation.conversation_detail_modified_at = datetime.now()
        conversation.heading = question_message
        conversation.save()

        chat_history = ConversationDetail.objects.filter(conversation=conversation).values('role','conversations').order_by('-created_at')[:int(count)][::-1]

        answer,flow = invoke_llm_service_whatsapp(question=question_message, chat_history=chat_history, conversation=conversation, request=request, user_info=user_info)
        self.send_whatsapp_messsage(phone_no=phone_no, message=answer,flow=flow)
        return answer
    
    @classmethod
    def get_user_whatsapp_info(self,user):
        try:
            user_whatsapp_info = UserWhatsappInfo.objects.get(user=user)
            info_dict = {}
            fields = ['name', 'profession', 'land_size', 'crop_growing', 'soil_type', 'location']

            for field in fields:
                value = getattr(user_whatsapp_info, field, None)
                if value not in [None, '']:
                    info_dict[field] = value

            return info_dict
        except UserWhatsappInfo.DoesNotExist:
            return {}

    @classmethod
    def send_whatsapp_messsage(self, phone_no, message, flow=None):
        url = os.getenv("WHATSAPP_API_URL") + '/messages'
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_BEARER_TOKEN')}",
            "Content-Type": "application/json",
        }

        flow_data = self.get_whatsapp_flow_id_cta(flow)
        if flow_data != None:
            screen = 'YOUR_INFORMATION'
            if len(message) > 1000:
                message = message[:1000]

            data = {
                "recipient_type": "individual",
                "messaging_product": "whatsapp",
                "to": f"{phone_no}",
                "type": "interactive",
                "interactive": {
                    "type": "flow",
                    "body": {
                        "text": f"{message}"
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "mode":"published",
                            "flow_message_version": "3",
                            "flow_token": "123456",
                            "flow_id": flow_data.flow_id,
                            "flow_cta": flow_data.cta,
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": screen
                            }
                        }
                    }
                }
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            print('RESPONSE FROM MESSAGE:',response.json())
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{phone_no}",
                "type": "text",
                "text": {"preview_url": False, "body": f"{message}"},
            }

            response = requests.post(url, headers=headers, json=payload)
            print('RESPONSE FROM MESSAGE SIMPLE:',response.json())

    @classmethod
    def get_whatsapp_flow_id_cta(self, flow_name):
        if not flow_name:
            return None
        
        whatsapp_flow = WhatsappFlow.objects.filter(flow_name=flow_name).first()
        if whatsapp_flow:
            return whatsapp_flow
        else:
            return None
    
    @classmethod
    def send_whatsapp_audio(self, phone_no, audio_file_path):
        url = os.getenv("WHATSAPP_API_URL") + '/messages'
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_BEARER_TOKEN')}",
            "Content-Type": "application/json",
        }
        # Upload the audio file to the WhatsApp server and get the media ID
        media_id = self.upload_whatsapp_media_file(audio_file_path)
        if not media_id:
            raise Exception("Failed to upload audio file to WhatsApp server.")

        # Send the audio message using the media ID
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"{phone_no}",
            "type": "audio",
            "audio": {
                "id":f"{media_id}"
            },
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(response.json())
        else:
            print('error in sending audio message.')

    @classmethod
    def upload_whatsapp_media_file(self,file_path):
        access_token = os.getenv('WHATSAPP_BEARER_TOKEN')
        url = os.getenv("WHATSAPP_API_URL") + '/media'
        mime_type = 'audio/mpeg'

        with open(file_path, "rb") as file:
            form_data = MultipartEncoder(
                fields={
                    'file': (os.path.basename(file_path), file, mime_type),
                    'messaging_product': 'whatsapp',
                    'type': mime_type
                }
            )

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': form_data.content_type  # Use the content_type from MultipartEncoder
            }

            response = requests.post(url, headers=headers, data=form_data)

            if response.status_code == 200:
                media_id = response.json().get('id')
                return media_id
            else:
                print(f"Failed to upload media. Status code: {response.status_code}, Response: {response.text}")
                return None
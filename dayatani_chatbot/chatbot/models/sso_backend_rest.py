import requests
from rest_framework import authentication, exceptions
from rest_framework import status
from rest_framework.response import Response
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from chatbot.constants import Constant
from datetime import datetime
import hashlib
import hmac
from django.utils.encoding import force_bytes
from django.urls import resolve
from chatbot.helpers import decrypt_message
UserModel = get_user_model()
import os


class SSOBearerAuthentication(authentication.BaseAuthentication):
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return "Invalid Credentials"
    

    def validate_signature(self, signature_header, data):
        secret = os.getenv("WHATSAPP_SECRET")
        signature = signature_header.split('sha256=')[1]
        payload_body = force_bytes(data)
        expected_signature = hmac.new(
            force_bytes(secret),
            msg=payload_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    
    def authenticate(self, request):
        resolved_url = resolve(request.path)
        view_name = resolved_url.url_name
        sso_token = request.META.get('HTTP_AUTHORIZATION')
        client_api_key = request.headers.get('Api-Key')
        
        if sso_token and client_api_key:
            return None, 401

        if view_name == 'whatsapp-list' and request.method == 'GET':
            return (None, None)
        
        if view_name == 'whatsapp-list' and request.method == 'POST':
            body = request.body
            data = request.data
            sign_status = self.validate_signature(request.headers.get('X-Hub-Signature-256', None), 
                                                    body)
            if not sign_status:
                return (None, None)
            
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                phone_no = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
                user, created = UserModel.objects.get_or_create(mobile_number=phone_no)
                if created:
                    user.set_unusable_password()
                    user.save()
                return (user, None)
            
            if 'statuses' in data['entry'][0]['changes'][0]['value']:
                statuses = data['entry'][0]['changes'][0]['value']['statuses']
                recipient_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['recipient_id']
                user, created = UserModel.objects.get_or_create(mobile_number=recipient_id)
                if created:
                    user.set_unusable_password()
                    user.save()
                return (user, None)
            
        elif sso_token:
            if not sso_token:
                return None, 401
            try:
                SSO_API_URL = os.getenv('SSO_API_URL')
                response = requests.get(SSO_API_URL, headers={
                            'Accept-Language': 'en',
                            'Authorization': sso_token
                        })

                if response.status_code == 200:
                    user_data = (response.json()).get('data')
                    user_data = user_data.get("user")  
                    sso_id = user_data['id']
                    mobile_number = user_data['phone']
                    user, created = UserModel.objects.get_or_create(sso_uid=sso_id, mobile_number=mobile_number)
                    if created:
                        user.set_unusable_password()  # Set an unusable password for SSO users
                        user.name = user_data['name']
                        user.save()
                    if not user.name:
                        user.name = user_data['name']
                        user.save()
                    return (user, None)  # Authentication successful
            except requests.exceptions.RequestException:
                raise exceptions.AuthenticationFailed('SSO authentication failed')
        elif client_api_key:
            try:
                client_user_id = request.headers.get('Client-User-Id')
                if not client_user_id:
                    return None, 401
                CLIENT_SSO_API_URL = os.getenv('CLIENT_SSO_API_URL') 
                response = requests.get(CLIENT_SSO_API_URL, headers={
                            'Accept-Language': 'en',
                            'X-API-KEY': client_api_key
                        })
                
                if response.status_code == 200:
                    user_data = response.json()
                    client_id = user_data['id']
                    chatbot_configurations = json.loads(decrypt_message(user_data['chatbot_configurations']))
                    
                    user, created = UserModel.objects.get_or_create(sso_uid=client_user_id, client_id=client_id)
                    if created:
                        user.set_unusable_password()  # Set an unusable password for SSO users
                        user.save()
                    
                    request.session['openai_api_type'] = chatbot_configurations['openai_api_type']
                    request.session['openai_api_version'] = chatbot_configurations['openai_api_version']
                    request.session['openai_api_base'] = chatbot_configurations['openai_api_base']
                    request.session['openai_api_key'] = chatbot_configurations['openai_api_key']
                    request.session['deployment_name_embedding'] = chatbot_configurations['deployment_name_embedding']
                    request.session['deployment_name_model'] = chatbot_configurations['deployment_name_model']
                    return (user, None)  # Authentication successful
            except requests.exceptions.RequestException:
                raise exceptions.AuthenticationFailed('SSO authentication failed')


        return None # No valid user

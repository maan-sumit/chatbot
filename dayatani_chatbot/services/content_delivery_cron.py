import os
import requests
from dayatani_llm_core.tools.weather import get_weather, get_weather_by_location_name
import json
from chatbot.models import User, Conversation, ConversationDetail, WhatsappCronContent
from datetime import datetime
from chatbot.constants import Constant
from .templates import CONTENT_TEMPLATE
from .constant import ServiceConstant

class ContentCron:
    def __init__(self,connection):
        self.connection = connection
    
    def start_content_cron(self):
        users = self.get_users()
        content = self.get_content()
        if content:
            for user_data in users:
                user_id = user_data[0]
                phone_no = user_data[1]
                unsubscribe_status =  user_data[4]
                if unsubscribe_status != True:
                    content_formatted_message = self.send_message(phone_no, content)
                    self.save_content_messsage_to_db(content_formatted_message,user_id)

    def send_message(self,phone_no, content):
        link_message = f"{content.link}"
        message = f"{content.description}"
        self.send_whatsapp_messsage(phone_no, message, link_message)
        
        formatted_content_message = CONTENT_TEMPLATE.format(link=link_message, description=message)
        data = WhatsappCronContent.objects.filter(id=content.id).first()
        data.is_sent = True
        data.save()
        print('Content:',formatted_content_message)
        return formatted_content_message
    
    def get_language_code_from_phone_no(self, phone_no):
        if phone_no and str(phone_no).startswith("62"):
                return ServiceConstant.INDO_LANGUAGE_CODE
        return ServiceConstant.ENGLISH_LANGUAGE_CODE


    def send_whatsapp_messsage(self, phone_no, message, content_link):
        url = os.getenv("WHATSAPP_API_URL") + '/messages'
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_BEARER_TOKEN')}",
            "Content-Type": "application/json",
        }
        if len(message) > 800:
            message = message[:800]

        data = {
            "recipient_type": "individual",
            "messaging_product": "whatsapp",
            "to": f"{phone_no}",
            "type": "template",
            "template": {
                "name": ServiceConstant.CONTENT_TEMPLATE_NAME,
                "language": {
                    "policy": "deterministic",
                    "code": self.get_language_code_from_phone_no(phone_no)
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": content_link},
                            {"type": "text", "text": message}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                        {
                            "type": "payload",
                            "payload": Constant.CONTENT_UNSUBSCRIBE_PAYLOAD
                        }
                        ]
                    }
                ]
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print('RESPONSE FROM CONTENT MESSAGE:',response.json())   

    def get_content(self):
        data = WhatsappCronContent.objects.filter(is_sent=False).order_by('created_at').first()
        return data

    def get_users(self):
        users_uuids = self.get_user_ids()
        print(users_uuids)
        user_data = self.get_user_data_from_id(users_uuids)
        print(user_data)
        return user_data

    def get_user_data_from_id(self, uuids):
        result = tuple()
        if uuids and len(uuids)>0:
            query = """select u.id , u.mobile_number, cu.latitude, cu.longitude, cu.unsubscribe
            from chatbot_user u 
            left join chatbot_userwhatsappinfo cu
            on u.id = cu.user_id 
            where u.id in %s;
            """
            params = [uuids]
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
        return result
    

    def get_user_ids(self):
        query = """SELECT DISTINCT u.id as user_id
        FROM public.chatbot_user u 
        JOIN public.chatbot_conversation c 
        ON u.id = c.user_id
        where c.whatsapp_chat = True
        AND (u.client_id IS NULL OR u.client_id = %s);
        """

        client_id = os.getenv("DAYATANI_CLIENT_ID", "54f25658-f3d8-414a-9565-6ccad0540242")
        params = [client_id]
        result = None
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()

        ids = [str(res[0]) for res in result] 
        return tuple(ids)
    
    def get_user_from_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def save_content_messsage_to_db(self, message, user_id):
        if message:
            user = self.get_user_from_id(user_id)
            conversation = Conversation.objects.filter(user=user, whatsapp_chat=True).first()
            if not conversation:
                conversation = Conversation.objects.create(user=user, whatsapp_chat=True)
            
            ConversationDetail.objects.create(conversation=conversation, conversations=message, role=Constant.AGENT)
            conversation.conversation_detail_modified_at = datetime.now()
            conversation.heading = message
            conversation.save()

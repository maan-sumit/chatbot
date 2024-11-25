import os
import requests
from dayatani_llm_core.tools.weather import get_weather, get_weather_by_location_name
import json
from chatbot.models import User, Conversation, ConversationDetail
from datetime import datetime
from chatbot.constants import Constant
from itertools import islice
from .constant import ServiceConstant

class WeatherCron:
    def __init__(self,connection):
        self.connection = connection

    def start_weather_cron(self):
        users = self.get_users()
        for user_data in users:
            user_id = user_data[0]
            phone_no = user_data[1]
            latitude = user_data[2]
            longitude = user_data[3]
            unsubscribe_status =  user_data[4]
            if unsubscribe_status != True:
                weather_report = self.send_message(phone_no, latitude, longitude)
                self.save_weather_report_to_db(weather_report,user_id)

    def send_message(self, phone_no, latitude, longitude):
        language_code = self.get_language_code_from_phone_no(phone_no)
        weather_report = ''
        if latitude and longitude:
            weather_data = get_weather(latitude, longitude, language_code)
            weather_report_msg , weather_report_list = self.format_weather_report(weather_data)
            weather_report_list.append(' ')
        else:
            weather_data = get_weather_by_location_name('Garut', language_code)
            weather_report_msg , weather_report_list = self.format_weather_report(weather_data)
            if language_code == 'id':
                weather_report_list.append(Constant.WEATHER_DEFAULT_LOCATION_MSG_INDO)
                weather_report_msg+=Constant.WEATHER_DEFAULT_LOCATION_MSG_INDO
            else:
                weather_report_list.append(Constant.WEATHER_DEFAULT_LOCATION_MSG)
                weather_report_msg+=Constant.WEATHER_DEFAULT_LOCATION_MSG
        
        print(weather_report_list)
        self.send_whatsapp_messsage(phone_no, weather_report_list)
        return weather_report_msg
    
    def get_language_code_from_phone_no(self, phone_no):
        if phone_no and str(phone_no).startswith("62"):
                return ServiceConstant.INDO_LANGUAGE_CODE
        return ServiceConstant.ENGLISH_LANGUAGE_CODE


    def send_whatsapp_messsage(self, phone_no, weather_report_list):
        url = os.getenv("WHATSAPP_API_URL") + '/messages'
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_BEARER_TOKEN')}",
            "Content-Type": "application/json",
        }
        final_message_list = []
        for item in weather_report_list[1:]:
            final_message_list.append({"type": "text", "text": item})

        data = {
            "recipient_type": "individual",
            "messaging_product": "whatsapp",
            "to": f"{phone_no}",
            "type": "template",
            "template": {
                "name": ServiceConstant.WEATHER_TEMPLATE_NAME,
                "language": {
                    "policy": "deterministic",
                    "code": self.get_language_code_from_phone_no(phone_no)
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "text",
                                "text": weather_report_list[0]
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": final_message_list
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                        {
                            "type": "payload",
                            "payload": Constant.WEATHER_UNSUBSCRIBE_PAYLOAD
                        }
                        ]
                    }
                ]
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print('RESPONSE FROM MESSAGE:',response.json())


    def convert_date_format(self, date_str):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d %b %Y')
        return formatted_date
    
    def format_weather_report(self, weather_data):
        weather_data = json.loads(weather_data)
        weather_report_list = []
        
        city_data = weather_data.get('city', {})
        weather = weather_data.get('weather', {})
        city_name = city_data.get('name', 'Unknown city')
        country = city_data.get('country', 'Unknown country')
        formatted_message = [f"*Weather Forecast for {city_name}, {country}:*"]
        weather_report_list.append(f"{city_name}, {country}")

        for date, details in islice(weather.items(),3):
            avg_temp = details.get('avg_temp', 'N/A')
            avg_humidity = details.get('avg_humidity', 'N/A')
            weather_statuses = set()

            for status in details.get('status', []):
                weather_statuses.add(status['status'])

            date = self.convert_date_format(date)
            conditions_summary = ', '.join(sorted(weather_statuses)).lower()
            formatted_message.append(f"\n- *Date: {date}*")
            formatted_message.append(f"  - _Weather Conditions:_ {conditions_summary}")
            formatted_message.append(f"  - _Average Temperature:_ {avg_temp}°C")
            formatted_message.append(f"  - _Humidity:_ {avg_humidity}%")

            weather_report_list.append(date)
            weather_report_list.append(conditions_summary)
            weather_report_list.append(f"{avg_temp}°C")
            weather_report_list.append(f"{avg_humidity}%")

        return "\n".join(formatted_message),weather_report_list
    

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
    
    def save_weather_report_to_db(self, message, user_id):
        if message:
            user = self.get_user_from_id(user_id)
            conversation = Conversation.objects.filter(user=user, whatsapp_chat=True).first()
            if not conversation:
                conversation = Conversation.objects.create(user=user, whatsapp_chat=True)
            
            ConversationDetail.objects.create(conversation=conversation, conversations=message, role=Constant.AGENT)
            conversation.conversation_detail_modified_at = datetime.now()
            conversation.heading = message
            conversation.save()
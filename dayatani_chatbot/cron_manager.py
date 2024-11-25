import os
import dotenv
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dayatani_chatbot.settings")
dotenv.load_dotenv()

import django
from django.db import connection
django.setup()

from services.weather_update_cron import WeatherCron
from services.content_delivery_cron import ContentCron
import sys

if __name__ == "__main__":
    script_name = None
    if len(sys.argv) > 1:
        script_name = sys.argv[1]  
    
    if script_name == 'WEATHER':
        weather_cron = WeatherCron(connection)
        weather_cron.start_weather_cron()
    elif script_name == 'CONTENT':
        content_cron = ContentCron(connection)
        content_cron.start_content_cron()
    else:
        print('Pass valid script name parameter.')

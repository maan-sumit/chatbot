import os
from dotenv import load_dotenv
load_dotenv()

class ServiceConstant:
    WEATHER_TEMPLATE_NAME = os.getenv('WEATHER_TEMPLATE_NAME')
    CONTENT_TEMPLATE_NAME = os.getenv('CONTENT_TEMPLATE_NAME')
    INDO_LANGUAGE_CODE = 'id'
    ENGLISH_LANGUAGE_CODE = 'en'
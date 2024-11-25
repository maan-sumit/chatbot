import os
from dotenv import load_dotenv
load_dotenv()

class Constant:
    USER = 'user'
    AGENT = 'agent'
    CONTAINER_NAME = os.getenv('CONTAINER_NAME')
    FILES_TRAINING_URL = os.getenv('FILES_TRAINING_URL')
    FILES_TRAINING_ABORT_URL = os.getenv('FILES_TRAINING_ABORT_URL')
    AZURE_FILES_FOLDER_NAME = os.getenv('AZURE_FILES_FOLDER_NAME')
    TRAINED_MODEL = 'Trained Model'
    UPLOAD_FILE = 'Uploaded file'
    DELETE_FILE = 'Deleted file'
    ABORT_TRAINING = 'Abort training'
    WHATSAPP_UNSUPPORTED_FORMAT_MSG = "Sorry, I only understand text messages at this moment."
    WHATSAPP_AUDIO_ERROR = "Sorry, I am not able to parse this audio messsage. Can you ask the question again."
    TEMP_DIR = 'temp'
    WHATSAPP_IMAGE_ERROR = 'Sorry, I am not able to parse this image. Can you please ask the question again.'
    WHATSAPP_UNSUBSCRIBE_NOTIFICATION_MSG='You are successfully unsubscribed from the weekly updates.'
    WEATHER_UNSUBSCRIBE_PAYLOAD = 'WEATHER_UNSUBSCRIBE'
    CONTENT_UNSUBSCRIBE_PAYLOAD = 'CONTENT_UNSUBSCRIBE'
    WEATHER_DEFAULT_LOCATION_MSG = 'This report uses default location Garut. Please share your location to receive accurate weather report.'
    WEATHER_DEFAULT_LOCATION_MSG_INDO = 'Laporan ini menggunakan lokasi default Garut. Silakan bagikan lokasi Anda untuk menerima laporan cuaca yang akurat.'



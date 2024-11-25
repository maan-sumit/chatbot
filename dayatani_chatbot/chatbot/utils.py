import threading
from threading import Thread
from dayatani_llm_core.dayatani_llm_core import DayatanLLMCore
from dayatani_llm_core.constant import USER_INFO_NOT_FOUND_MSG
import queue
from chatbot.models import ConversationDetail, FileTrainingStatus, FileBatch, Logs
from chatbot.constants import Constant
from datetime import datetime
import os
import json
import time
from azure.storage.blob import BlobServiceClient, ContainerClient
import os,urllib

class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)
       
class CustomThread(Thread):
    def __init__(self, client_id, open_ai_dict, question, chat_history, user_info):
        Thread.__init__(self)
        self.value = None
        self.client_id = client_id
        self.open_ai_dict = open_ai_dict
        self.question = question
        self.chat_history = chat_history
        self.user_info = user_info


    def run(self):
        llm_service = DayatanLLMCore(client_id=self.client_id, open_ai_dict=self.open_ai_dict, user_info=self.user_info)
        threaded_generator = ThreadedGenerator()
        res = llm_service.get_response(threaded_generator, self.question, self.chat_history)
        self.value = res


def invoke_llm_service(conversation_detail:object, chat_history: list, request:object):
    client_id = []
    open_ai_dict = {
        'openai_api_type': request.session.get('openai_api_type', os.getenv('OPENAI_API_TYPE')),
        'openai_api_version': request.session.get('openai_api_version', os.getenv('OPENAI_API_VERSION')),
        'openai_api_base': request.session.get('openai_api_base', os.getenv('OPENAI_API_BASE')),
        'openai_api_key': request.session.get('openai_api_key', os.getenv('OPENAI_API_KEY')),
        'deployment_name_embedding': request.session.get('deployment_name_embedding', os.getenv('DEPLOYMENT_NAME_EMBEDDING')),
        'deployment_name_model': request.session.get('deployment_name_model', os.getenv('DEPLOYMENT_NAME_MODEL'))
    }

    # open_ai_dict = {
    #             'openai_api_type': os.getenv('OPENAI_API_TYPE'),
    #             'openai_api_version': os.getenv('OPENAI_API_VERSION'),
    #             'openai_api_base': os.getenv('OPENAI_API_BASE'),
    #             'openai_api_key': os.getenv('OPENAI_API_KEY'),
    #             'deployment_name_embedding': os.getenv('DEPLOYMENT_NAME_EMBEDDING'),
    #             'deployment_name_model': os.getenv('DEPLOYMENT_NAME_MODEL')
    #         }
    
    client_id.append(str(request.user.client_id)) if request.user.client_id else client_id.append(os.getenv('DAYATANI_CLIENT_ID'))
    print("client_id", client_id)

    llm_service = DayatanLLMCore(client_id, open_ai_dict)
    threaded_generator = ThreadedGenerator()
    threading.Thread(target=llm_service.get_response, args=(
        threaded_generator, conversation_detail.conversations, chat_history)).start()
    res = []
    for token in threaded_generator:
        res.append(token)
        yield token

    conversation = conversation_detail.conversation
    data = ''.join(res)
    conversation.answer = data
    conversation.save()
    
    chat = ConversationDetail.objects.create(conversation=conversation, conversations=data, role=Constant.AGENT)
    conversation.conversation_detail_modified_at = datetime.now()
    conversation.save()
    yield {"conversation_detail_id": chat.id, "conversation_id": conversation.id}

def invoke_llm_service_whatsapp(question, chat_history: list, conversation:object, request:object, user_info:dict):
    client_id  = []
    open_ai_dict = request['open_ai_dict']
    user = request['user']

    client_id.append(str(user['client_id'])) if user['client_id'] else client_id.append(os.getenv('DAYATANI_CLIENT_ID'))
    t = CustomThread(client_id=client_id,
                     open_ai_dict=open_ai_dict,
                     question=question,
                     chat_history=chat_history,
                     user_info=user_info)

    t.start()
    t.join()
    data = t.value
    answer = data['output']

    conversation.answer = answer
    conversation.save()

    ConversationDetail.objects.create(conversation=conversation, conversations=answer, role=Constant.AGENT)
    conversation.conversation_detail_modified_at = datetime.now()
    conversation.save()
    flow = process_input_data(data=data)
    print(chat_history)
    if flow == None and len(chat_history) <= 1:
        flow = 'signup'
    print('flow',flow)
    return answer,flow

def process_input_data(data):
    for log, output in data['intermediate_steps']:
        if log.tool == 'USER_INFORMATION_SEARCH':
            category = log.tool_input.get('category')
            if output and output == USER_INFO_NOT_FOUND_MSG:
                print(f"Tool: USER_INFORMATION_SEARCH, Category: {category}, Output: {output}")
                return category
            else:
                print("Tool was USER_INFORMATION_SEARCH.")
                return None
    print("No USER_INFORMATION_SEARCH tool found.")
    return None

def log_user_activity(user, activity, file_url=None):
    log = Logs.objects.create(user=user, activity=activity)
    if file_url:
        log.file_url = file_url
        log.save()


def convert_str_to_datetime(date:str):
    datetime_obj = datetime.strptime(date, "%Y-%m-%d")
    return datetime_obj


def invoke_llm_service_healthcheck(data:str, chat_history: list):
    llm_service = DayatanLLMCore()
    threaded_generator = ThreadedGenerator()
    threading.Thread(target=llm_service.get_response, args=(
        threaded_generator, data, chat_history)).start()
    
    for token in threaded_generator:
        yield token


def remove_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)



def invoke_llm_service_client(conversation_detail:object, chat_history: list, request:object):
    client_id = []
    open_ai_dict = {
        'openai_api_type': request.session.get('openai_api_type', os.getenv('OPENAI_API_TYPE')),
        'openai_api_version': request.session.get('openai_api_version', os.getenv('OPENAI_API_VERSION')),
        'openai_api_base': request.session.get('openai_api_base', os.getenv('OPENAI_API_BASE')),
        'openai_api_key': request.session.get('openai_api_key', os.getenv('OPENAI_API_KEY')),
        'deployment_name_embedding': request.session.get('deployment_name_embedding', os.getenv('DEPLOYMENT_NAME_EMBEDDING')),
        'deployment_name_model': request.session.get('deployment_name_model', os.getenv('DEPLOYMENT_NAME_MODEL'))
    }

    # open_ai_dict = {
    #             'openai_api_type': os.getenv('OPENAI_API_TYPE'),
    #             'openai_api_version': os.getenv('OPENAI_API_VERSION'),
    #             'openai_api_base': os.getenv('OPENAI_API_BASE'),
    #             'openai_api_key': os.getenv('OPENAI_API_KEY'),
    #             'deployment_name_embedding': os.getenv('DEPLOYMENT_NAME_EMBEDDING'),
    #             'deployment_name_model': os.getenv('DEPLOYMENT_NAME_MODEL')
    #         }
    
    client_id.append(str(request.user.client_id)) if request.user.client_id else client_id.append(os.getenv('DAYATANI_CLIENT_ID'))

    llm_service = DayatanLLMCore(client_id, open_ai_dict)
    threaded_generator = ThreadedGenerator()
    threading.Thread(target=llm_service.get_response, args=(
        threaded_generator, conversation_detail.conversations, chat_history)).start()
    res = []
    res_str = ""
   
    for token in threaded_generator:
        res.append(token)
        print("token", token)
        if not "\n" in token:
            res_str+=token
        else:
            yield "{\"message\": \"" + res_str + "\"}\n"
            res_str = ""

    conversation = conversation_detail.conversation
    data = ''.join(res)
    conversation.answer = data
    conversation.save()
    
    chat = ConversationDetail.objects.create(conversation=conversation, conversations=data, role=Constant.AGENT)
    conversation.conversation_detail_modified_at = datetime.now()
    conversation.save()
    yield "{\"conversation_detail_id\": \"" + str(chat.id) + "\", \"conversation_id\": \"" + str(conversation.id) + "\", \"message\": \"" + res_str + "\"}\n"
    res_str = ""


def get_client():
    parsed_url = urllib.parse.urlparse(os.environ['VISION_BLOB_SAS_URL'])
    CONTAINER_NAME = parsed_url.path.strip('/')
    account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    credential = parsed_url.query
    blob_service_client = BlobServiceClient(
        account_url=account_url, credential=credential)
    container_client = blob_service_client.get_container_client(
        CONTAINER_NAME)
    return blob_service_client, container_client
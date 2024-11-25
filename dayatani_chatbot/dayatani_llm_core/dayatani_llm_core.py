import os
from .my_custom_handler import MyCustomHandler
from .templates import TEMPLATE_SYSTEM, USER_INFO_TEMPLATE
from langchain.prompts.chat import (
    SystemMessagePromptTemplate as SystemTemplate,
    HumanMessagePromptTemplate as HumanTemplate,
)
from langchain.chat_models import AzureChatOpenAI
import logging
from langchain.memory import ChatMessageHistory

# importing all the tools
from dayatani_llm_core.tools.vector_db import get_vector_db_search_tool
from dayatani_llm_core.tools.weather import (
    weather_search_by_lat_lon_tool,
    weather_search_by_place_tool,
)
from dayatani_llm_core.tools.other import (
    get_calculator_tool,
    get_internet_search_tool,
)
from dayatani_llm_core.tools.user_info import get_user_info_tool
from dayatani_llm_core.tools.vision import get_vision_tool

from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.embeddings.openai import OpenAIEmbeddings

logging.basicConfig(
    format="LLM-CORE-%(asctime)s-%(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%I:%M:%S",
)
logger = logging.getLogger("LLM-CORE")

class DayatanLLMCore:
    def __init__(self, client_id, open_ai_dict, user_info={}) -> None:
        self.client_id = client_id
        self.user_info = user_info
        self.DEPLOYMENT_NAME_MODEL = open_ai_dict['deployment_name_model']
        self.DEPLOYMENT_NAME_EMBEDDING = open_ai_dict['deployment_name_embedding']
        self.OPENAI_API_TYPE = open_ai_dict['openai_api_type']
        self.OPENAI_API_VERSION = open_ai_dict['openai_api_version']
        self.OPENAI_API_BASE = open_ai_dict['openai_api_base']
        self.OPENAI_API_KEY = open_ai_dict['openai_api_key']
        self.llm = self.get_llm()
        self.embedding = self.get_embedding()

    def get_response(self, threaded_generator, question, chat_history=[]):
        try:
            history = self.__create_chat_history(chat_history)
            streaming_llm = self.__get_streaming_llm(threaded_generator)

            # Generate the system message, including formatted user_info
            system_message_template = SystemTemplate.from_template(TEMPLATE_SYSTEM)
            system_message = system_message_template.format(user_info=self.get_user_info_template_string())

            agent_kwargs = {
                "system_message": system_message,
                "extra_prompt_messages": history.messages,
            }

            tools = self.get_tool_list()
            agent = initialize_agent(
                tools,
                streaming_llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                agent_kwargs=agent_kwargs,
                return_intermediate_steps=True
            )

            res = agent({"input": question})
            logger.info(res)
            return res

        except Exception as e:
            logging.error(e, exc_info=True)
            threaded_generator.send('Sorry, I am unable to answer this question.')
            res = {
                'input': question,
                'output': "Sorry, I am unable to answer this question.",
                'intermediate_steps': []
            }
            return res
        finally:
            threaded_generator.close()

    def get_tool_list(self) -> list:
        internet_search_tool = get_internet_search_tool()
        calculator_tool = get_calculator_tool(llm=self.llm)
        vector_db_search_tool = get_vector_db_search_tool(self.embedding,self.client_id)
        user_info_tool = get_user_info_tool(self.user_info)
        vision_tool = get_vision_tool()

        return [
            vector_db_search_tool,
            weather_search_by_lat_lon_tool,
            weather_search_by_place_tool,
            calculator_tool,
            internet_search_tool,
            user_info_tool,
            vision_tool
        ]

    def __create_chat_history(self, chat_history=[]) -> ChatMessageHistory:
        if chat_history == None:
            chat_history = []

        history = ChatMessageHistory()
        for chat in chat_history:
            if chat["role"] == "user":
                history.add_user_message(chat["conversations"])
            elif chat["role"] == "agent":
                history.add_ai_message(chat["conversations"])

        return history

    def __get_streaming_llm(self, threaded_generator):
        custom_handler = MyCustomHandler(threaded_generator)
        streaming_llm = AzureChatOpenAI(
            temperature=0.5,
            streaming=True,
            callbacks=[custom_handler],
            cache=False,
            deployment_name = self.DEPLOYMENT_NAME_MODEL,
            openai_api_type= self.OPENAI_API_TYPE,
            openai_api_version= self.OPENAI_API_VERSION,
            openai_api_base= self.OPENAI_API_BASE,
            openai_api_key= self.OPENAI_API_KEY 
        )
        return streaming_llm
    
    def get_llm(self):
        llm = AzureChatOpenAI(
                temperature=0,
                cache=False, 
                verbose=False,
                deployment_name = self.DEPLOYMENT_NAME_MODEL,
                openai_api_type= self.OPENAI_API_TYPE,
                openai_api_version= self.OPENAI_API_VERSION,
                openai_api_base= self.OPENAI_API_BASE,
                openai_api_key= self.OPENAI_API_KEY )
        return llm

    def get_embedding(self):
        embeddings = OpenAIEmbeddings(
                        chunk_size = 16,    
                        deployment = self.DEPLOYMENT_NAME_EMBEDDING,
                        openai_api_type= self.OPENAI_API_TYPE,
                        openai_api_version= self.OPENAI_API_VERSION,
                        openai_api_base= self.OPENAI_API_BASE,
                        openai_api_key= self.OPENAI_API_KEY)
        return embeddings
    
    def get_user_info_template_string(self):
        if len(self.user_info) > 0:
            msg = USER_INFO_TEMPLATE.format(name = self.user_info.get('name','_unknown_'),
                          profession = self.user_info.get('profession','_unknown_'),
                          location = self.user_info.get('location','_unknown_'),
                          land_size = self.user_info.get('land_size','_unknown_'),
                          crop_growing = self.user_info.get('crop_growing','_unknown_'),
                          soil_type = self.user_info.get('soil_type','_unknown_')
                          )
            return msg
        else:
            return " "


from langchain.agents import Tool
from pydantic import BaseModel, Field
import os
from dayatani_llm_core.constant import VISION_DESC
import base64, requests
import urllib
from azure.storage.blob import BlobServiceClient, ContainerClient
from dayatani_llm_core.util import get_client

blob_service_client, container_client = get_client()


def download_file(file_name, download_dir_path="temp") -> dict:
    os.makedirs(download_dir_path, exist_ok=True)
    download_file_path = os.path.join(download_dir_path, os.path.basename(file_name))

    with open(download_file_path, "wb") as download_file:
        download_file.write(container_client.download_blob(file_name).readall())
    return download_file_path


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def remove_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


class VisionInput(BaseModel):
    image_id_and_query: list = Field(
        description="python list with 0th element as \
                                     id of an image that user sent along with exetension.\
                                     1st element will be fully formed question. In case no question is asked by user, just pass 'what's in this image?"
    )
    # query: str = Field(description="should be a fully formed question. In case no question is asked by user, just pass 'what's in this image?'")


def call_gpt_4_vision(image_id_and_query: list) -> str:
    try:
        image_id = image_id_and_query[0]
        query = image_id_and_query[1]
        file_path = download_file(image_id)
        print(file_path)
        base64_image = encode_image(file_path)

        url = f"{os.environ['OPENAI_API_BASE']}openai/deployments/{os.environ['DEPLOYMENT_NAME_VISION']}/chat/completions?api-version={os.environ['OPENAI_API_VERSION']}"
        headers = {
            "Content-Type": "application/json",
            "api-key": f"{os.environ['OPENAI_API_KEY']}",
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=payload)
        answer = response.json()["choices"][0]["message"]["content"]
        print(answer)
        remove_file(file_path)
        return answer
    except Exception as e:
        print(e)
        return "Not able to parse image."


def get_vision_tool():
    vision_tool = Tool(
        name="Agriculture_Image_Search",
        func=call_gpt_4_vision,
        description=f"""{VISION_DESC}""",
        args_schema=VisionInput,
    )

    return vision_tool

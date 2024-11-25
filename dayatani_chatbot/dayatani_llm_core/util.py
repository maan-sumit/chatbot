from azure.storage.blob import BlobServiceClient, ContainerClient
import os,urllib

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
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()
connection_string = os.getenv("AZURE_STORAGE_CONN_STRING")

service = BlobServiceClient.from_connection_string(conn_str=connection_string)
episodes_client = service.get_container_client("episodes")
episodes = episodes_client.list_blob_names()
episode_blob_client = episodes_client.get_blob_client(min(episodes))
with open("episode-01.mp3", "wb") as download_file:
    download_file.write(episode_blob_client.download_blob().readall())

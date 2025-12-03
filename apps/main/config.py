import os
from dotenv import load_dotenv

load_dotenv('/home/cosai/Nive/Cloud_movable/.env')

GMAIL_HOST = os.environ.get("GMAIL_HOST")
FROM_GMAIL = os.environ.get("FROM_GMAIL")
FROM_GMAIL_PASSWORD = os.environ.get("FROM_GMAIL_PASSWORD")
GMAIL_PORT = os.environ.get("GMAIL_PORT", 465)
HOSTDB_URL = os.environ.get("HOSTDB_URL")
SESSION_EXPIRE_MINUTES = 60
media_base_path = os.environ.get("media_path", "/app")
AUDIT_DATE_FILTER= os.environ.get("AUDIT_DATEFILTER")
temp_dir=os.environ.get("temp_dir")
deep_config_file=os.environ.get("config_file")
deep_file=os.environ.get("configs")
folder=os.environ.get("folder")

BACKUP_DELETION = False



# BASE_UPLOAD_DIRECTORY = "/root/Movable/kishore/Cloud_movable/files/cloud_video/"
BASE_UPLOAD_DIRECTORY = "/root/Documents/cloud_movable_update/Cloud_movable/files/cloud_video/"
WEBSOCKET_CLOUD_URL ="sesha.cosai.in"
WEBSOCKET_CLOUD_PREVIEW ="sesha.cosai.in"

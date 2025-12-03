# # from apps.main.database.mongodb import db
# # from apps.main.models.user_model import *
# import requests
# from apps.main.database.db import *
# from apps.main.models.model import * 

# db=next(get_db())
# kit_collection = db["kit_info"]
# kit_details = kit_collection.find_one({"user_id":1})
# users_collection = db["users"]
# users_details = users_collection.find_one({"user_id":1})


# def get_access_headers(serveraccess_token):
#     headers = { 'Authorization': f'Bearer {serveraccess_token}' }
#     return headers


# if kit_details is not None: 
    
#     ############ CPU TEMPERATURE ALERT   ##########
#     CPU_LOW_PRIORITY_1= kit_details.get("cpu_low_priority_1")
#     CPU_LOW_PRIORITY_2 = kit_details.get("cpu_low_priority_2")
#     CPU_MEDIUM_PRIORITY_1= kit_details.get("cpu_medium_priority_1")
#     CPU_MEDIUM_PRIORITY_2 = kit_details.get("cpu_medium_priority_2")

#     ############ DISK USED PERCENTAGE ALERT   ##########
#     DISK_LOW_PRIORITY= kit_details.get("disk_low_priority")
#     DISK_MEDIUM_PRIORITY = kit_details.get("disk_medium_priority")

#     ############# STREAM VALIDITY TIME (MINUTES) ############
#     STREAM_VALIDITY_TIME = kit_details.get("stream_validity_time")

#     ########### CAMERA SETTING ##########################
#     ALLOWED_RESOLUTIONS = kit_details.get("allowed_resolution")
#     ALLOWED_FPS= kit_details.get("allowed_fps")
    
                        



# EXTERNAL_URL =  'http://157.173.221.23:8000'
# EXTERNAL_EMAIL = 'admin@gmail.com'
# EXTERNAL_PASSWORD =  'admin@123'
# SERVER_UPLOAD_URL = 'http://10.0.0.2:8015'
# TS_FRAGMENTS = 5  # in seconds

# BULK_UPLOAD = 'http://157.173.221.23:80'


# def update_access_token():
#     try:        
#         request_url = f"{EXTERNAL_URL}/accounts/token/"
#         data = {'email': EXTERNAL_EMAIL ,'password': EXTERNAL_PASSWORD}
#         response = requests.post(request_url, data=data)
#         if response.status_code == 201:
#             response_json = response.json()  
#             access_token = response_json.get('accessToken')              
#             if access_token:
#                 print("Access token obtained successfully:",access_token)
#                 users_collection.update_one( {"user_id": 1},{"$set": {"serveraccess_token": access_token}})
#             else:
#                 print("Access token not found in response.")
#         else:
#             print("Failed to obtain token. Status code:", response.status_code)
#             print("Response content:", response.text)            
#     except Exception as e:
#         print("Something Issue on Occur",e)
#         pass
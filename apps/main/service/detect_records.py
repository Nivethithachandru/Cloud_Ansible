from aiocron import crontab
from apps.main.database.mongodb import db, det_rec1,det_rec2
from apps.main.models.user_model import *
from apps.main.service.setting import *
import requests
import os
import json
import cv2
import base64
from fastapi import FastAPI ,HTTPException ,BackgroundTasks ,APIRouter,Form,Query
from fastapi_utilities import repeat_every
from datetime import datetime,timedelta
from apps.main.models.get_details import Get_cameras
from apps.main.service.setting import get_access_headers
from main import HLS_FOLDER,static_folder_path
from apps.main.routers.time_incident import detectionrecords_before_after_seconds,tsrecords_before_after_seconds,run_video_merging_in_thread,file_uploading
import threading
from pymongo import ASCENDING



camera = Get_cameras()


plate_path = os.path.join(static_folder_path, 'number_plate.jpg')
detection_collection = db['detection_records_demo']
camera_collection = db["camera_info"]

det1 = det_rec1['detection_records']
det2 = det_rec2['detection_records']


ondemand_data_list = [] 

BULK_URL = f"{EXTERNAL_URL}/detect/vehicle/"

users_collection = db["users"]
users_details = users_collection.find_one({"user_id":1})

detection_reference =db["detection_reference"]

kit_collection = db["kit_info"]
users_details = kit_collection.find_one({"user_id":1})
print(users_details)


if users_details is not None:
    getserverid = users_details.get('kit_serverid')
else:
    getserverid = 1

router=APIRouter()


if users_details is not  None:
    serveraccess_token= users_details.get("serveraccess_token")
    serveraccess_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkZW50aWZpZXIiOiJhZG1pbkBnbWFpbC5jb20iLCJleHAiOjE3NTI1NTcyNDEsImlhdCI6MTcxNjU1NzI0MS44NDc5MywiZW1haWwiOiJhZG1pbkBnbWFpbC5jb20ifQ.nJYRSF_81plpbM1bLwhieoL-gYH3Yy5nCOqHmkgK3Hg'
    headers = get_access_headers(serveraccess_token)



# @router.on_event('startup')
# @repeat_every(seconds=60)
# async def cron_job():
#     # await records_update()
#     await automate_timeincident_upload(2)

# @router.on_event('startup')
# @repeat_every(seconds=60)
# async def cron_job():
#     pass
#     # await records_update()
#     # await records_update1()



async def records_update():
    with open(plate_path, "rb") as f:
        image_data = f.read()
        base64_encoded_image = base64.b64encode(image_data).decode("utf-8")
    serveraccess_token= users_details.get("serveraccess_token")

    datection_data_list = []

    first_record = det1.find_one({"status": False}, sort=[("date_time", 1)]) 

    if first_record:
        first_record_datetime = first_record["date_time"]
        rounded_first_record_datetime = first_record_datetime.replace(second=0, microsecond=0)
        adjusted_datetime = rounded_first_record_datetime + timedelta(seconds=60)
        print("firstdata",first_record_datetime)
        print("start_time",rounded_first_record_datetime)
        print("end_time",adjusted_datetime)

    detection_records = list(det1.find({
        "date_time": {
            "$gte": rounded_first_record_datetime, 
            "$lte": adjusted_datetime 
        },
        "status": False
    }))


    if not detection_records:        
        print("ANALYTICS OFFLINE")
    else:
        for record in detection_records:   

            record_edit = {
                'object_id' : str(record.get('_id')),
                'camera' : record.get('camera_id'),
                'vehicle_id' : record.get('vehicle_id'),
                'vehicle_class_id' : record.get('vehicle_class_id'),
                'vehicle_class_name' : record.get('vehicle_class_name'),
                'direction' : record.get('direction'),
                'plate_number' : record.get('plate_number'),
                'speed' : record.get('speed'),
                'status' : record.get('status'),
                'date_time' : str(record.get('date_time')),
                'image_file' : record.get('image'),
                'plate_image_file' : base64_encoded_image
            }

            datection_data_list.append(record_edit)


        det1.update_many(
            {"_id": {"$in": [record["_id"] for record in detection_records]}},
            {"$set": {"status": True}}
        )

        # update_detectrecors = {
        #     'kit_serverid' : getserverid,
        #     'start_time' : rounded_first_record_datetime,
        #     'end_time' : adjusted_datetime,
        #     'data' : datection_data_list
        # }
       
        response = requests.post(BULK_URL, data=json.dumps(datection_data_list),headers=headers) 
        if response.status_code == 201:
            det1.update_many(
                {"_id": {"$in": [record["_id"] for record in detection_records]}},
                {"$set": {"status": True}}
            )
            print("kit analytics bulk data successfully to server",rounded_first_record_datetime,'TO',adjusted_datetime)
            return {"status" :"post method successfully","data":datection_data_list}

        elif response.status_code == 400:
            print("nn",response.text)
        else:
            print(response.status_code)
            return {"status" :"post method failed","data":datection_data_list}




async def automate_timeincident_upload(vehicle_class_id):

    first_record = det1.find_one({'time_incident': False,'vehicle_class_id': vehicle_class_id}, sort=[("date_time", ASCENDING)]) 
    if first_record:
        first_record_datetime = first_record["date_time"]
        rounded_first_record_datetime = first_record_datetime.replace(second=0, microsecond=0)
        adjusted_datetime = rounded_first_record_datetime + timedelta(seconds=60)
        print("$$$$$$$444",first_record_datetime)
        print("start_time",rounded_first_record_datetime)
        print("end_time",adjusted_datetime)

        detection_records = list(det1.find({
            "date_time": {
                "$gte": rounded_first_record_datetime, 
                "$lte": adjusted_datetime 
            },
            'vehicle_class_id': vehicle_class_id,
            'time_incident' : False
        }))
        print("notdetection_records")

        if not detection_records:
            server_vehicle_id = first_record["server_vehicle_id"]

            update_result = det1.update_one(
                {"server_vehicle_id": server_vehicle_id},
                {"$set": {"time_incident": True}}
            )
            

        for record in detection_records:   
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            if record:
                incident_datetime_ISO = record.get('date_time') 
                camera_id = record.get('camera_id') 
                server_vehicle_id = record.get('server_vehicle_id')

                print("*******************Server Vehicle id is",server_vehicle_id,camera_id)

                print('Requested Time:',incident_datetime_ISO)
                
                if isinstance(incident_datetime_ISO, datetime):
                    collection_incident_data = await detectionrecords_before_after_seconds(incident_datetime_ISO,camera_id)
                    # print("Fetched incident data:", json.dumps(collection_incident_data, indent=4, default=str))
                else:
                    print("Incident datetime is not a datetime object:", incident_datetime_ISO)
                
                ts_record_filter_data = await tsrecords_before_after_seconds(incident_datetime_ISO,camera_id)        
                print("ts_record_filter_data ############:", json.dumps(ts_record_filter_data, indent=4, default=str))
                if not ts_record_filter_data:          
                    thread = threading.Thread(target=file_uploading, args=(collection_incident_data, '',server_vehicle_id))
                    thread.start()
                    thread.join()

                else:
                    print("Video merging . . .")
                    merged_output_file_path = await run_video_merging_in_thread(camera_id, ts_record_filter_data,server_vehicle_id)
                    print("video merged successfuly",merged_output_file_path)
                    if merged_output_file_path:
                        thread = threading.Thread(target=file_uploading, args=(collection_incident_data, merged_output_file_path,server_vehicle_id))
                        thread.start()
                        thread.join()



    find_query = {'vehicle_class_id': vehicle_class_id , 'time_incident' : False}

    # cursor = det2.find(find_query)
    # list_filter_data = [document for document in cursor]

    # if list_filter_data:
    #     first_list_data = list_filter_data[0]
    #     incident_datetime_ISO = first_list_data.get('date_time') 
    #     camera_id = first_list_data.get('camera_id') 
    #     server_vehicle_id = first_list_data.get('server_vehicle_id')

    #     print("*******************Server Vehicle id is",server_vehicle_id)

    #     print('Requested Time:',incident_datetime_ISO)
        
    #     if isinstance(incident_datetime_ISO, datetime):
    #         collection_incident_data = await detectionrecords_before_after_seconds(incident_datetime_ISO,camera_id)
    #         # print("Fetched incident data:", json.dumps(collection_incident_data, indent=4, default=str))
    #     else:
    #         print("Incident datetime is not a datetime object:", incident_datetime_ISO)
        
    #     ts_record_filter_data = await tsrecords_before_after_seconds(incident_datetime_ISO,camera_id)        
    #     print("ts_record_filter_data :", json.dumps(ts_record_filter_data, indent=4, default=str))

    #     if ts_record_filter_data:          
    #         print("Video merging . . .")
    #         merged_output_file_path = await run_video_merging_in_thread(camera_id, ts_record_filter_data)
    #         print("video merged successfuly",merged_output_file_path)
    #         if merged_output_file_path:
    #             thread = threading.Thread(target=file_uploading, args=(collection_incident_data, merged_output_file_path,server_vehicle_id))
    #             thread.start()
    #             thread.join()



# async def records_update1():
#     with open(plate_path, "rb") as f:
#         image_data = f.read()
#         base64_encoded_image = base64.b64encode(image_data).decode("utf-8")
#     serveraccess_token= users_details.get("serveraccess_token")
#     datection_data_list1 = []

#     second_record = det2.find_one({"status": False}, sort=[("date_time", 1)])
#     print("second_camera")


#     if second_record:
#         first_record_datetime = second_record["date_time"]
#         rounded_first_record_datetime = first_record_datetime.replace(second=0, microsecond=0)
#         adjusted_datetime = rounded_first_record_datetime + timedelta(seconds=60)
#         print("firstdata",first_record_datetime)
#         print("start_time",rounded_first_record_datetime)
#         print("end_time",adjusted_datetime)

#     detection_records1 = list(det2.find({
#         "date_time": {
#             "$gte": rounded_first_record_datetime, 
#             "$lte": adjusted_datetime 
#         },
#         "status": False
#     }))


#     if not detection_records1:        
#         print("ANALYTICS OFFLINE")
#     else:
#         for record in detection_records1:   

#             record_edit1 = {
#                 'object_id' : str(record.get('_id')),
#                 'camera' : record.get('camera_id'),
#                 'vehicle_id' : record.get('vehicle_id'),
#                 'vehicle_class_id' : record.get('vehicle_class_id'),
#                 'vehicle_class_name' : record.get('vehicle_class_name'),
#                 'direction' : record.get('direction'),
#                 'plate_number' : record.get('plate_number'),
#                 'speed' : record.get('speed'),
#                 'status' : record.get('status'),
#                 'date_time' : str(record.get('date_time')),
#                 'image_file' : record.get('image'),
#                 'plate_image_file' : record.get('plate_img')
#             }

#             datection_data_list1.append(record_edit1)

#         # det2.update_many(
#         #     {"_id": {"$in": [record["_id"] for record in detection_records1]}},
#         #     {"$set": {"status": True}}
#         # )

#         # update_detectrecors = {
#         #     'kit_serverid' : getserverid,
#         #     'start_time' : rounded_first_record_datetime,
#         #     'end_time' : adjusted_datetime,
#         #     'data' : datection_data_list
#         # }
       
#         response1 = requests.post(BULK_URL, data=json.dumps(datection_data_list1),headers=headers) 

#         if response1.status_code == 201:

#             det2.update_many(
#                 {"_id": {"$in": [record["_id"] for record in detection_records1]}},
#                 {"$set": {"status": True}}
#             )
#             print("kit analytics bulk data successfully to server",rounded_first_record_datetime,'TO',adjusted_datetime)
#             return {"status" :"post method successfully","data":datection_data_list1}

#         elif response1.status_code == 400:
#             print("nn",response1.text)
#         else:
#             print(response1.status_code)
#             return {"status" :"post method failed","data":datection_data_list1}
        
  




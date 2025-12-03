from aiocron import crontab
from apps.main.database.mongodb import db
from main import HLS_FOLDER
from apps.main.service.setting import *
import requests
import os
from apps.main.service.setting import get_access_headers

ondemand_collection = db['ondemand_video']
ondemandReference_collection =db["ondemand_reference"]
users_collection = db["users"]

ondemand_data_list = [] 
ondemand_recordidlist = []

users_details = users_collection.find_one({"user_id":1})

ping_url = f"http://10.0.0.28:8005/system/videosource/"


if users_details is not  None:
    serveraccess_token= users_details.get("serveraccess_token")
    headers = get_access_headers(serveraccess_token)


async def cron_upfiles():
    print("(***************)")
    await total_upfileslist()
    await upload_record()
    print("(***************)")


@crontab('*/5 * * * *')
async def cron_job():
    await cron_upfiles()

###################################################################################
record_id_list = []
only_uploaded_list = []

async def total_upfileslist():
    
    ondemand_data = list(ondemand_collection.find()) 
    if not ondemand_data:        
        print("No On-Demand_data found (failed status)")
    else:
        for ondemand_data in ondemand_data:              
            record_id_list.append(int(ondemand_data['record_id']))

async def upload_record():
    failed_pathlist = []
    
    for record_id in record_id_list:
        ondemand_reffor_recordid = ondemandReference_collection.find_one({"record_id": record_id})    
        ondemand_video_forrecordid = ondemand_collection.find_one({"record_id": record_id})
        
        if ondemand_reffor_recordid is None or ondemand_video_forrecordid is None:
            pass
        else:
            record_file_status = ondemand_reffor_recordid['file_list_status']
            record_total_file_count = ondemand_reffor_recordid['total_file_count']
            record_upload_count = ondemand_reffor_recordid['upload_count']
            allrecord_list = ondemand_video_forrecordid['all_records_list']

        
        if record_total_file_count != record_upload_count:
            print(f"record_id {record_id} record_total_file_count {record_total_file_count} record_upload_count {record_upload_count} ")
            
            for record_status in record_file_status:        
                failed_status_path = record_status['file_path']                
                failed_pathlist.append(failed_status_path)
   
            for index, file_path in enumerate(allrecord_list, start=1):  
            #for index, file_path in enumerate(failed_pathlist, start=1):                                                                        
                if index > record_upload_count:
                    try:                    
                        with open(file_path , 'rb') as file:
                            file_name = os.path.basename(file_path)
                            prod_datetime_str = file_name.replace("ts_", "").replace(".ts", "")          
                            datetime_obj = datetime.strptime(prod_datetime_str, "%Y-%m-%d-%H-%M-%S")
                            producer_time = datetime_obj.isoformat()
                            print(f" Record id: {record_id} Index: {index}, File Path: {file_path} producer_time {producer_time}")
                            
                            existing_recordid = ondemand_collection.find_one({"record_id": record_id})
                            if existing_recordid is not None:
                                existing_fileupload_status = existing_recordid.get("upload_status")                

                                
                            existing_fileupload_status = 1
                            if index == record_total_file_count:
                                existing_fileupload_status = 2
                                ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})

                            data = { 
                                "ondemand": record_id,
                                "remaining_count": index,
                                "upload_status": existing_fileupload_status,
                                "producer_datetime": producer_time,
                                "object_id": record_id,
                                "fragment": TS_FRAGMENTS,
                            }
                            print(data)
                            print("FIle path is     ", file_path)
                            try:    
                                response = requests.post(ping_url, data=data, files=[('source_file', file)], headers=headers) 
                                print(response.text)  
                                if response.status_code == 201:
                                    existing_upload_count = index
                                    file_status = "uploaded"
                                    #ondemandReference_collection.update_one({"record_id": record_id, "file_list_status.file_path": file_path},{"$set": {"file_list_status.$.file_status": file_status}})
                                    
                                    ondemandReference_collection.update_one(
                                        {"record_id": record_id, "file_list_status.file_path": file_path},
                                        {"$set": {"file_list_status.$.file_status": file_status}}
                                    )

                                    ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
                                    ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status ,"last_update_time": datetime.now()}})                

                            except Exception as e:                                                       
                                print(f"Error processing file: {file_path}. Exception: {str(e)}")                                                                                                                                  
                                continue
                    except FileNotFoundError:
                        print(f"Warning: File not found at path: {file_path}. Skipping file.")                   
                        

# async def upload_record1():
    
#     for record_id in record_id_list:
#         ondemand_reffor_recordid = ondemandReference_collection.find_one({"record_id": record_id})    
#         record_file_status = ondemand_reffor_recordid['file_list_status']
#         record_total_file_count = ondemand_reffor_recordid['total_file_count']
#         record_upload_count = ondemand_reffor_recordid['upload_count'] 
        
#         if record_total_file_count != record_upload_count:

#             print(f"record_id {record_id} record_total_file_count {record_total_file_count} record_upload_count {record_upload_count} ")
            
#             ondemand_video_forrecordid = ondemand_collection.find_one({"record_id": record_id})
#             allrecord_list = ondemand_video_forrecordid['all_records_list']
#             existing_fileupload_status = ondemand_video_forrecordid.get("upload_status") 
            
#             for record_status in record_file_status:        
#                 failed_status_path = record_status['file_path']        
#                 if record_status['file_status'] == 'failed':
#                     print("Skip it (Because it's failed)")
                    
#                     with open(failed_status_path , 'rb') as file:
#                         file_name = os.path.basename(failed_status_path)
#                         prod_datetime_str = file_name.replace("ts_", "").replace(".ts", "")          
#                         datetime_obj = datetime.strptime(prod_datetime_str, "%Y-%m-%d-%H-%M-%S")
#                         producer_time = datetime_obj.isoformat()

#                         existing_recordid = ondemand_collection.find_one({"record_id": record_id})
#                         if existing_recordid is not None:
#                             existing_fileupload_status = existing_recordid.get("upload_status")                
#                             existing_upload_count = existing_recordid.get("upload_count")
#                             existing_total_count = existing_recordid.get("total_count")
#                             print("existing_fileupload_status",existing_fileupload_status)
#                             print("existing_upload_count",existing_upload_count)                            
#                         file_status = 2


#                         data = { 
#                         "ondemand": record_id,
#                         "remaining_count": existing_upload_count,
#                         "upload_status": file_status,
#                         "producer_datetime": producer_time,
#                         "object_id": record_id,
#                         "fragment": TS_FRAGMENTS,
#                         }
#                         print(data)
#                         try:    

#                             response = requests.post(ping_url, data=data, files=[('source_file', file)], headers=headers) 
#                             print(response.text)  
#                             if response.status_code == 201:
#                                 existing_upload_count += 1  
#                                 file_status = "uploaded"
#                                 existing_fileupload_status = 4

#                                 ondemandReference_collection.update_one(
#                                         {"record_id": record_id, "file_list_status.file_path": failed_status_path},
#                                         {"$set": {"file_list_status.$.file_status": file_status}}
#                                     )
#                                 ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
#                                 ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status ,"last_update_time": datetime.now()}})                
#                         except Exception as e:
#                             existing_fileupload_status = 4
                            
#                             print(f"Error processing file: {failed_status_path}. Exception: {str(e)}")                                                                       
#                             ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
#                             ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status}})                                
#                             continue
#                         if existing_upload_count == existing_total_count:  
#                             existing_fileupload_status = 2
#                             print("Successfully, Specified time range file's is uploaded  . . ")                    
#                         ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})
               
#                 else:      
#                     file_list =[]              
#                     for index, file_path in enumerate(allrecord_list, start=1):                        
#                         if index > record_upload_count:
#                             print("_____________________________________________")
#                             print(f"Index: {index}, File Path: {file_path}")
                            
#                             with open(file_path , 'rb') as file:
#                                 file_name = os.path.basename(file_path)
#                                 prod_datetime_str = file_name.replace("ts_", "").replace(".ts", "")          
#                                 datetime_obj = datetime.strptime(prod_datetime_str, "%Y-%m-%d-%H-%M-%S")
#                                 producer_time = datetime_obj.isoformat()
#                                 print(f"file_name {file_name} producer_time {producer_time}")

#                                 file_status = 2
#                                 data = { 
#                                     "ondemand": record_id,
#                                     "remaining_count": index,
#                                     "upload_status": file_status,
#                                     "producer_datetime": producer_time,
#                                     "object_id": record_id,
#                                     "fragment": TS_FRAGMENTS,
#                                 }
#                                 print(data)
#                                 try:    
#                                     response = requests.post(ping_url, data=data, files=[('source_file', file)], headers=headers) 
#                                     print(response.text)  
#                                     if response.status_code == 201:                                        
#                                         file_status = "uploaded"                                    
#                                         file_status_data = {"file_path": file_path,"file_status": file_status}
#                                         file_list.append(file_status_data)
#                                         ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": index ,"file_list_status" : file_list}})
#                                         ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": index , "upload_status": existing_fileupload_status ,"last_update_time": datetime.now()}})                

#                                 except Exception as e:
#                                     existing_fileupload_status = 4
#                                     print(f"Error processing file: {file_path}. Exception: {str(e)}")                                                                                                           
#                                     ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})                                
#                                     continue
#                                 if record_upload_count == record_total_file_count:  
#                                     existing_fileupload_status = 2
#                                     print("Successfully, Specified time range file's is uploaded  . . ")                    
#                                     ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})
#                                 print("_____________________________________________")

#         else:
#             print("No need to upload video for ondemand")
###################################################################################

# async def failed_upfileslist1():
#     ondemand_data = list(ondemand_collection.find()) 
        
#     if not ondemand_data:        
#         print("No On-Demand_data found (failure)")
#     else:
#         for ondemand_data in ondemand_data:              
#             ondemand_data_list.append(int(ondemand_data['record_id']))

#         for record_id in ondemand_data_list:
            
#             record_info = ondemandReference_collection.find_one({"record_id": record_id})
#             record_file_status = record_info['file_list_status']

#             record_total_file_count = record_info['total_file_count']
#             record_upload_count= record_info['upload_count']
    
    
#             count = 0
#             for record_status in record_file_status:
                
#                 if record_status['file_status'] == 'failed':
#                     print("")
#                     failed_status_path = record_status['file_path']
#                     count += 1
#                     print(f"Record Id {record_id} | | | Filepath {failed_status_path} | | | Count {count}")
                
#                     with open(failed_status_path , 'rb') as file:
#                         file_name = os.path.basename(failed_status_path)
#                         prod_datetime_str = file_name.replace("ts_", "").replace(".ts", "")          
#                         datetime_obj = datetime.strptime(prod_datetime_str, "%Y-%m-%d-%H-%M-%S")
#                         producer_time = datetime_obj.isoformat()

#                         existing_recordid = ondemand_collection.find_one({"record_id": record_id})
#                         if existing_recordid is not None:
#                             existing_fileupload_status = existing_recordid.get("upload_status")                
#                             existing_upload_count = existing_recordid.get("upload_count")
#                             existing_total_count = existing_recordid.get("total_count")
#                             print("existing_fileupload_status",existing_fileupload_status)
#                             print("existing_upload_count",existing_upload_count)
#                         file_status = 2
#                         data = { 
#                             "ondemand": record_id,
#                             "remaining_count": existing_upload_count,
#                             "upload_status": file_status,
#                             "producer_datetime": producer_time,
#                             "object_id": record_id,
#                             "fragment": TS_FRAGMENTS,
#                         }
#                         print(data)
                        
#                         try:    

#                             response = requests.post(ping_url, data=data, files=[('source_file', file)], headers=headers) 
#                             print(response.text)  
#                             if response.status_code == 201:
#                                 existing_upload_count += 1  
#                                 file_status = "uploaded"

#                                 ondemandReference_collection.update_one(
#                                         {"record_id": record_id, "file_list_status.file_path": failed_status_path},
#                                         {"$set": {"file_list_status.$.file_status": file_status}}
#                                     )
#                             ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
#                             ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status ,"last_update_time": datetime.now()}})                
#                         except Exception as e:
#                             existing_fileupload_status = 4
                            
#                             print(f"Error processing file: {failed_status_path}. Exception: {str(e)}")                                                                       
#                             ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
#                             ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status}})                                
#                             continue
                            
                        
#                         if existing_upload_count == existing_total_count:  
#                             existing_fileupload_status = 2
#                             print("Successfully, Specified time range file's is uploaded  . . ")                    
#                         ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})
#                 else:
                    
#                     if record_total_file_count != record_upload_count:
#                         all_files_uploaded = True  
#                         for record_status in record_file_status:
#                             if record_status['file_status'] == 'failed':
#                                 all_files_uploaded = False
#                                 break  
#                         file_list =[]
#                         for record_status in record_file_status:
#                             if all_files_uploaded:           
#                                 failed_status_path = record_status['file_path']                                
#                                 ondemand_data = list(ondemand_collection.find())
#                                 for ondemand_data in ondemand_data:              
#                                     print()
#                                     all_records_list = ondemand_data['all_records_list']                                    
#                                     for recordfile_path in all_records_list:                                        
#                                         if failed_status_path != recordfile_path:                                                                                                                            
#                                             if record_status['file_status'] == 'uploaded': 
#                                                 print("Need to update for shutdown or partial upload video")
#                                                 print(f"Record_id {record_id} recordfile_path {recordfile_path}" )
                                                                    
#                                                 with open(failed_status_path , 'rb') as file:
#                                                     file_name = os.path.basename(failed_status_path)
#                                                     prod_datetime_str = file_name.replace("ts_", "").replace(".ts", "")          
#                                                     datetime_obj = datetime.strptime(prod_datetime_str, "%Y-%m-%d-%H-%M-%S")
#                                                     producer_time = datetime_obj.isoformat()

#                                                     existing_recordid = ondemand_collection.find_one({"record_id": record_id})
#                                                     if existing_recordid is not None:
#                                                         existing_fileupload_status = existing_recordid.get("upload_status")                
#                                                         existing_upload_count = existing_recordid.get("upload_count")
#                                                         existing_total_count = existing_recordid.get("total_count")
                                        
#                                                         file_status = 1
#                                                         data = { 
#                                                             "ondemand": record_id,
#                                                             "remaining_count": existing_upload_count,
#                                                             "upload_status": file_status,
#                                                             "producer_datetime": producer_time,
#                                                             "object_id": record_id,
#                                                             "fragment": TS_FRAGMENTS,
#                                                         }
#                                                         print(data)
#                                                         try:    
#                                                             response = requests.post(ping_url, data=data, files=[('source_file', file)], headers=headers) 
#                                                             print(response.text)  
#                                                             if response.status_code == 201:
#                                                                 existing_upload_count += 1  
#                                                                 file_status = "uploaded"
#                                                                 ondemandReference_collection.update_one(
#                                                                         {"record_id": record_id, "file_list_status.file_path": failed_status_path},
#                                                                         {"$set": {"file_list_status.$.file_status": file_status}}
#                                                                     )
#                                                                 file_status_data = {"file_path": failed_status_path,"file_status": file_status}
#                                                                 file_list.append(file_status_data)
#                                                                 ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count ,"file_list_status" : file_list}})
#                                                                 ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status ,"last_update_time": datetime.now()}})                
#                                                         except Exception as e:
#                                                             existing_fileupload_status = 4
                                                            
#                                                             print(f"Error processing file: {failed_status_path}. Exception: {str(e)}")                                                                       
#                                                             ondemandReference_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count }})
#                                                             ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_count": existing_upload_count , "upload_status": existing_fileupload_status}})                                
#                                                             continue
                                                            
#                                                         if existing_upload_count == existing_total_count:  
#                                                             existing_fileupload_status = 2
#                                                             print("Successfully, Specified time range file's is uploaded  . . ")                    
#                                                         ondemand_collection.update_one({"record_id": record_id}, {"$set": {"upload_status": existing_fileupload_status}})
                                        
from apps.main.database.db import get_db 
from apps.main.models.model import *
import requests
import os
from requests.exceptions import Timeout, ConnectionError, HTTPError,RequestException



async def get_all_camera_by_lpu(active_lpu_id):
    db = next(get_db())
    lpu_list = db.query(LpuGroup).order_by(LpuGroup.id).filter(LpuGroup.lpu_id == active_lpu_id).all() 
    
    rtsp_urls = []
    for lpu in lpu_list:
        rtsp_url = f"rtsp://{lpu.camera_username}:{lpu.camera_password}@{lpu.camera_ip}:{lpu.camera_port}"
        rtsp_urls.append({
            "id": lpu.camera_id,  
            "lpu_id": lpu.lpu_id,      
            "rtsp_url": rtsp_url, 
            "camera_name": lpu.camera_name,          
        })
    return rtsp_urls

async def get_all_camera():
    db = next(get_db())
    lpu_list = db.query(LpuGroup).order_by(LpuGroup.id).all() 
    
    rtsp_urls = []
    for lpu in lpu_list:
        rtsp_url = f"rtsp://{lpu.camera_username}:{lpu.camera_password}@{lpu.camera_ip}:{lpu.camera_port}"
        rtsp_urls.append({
            "id": lpu.id,
            "lpu_id": lpu.lpu_id,
            "lpu_name": lpu.lpu_name,
            "camera_name": lpu.camera_name,
            "rtsp_url": rtsp_url,
            "camera_ip": lpu.camera_ip,
            "camera_status": lpu.camera_status,
            "username": lpu.camera_username,
            "password": lpu.camera_password
        })
    return rtsp_urls

async def get_detetction_details():
    db=next(get_db())
    detection_details=db.query(Detection_details).order_by(Detection_details.id).all()
    print("detection_details:",detection_details)
    detection = []
    for detection in detection_details:
        detection.append({
            "camera_id":detection.camera_id,
            "camera_ip":detection.camera_ip,
            
        })
    return detection





async def get_camera_by_index(index: int):
    db= next(get_db())  
    camera = db.query(LpuGroup).order_by(LpuGroup.id.asc()).offset(index).limit(1).first()

    if camera:
        rtsp_url = f"rtsp://{camera.camera_username}:{camera.camera_password}@{camera.camera_ip}:{camera.camera_port}"
        return {
            "id": camera.id,
            "lpu_id": camera.lpu_id,
            "camera_ip": camera.camera_ip,
            "lpu_name": camera.lpu_name,
            "rtsp_url": rtsp_url
        }
    return None 

async def get_first_camera():
    db = next(get_db())
    first_lpu = db.query(LpuGroup).order_by(LpuGroup.id.asc()).first()

    if first_lpu: 
        rtsp_url = f"rtsp://{first_lpu.camera_username}:{first_lpu.camera_password}@{first_lpu.camera_ip}:{first_lpu.camera_port}"
        return {
            "id": first_lpu.id,
            "lpu_id": first_lpu.lpu_id,
            "lpu_name": first_lpu.lpu_name,
            "rtsp_url": rtsp_url
        }
    return None  

async def get_second_camera():
    db = next(get_db())
    second_lpu = db.query(LpuGroup).order_by(LpuGroup.id.asc()).offset(1).limit(1).first()

    if second_lpu:  
        rtsp_url = f"rtsp://{second_lpu.camera_username}:{second_lpu.camera_password}@{second_lpu.camera_ip}:{second_lpu.camera_port}"
        return {
            "id": second_lpu.id,
            "lpu_id": second_lpu.lpu_id,
            "lpu_name": second_lpu.lpu_name,
            "rtsp_url": rtsp_url
        }
    return None  


async def check_hikvision_camera_status(camera_ip, username, password):    
    request_url = f'http://{camera_ip}:80/ISAPI/System/deviceInfo'
    auth = requests.auth.HTTPDigestAuth(username, password)
    is_streaming = False
    try:
        response = requests.get(request_url, auth=auth, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            is_streaming = True
    except Timeout:
        print("Error: Request timed out.")
    except ConnectionError:
        print(f"[CAMERA NOT LIVE] Error: Could not connect to {camera_ip}.")
    except HTTPError as err:
        print(f"Error: HTTP error occurred - {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    return is_streaming    





async def delete_file(file_path):
    if file_path.exists():
        os.remove(file_path)
        # print(f"Deleted file: {file_path}")

async def delete_ts_files(ts_file_pattern):
    ts_files_deleted = False
    for ts_file in ts_file_pattern.parent.glob(ts_file_pattern.name):
        os.remove(ts_file)
        ts_files_deleted = True
        # print(f"Deleted file: {ts_file}")
        
 
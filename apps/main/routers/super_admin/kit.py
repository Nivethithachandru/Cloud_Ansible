from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db
from apps.main.models.model import * 
from apps.main.utils.jwt import *
from apps.main.config import *
from fastapi.templating import Jinja2Templates
from apps.main.routers.roles.auth_role import *
from apps.main.routers.super_admin.alerts import  camera_status_mail_trigger,kit_status_mail_trigger,storage_status_mail_trigger,temperature_status_mail_trigger
from fastapi import BackgroundTasks
from logg import *
from fastapi_utilities import repeat_every
from sqlalchemy import create_engine,text
from sqlalchemy.exc import SQLAlchemyError
from aiocron import crontab

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")


async def kit_status_function(db, kit_alert_status, org_group, kit_status_now, exiting_kit_status, to_addresses):
    print(f"In kit_status_function for LPU ID: {org_group.lpu_id}")
    print("#$$$$$$$$$$$$$$$$$$$$$$$$")

    if exiting_kit_status == kit_status_now: 
        log_status = "ONLINE" if kit_status_now else "OFFLINE"
        print("log_status:",log_status)
        KIT_MONITOR_LOGGER.warning(f"[KIT] - Status changed to {log_status} for LPU IP: {org_group.lpu_ip}, Name: {org_group.lpu_name}")

        email_message = {
            "kit_status": "Online" if kit_status_now else "Offline",
            "lpu_name": org_group.lpu_name,
            "lpu_ip": org_group.lpu_ip,
            "lpu_id": org_group.lpu_id,
            "to_addresses": to_addresses  
        }

        if kit_alert_status:
            print(f"Permission granted to send email for kit alert: {to_addresses}")
            KIT_MONITOR_LOGGER.info(f"[KIT] - Sending email alert for status change to {log_status} for LPU IP: {org_group.lpu_ip}, Name: {org_group.lpu_name}.")
            await kit_status_mail_trigger(email_message, cam_msg=False, kit_msg=True, store_msg=False, temp_msg=False)
        else:
            KIT_MONITOR_LOGGER.warning(f"[KIT] - No permission to send an email alert for status change to {log_status} for LPU IP: {org_group.lpu_ip}, Name: {org_group.lpu_name}.")
            print("No permission to send an email for kit alert")




        

async def camera_status_function(db,background_tasks,camera_alert_status,lpu_group,camera_status_now,exiting_camera_status):
    print("Camera status existing",exiting_camera_status)
    print("Camera status New",camera_status_now)
    # camera_status_now = False
    existing_kit = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == 1).first()    
    if exiting_camera_status != camera_status_now:
 
        email_message = {
            "camera_ip": lpu_group.camera_ip,
            "camera_status": "Online" if camera_status_now else "Offline",
            "lpu_name": lpu_group.lpu_name, 
            "lpu_id": lpu_group.lpu_id
        }      
        CAMERA_LOGGER.warning(f"[CAMERA] - Status changed to {'Online' if camera_status_now else 'Offline'} for Camera IP: {lpu_group.camera_ip}, LPU Name: {lpu_group.lpu_name}")

        if camera_alert_status:
            CAMERA_LOGGER.info(f"[CAMERA] - Sending email alert for camera status change to {'Online' if camera_status_now else 'Offline'} for Camera IP: {lpu_group.camera_ip}, LPU Name: {lpu_group.lpu_name}.")

            print("Yesssssssssssssssssss permission to send an email for camera alert")
            existing_kit.camera_status = camera_status_now
            db.commit() 
            db.refresh(existing_kit)
            await camera_status_mail_trigger(background_tasks, email_message,cam_msg= True,kit_msg=False,store_msg=False,temp_msg=False)
        else:
            CAMERA_LOGGER.warning(f"[CAMERA] - No permission to send an email alert for camera status change to {'Online' if camera_status_now else 'Offline'} for Camera IP: {lpu_group.camera_ip}, LPU Name: {lpu_group.lpu_name}.")
            existing_kit.camera_status = camera_status_now
            db.commit() 
            db.refresh(existing_kit)
            print("No permission to send an email for camera alert")
    else:
        existing_kit.camera_status = camera_status_now
        db.commit() 
        db.refresh(existing_kit)



async def temp_status_function(db,background_tasks,temp_alert_status,lpu_group,temperature_current_status,exist_temperature_status,data):
    print("Temperature status existing",exist_temperature_status)
    print("Temperature status New",temperature_current_status)
    # temperature_current_status = True
    existing_kit = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == 1).first()
    if exist_temperature_status != temperature_current_status:
        KIT_MONITOR_LOGGER.warning(f"[TEMP] - Temperature status changed to {'High' if temperature_current_status else 'Normal'} for LPU IP: {lpu_group.lpu_ip}, LPU Name: {lpu_group.lpu_name}. CPU Temperature: {data['cpu_percentage_usage']}")

        email_message = {               
            "lpu_name": lpu_group.lpu_name,
            "lpu_ip": lpu_group.lpu_ip,
            "lpu_id": lpu_group.lpu_id,
            "cpu_temperature": float(data['cpu_percentage_usage'])
        }  
        if temp_alert_status:
            KIT_MONITOR_LOGGER.info(f"[TEMP] - Sending email alert for temperature status change for LPU IP: {lpu_group.lpu_ip}, LPU Name: {lpu_group.lpu_name}. CPU Temperature: {data['cpu_percentage_usage']}")
            existing_kit.temp_status = temperature_current_status
            db.commit() 
            db.refresh(existing_kit)
            print("Yess permission to send an email for temperature alert")
            # await temperature_status_mail_trigger(background_tasks, email_message,cam_msg= False,kit_msg=False,store_msg=False ,temp_msg=True)
        else:
            KIT_MONITOR_LOGGER.warning(f"[TEMP] - No permission to send an email alert for temperature status change for LPU IP: {lpu_group.lpu_ip}, LPU Name: {lpu_group.lpu_name}. CPU Temperature: {data['cpu_percentage_usage']}")
            existing_kit.temp_status = temperature_current_status
            db.commit() 
            db.refresh(existing_kit)
            print("No permission to send an email for temperature alert")
    else:
        existing_kit.temp_status = temperature_current_status
        db.commit() 
        db.refresh(existing_kit)


############################################ MAIL FUNCTION ##########################################################################
 
async def mail_trigger():
    db = next(get_db())

    offline_lpus = db.query(Lpu_management).filter(Lpu_management.lpu_status == False).all()
    online_lpus = db.query(Lpu_management).filter(Lpu_management.lpu_status == True).all()

   # IF KIT IS OFFLINE,

    for org_group in offline_lpus:
        print(f"Processing Offline LPU ID: {org_group.lpu_id}, Name: {org_group.lpu_name}, Status: OFFLINE")

        alert_settings = db.query(settings).filter(settings.lpu_id == org_group.lpu_id).all()

        for alert_setting in alert_settings:
            to_addresses = alert_setting.to_address  
            kit_alert_status = alert_setting.kit_alert

            print(f"Sending kit alert email to: {to_addresses} for LPU ID: {org_group.lpu_id}")

            try:
                await kit_status_function(db, kit_alert_status, org_group, org_group.lpu_status, org_group.lpu_status, to_addresses)
                # print("Kit alert processed successfully")
            except Exception as e:
                print(f"Error in kit_status_function: {e}")
                continue  

    # IF KIT IS ONLINE,
    for org_group in online_lpus:
        print(f"Processing Online LPU ID: {org_group.lpu_id}, Name: {org_group.lpu_name}, Status: ONLINE")

        alert_settings = db.query(settings).filter(settings.lpu_id == org_group.lpu_id).all()

        for alert_setting in alert_settings:
            to_addresses = alert_setting.to_address  
            kit_alert_status = alert_setting.kit_alert

            print(f"Sending kit alert email to: {to_addresses} for LPU ID: {org_group.lpu_id}")

            try:
                print("$!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!5")
                await kit_status_function(db, kit_alert_status, org_group, org_group.lpu_status, org_group.lpu_status, to_addresses)
                print("Kit alert processed successfully for online LPU")
            except Exception as e:
                print(f"Error in kit_status_function for online LPU: {e}")
                continue  

        alert_settings = db.query(settings).filter(settings.lpu_id == org_group.lpu_id, settings.storage_alert == True).all()

        for alert_setting in alert_settings:
            lpu_id = alert_setting.lpu_id
            to_addresses = alert_setting.to_address 

            storage_records = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == lpu_id).all()
            org_list = db.query(Lpu_management).filter(Lpu_management.lpu_id == lpu_id).first()

            if not storage_records:
                print(f"No storage data found for LPU ID: {lpu_id}")
                continue

            for storage in storage_records:
                if storage.total_disk_gb > 0:
                    used_disk_percentage = (int(storage.used_disk_gb) / int(storage.total_disk_gb)) * 100
                else:
                    print(f"Invalid storage data for LPU ID: {lpu_id}")
                    continue

                print(f"LPU ID: {lpu_id} - Used Disk Percentage: {used_disk_percentage:.2f}%")

                if used_disk_percentage >= 60:
                    print(f"Storage usage critical for Online LPU ID: {lpu_id}, sending email alert...")

                    email_message = {
                        "storage_status": f"Critical - {used_disk_percentage:.2f}% used",
                        "lpu_name": org_list.lpu_name, 
                        "lpu_ip": org_list.lpu_ip,      
                        "lpu_id": lpu_id,
                        "total_disk_gb": int(storage.total_disk_gb),
                        "used_disk_gb": int(storage.used_disk_gb),
                        "free_disk_gb": int(storage.total_disk_gb) - int(storage.used_disk_gb),
                        "to_addresses": to_addresses
                    }

                    try:
                        print(f"Before sending storage alert email for Online LPU ID: {lpu_id}")
                        # await storage_status_mail_trigger(email_message, cam_msg=False, kit_msg=False, store_msg=True, temp_msg=False)
                    except Exception as e:
                        print(f"Error in storage_status_mail_trigger: {e}")







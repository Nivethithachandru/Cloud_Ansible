from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from main import CLASSES_ROOT
from apps.main.utils.jwt import *
from fastapi.templating import Jinja2Templates
from apps.main.utils.session import * 
from aiocron import crontab
from fastapi import APIRouter, BackgroundTasks
from apps.main.routers.super_admin.mailer import send_email

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")



@router.get('/main/settings/', response_class=HTMLResponse, name="main.settings")
async def settings_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")  
      
    role_id = session_data.get('role_id')
    db = next(get_db())   
    lpu_id=session_data['lpu_id']
    
    modulee_id = 16
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    existing_settings = db.query(settings).filter(settings.id == lpu_id).first()

    
    if role_id == 0:        
        return templates.TemplateResponse("mail/setting.html", 
                                          {"request": request, "session": session_data, "existing_settings":existing_settings}
                                          )
    else:
        if show_required_permission:
            return templates.TemplateResponse("mail/setting.html", 
                                          {"request": request, "session": session_data, "existing_settings":existing_settings}
                                          )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)
        


@router.post('/main/setting/add_update/')
async def user_alert_settings(request: Request):
    try:
        data = await request.json()

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        lpu_id=session_data['lpu_id']
        
        role_id = session_data.get('role_id')
        db = next(get_db())

        modulee_id = 16
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission",required_permission)


        to_address_input = data.get('to_address', '')
        to_address_list = [email.strip() for email in to_address_input.split(',') if email.strip()]
        kit_alert = data.get('kit_alert')
        camera_alert = data.get('camera_alert')
        storage_alert = data.get('storage_alert')
        temp_alert = data.get('temp_alert')

        existing_settings = db.query(settings).filter(settings.lpu_id == lpu_id).first() 
       
        if role_id != 0:
            if not required_permission:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Access Denied: You are not authorized to perform this operation."}
                )
        
        if existing_settings:
            existing_settings.to_address = to_address_list   
            existing_settings.kit_alert = kit_alert
            existing_settings.camera_alert = camera_alert
            existing_settings.storage_alert = storage_alert
            existing_settings.temperature_alert = temp_alert
            existing_settings.updated_at = datetime.now()
        else:
            new_settings = settings(
                to_address=to_address_list,  
                kit_alert=kit_alert,
                camera_alert=camera_alert,
                storage_alert=storage_alert,
                temperature_alert=temp_alert,
                lpu_id=lpu_id
            )
            db.add(new_settings)


        db.commit()
        db.refresh(existing_settings if existing_settings else new_settings)
        return JSONResponse(content={"message": "Alert settings updated successfully."})
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




# --------------------------camera alerts --------------------
 
async def camera_status_mail_trigger(background_tasks: BackgroundTasks, email_message, cam_msg, kit_msg,store_msg,temp_msg):
    subject = f" {email_message['lpu_name']} - Camera {email_message['camera_ip']} is {email_message['camera_status']}"
    background_tasks.add_task(send_email, subject, email_message, cam_msg, kit_msg,store_msg,temp_msg)
    return {"status": 200, "message": "Email has been scheduled"}

import threading

async def kit_status_mail_trigger(email_message, cam_msg, kit_msg, store_msg, temp_msg):
    print("in send email -kit status")
    subject = f"{email_message['lpu_name']} is {email_message['kit_status']}"
    print("subject in kit status:", subject)
    email_thread = threading.Thread(target=send_email, args=(subject, email_message, cam_msg, kit_msg, store_msg, temp_msg))
    email_thread.start()

    return {"status": 200, "message": "Email has been scheduled"}



async def storage_status_mail_trigger(email_message, cam_msg, kit_msg,store_msg,temp_msg):
    subject = f" {email_message['lpu_name']} - Storage  is {email_message['storage_status']}"

    print("in storage alert fucntion",email_message['to_addresses'],"subject:",subject)

    storage_email_thread = threading.Thread(target=send_email, args=(subject, email_message, cam_msg, kit_msg, store_msg, temp_msg))
    storage_email_thread.start()
    return {"status": 200, "message": "Email has been scheduled"}


async def temperature_status_mail_trigger(background_tasks: BackgroundTasks, email_message, cam_msg, kit_msg,store_msg,temp_msg):
    subject = f"{email_message['lpu_name']} - Temperature is High - {email_message['cpu_temperature']}°C"
    background_tasks.add_task(send_email, subject, email_message, cam_msg, kit_msg,store_msg,temp_msg)
    return {"status": 200, "message": "Email has been scheduled"}

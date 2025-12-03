from apps.main.database.db import *
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from apps.main.models.model import * 
from apps.main.utils.jwt import *
from apps.main.config import SESSION_EXPIRE_MINUTES
from apps.main.routers.roles.auth_role import *


import pytz

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")
 


@router.get("/auth/dashboard/", response_class=HTMLResponse, name="auth.dashboard")
async def role_dashboard(request: Request, lpu_id: int, lpu_ip: str,lpu_name:str):
    try:
        db = next(get_db()) 
        print("lpu ip:", lpu_ip,lpu_name)

        session_data, error_response = handle_session(request, lpu_id, lpu_ip,lpu_name)
        if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        print("lpu_id:", lpu_id)
        db.query(LpuGroup).update({"lpu_status": False})  
        db.query(LpuGroup).filter(LpuGroup.lpu_id == lpu_id).update({"lpu_status": True})
        db.commit()

       
        lpu_group = db.query(Lpu_management).filter(Lpu_management.lpu_id == lpu_id).first()

        if lpu_group:
            lpu_data = {
                "id": lpu_group.lpu_id,
                "name": lpu_group.lpu_name,
                "ip": lpu_group.lpu_ip,
                "lpu_status":lpu_group.lpu_status
            }
            print("LPU Data:", lpu_data)
        else:
            print(f"LPU with ID {lpu_id} not found. Proceeding without LPU data.")
            lpu_data = {"id": None, "name": "Unknown LPU", "ip": "Unknown"}


        first_kit = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == lpu_id).first()
        print("First Kit:", first_kit)

                
        if first_kit and first_kit.kit_time:
            india_tz = pytz.timezone("Asia/Kolkata")
            india_time = first_kit.kit_time.astimezone(india_tz)
            kit_time_str = india_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            kit_time_str = "No time available"  

        default_kit_data = {
            "lpu_status": lpu_data["lpu_status"],
            "id": first_kit.id if first_kit else None,
            "lpu_id": first_kit.lpu_id if first_kit else None,
            "total_disk_gb": first_kit.total_disk_gb if first_kit else None,
            "used_disk_gb": first_kit.used_disk_gb if first_kit else None,
            "free_disk_gb": first_kit.free_disk_gb if first_kit else None,
            "cpu_core": first_kit.cpu_core if first_kit else None,
            "kit_fan_speed": first_kit.kit_fan_speed if first_kit else None,
            "cpu_temperature": first_kit.cpu_temperature if first_kit else None,
            "gpu_temperature": first_kit.gpu_temperature if first_kit else None,
            "gpu_usage": first_kit.gpu_usage if first_kit else None,
            "cpu_percentage_usage": first_kit.cpu_percentage_usage if first_kit else None,
            "ram_percentage_usage": first_kit.ram_percentage_usage if first_kit else None,
            "system_uptime": first_kit.system_uptime if first_kit else None,
            "total_ram_gb": first_kit.total_ram_gb if first_kit else None,
            "used_ram_gb": first_kit.used_ram_gb if first_kit else None,
            "kit_time": kit_time_str if first_kit and first_kit.kit_time else 'No time available',
            "camera_status": first_kit.camera_status if first_kit else None,
            "upload_speed": first_kit.upload_speed if first_kit else None,
            "download_speed": first_kit.download_speed if first_kit else None,
            "camera_fps" : first_kit.camera_fps if first_kit else None

        }

        print("Default Kit Data:", default_kit_data)
      
        print("session_data", session_data['lpu_id'], session_data['lpu_ip'])

        return templates.TemplateResponse(
            "roles/dashboard_kit.html",
            {
                "request": request,
                "session": session_data,
                "lpu_dropdown": lpu_data,
                "kit_data": default_kit_data   
            }
        )

    except Exception as e:
        print("Error from dashboard:", e)
        return templates.TemplateResponse(
            "roles/dashboard_kit.html",
            {
                "request": request,
                "session": session_data,
                "lpu_dropdown": None,
                "kit_data": None   
            }
        )



# @router.get("/kit_live/get_refresh_data/", response_class=JSONResponse)
# async def get_kits_by_refresh_data():
#     db = next(get_db()) 

#     lpu_groups = db.query(LpuGroup).all() 
#     lpu_dropdown_data = [{"id": 1, "name":'LHS' } for lpu in lpu_groups]
#     print("lpu:",lpu_dropdown_data)

#     first_kit = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == lpu_dropdown_data[0]['id']).first() if lpu_dropdown_data else None
    
#     default_kit_data = {
#         "id": first_kit.id if first_kit else None,
#         "lpu_id": first_kit.lpu_id if first_kit else None,
#         "total_disk_gb": first_kit.total_disk_gb if first_kit else None,
#         "used_disk_gb": first_kit.used_disk_gb if first_kit else None,
#         "free_disk_gb": first_kit.free_disk_gb if first_kit else None,
#         "cpu_core": first_kit.cpu_core if first_kit else None,
#         "kit_fan_speed": first_kit.kit_fan_speed if first_kit else None,
#         "cpu_temperature": first_kit.cpu_temperature if first_kit else None,
#         "gpu_temperature": first_kit.gpu_temperature if first_kit else None,
#         "gpu_usage": first_kit.gpu_usage if first_kit else None,
#         "cpu_percentage_usage": first_kit.cpu_percentage_usage if first_kit else None,
#         "ram_percentage_usage": first_kit.ram_percentage_usage if first_kit else None,
#         "system_uptime": first_kit.system_uptime if first_kit else None,
#         "total_ram_gb": first_kit.total_ram_gb if first_kit else None,
#         "used_ram_gb": first_kit.used_ram_gb if first_kit else None,
#         "kit_time": first_kit.kit_time.isoformat() if first_kit.kit_time else None,

#         "camera_status": first_kit.camera_status if first_kit else None,
#     }


#     print("default kit data:",default_kit_data)
#     return JSONResponse(content={"kit_data": default_kit_data})


 
@router.get("/kit_live/{lpu_id}", response_class=JSONResponse)
async def get_kits_by_lpu_id(lpu_id):
    db = next(get_db()) 

    kits_monitor = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == lpu_id).all()

    kits_data = [
        {
            "id": kit.id,
            "lpu_id": kit.lpu_id,
            "total_disk_gb": kit.total_disk_gb,
            "used_disk_gb": kit.used_disk_gb,
            "free_disk_gb": kit.free_disk_gb,
            "cpu_core": kit.cpu_core,
            "kit_fan_speed": kit.kit_fan_speed,
            "cpu_temperature": kit.cpu_temperature,
            "gpu_temperature": kit.gpu_temperature,
            "gpu_usage": kit.gpu_usage,
            "cpu_percentage_usage": kit.cpu_percentage_usage,
            "ram_percentage_usage": kit.ram_percentage_usage,
            "system_uptime": kit.system_uptime,
            "total_ram_gb": kit.total_ram_gb,
            "used_ram_gb": kit.used_ram_gb,
            "kit_time": kit.kit_time.isoformat() if kit.kit_time else None,
            "camera_status": kit.camera_status,
            "download_speed": kit.download_speed,
            "upload_speed": kit.upload_speed,
            "created_at": kit.created_at.isoformat(),
            "updated_at": kit.updated_at.isoformat()
        }
        for kit in kits_monitor
    ]

    print("kits_data:",kits_data)

    
    return JSONResponse(content={"data": kits_data})



import base64
from datetime import timezone
from typing import List, Optional
from fastapi import FastAPI,APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.routers.super_admin.super_admin import has_permission_bool
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import status
from pydantic import BaseModel
from sqlalchemy import desc
from apps.main.models.model import *
from apps.main.config import *
import asyncio
from fastapi import Depends
import base64
from sqlalchemy import text
# from apps.main.deepstream.draw_line.newdeeptrack import deep_start
from apps.main.deepstream.draw_line import *
from apps.main.database.db import get_db
from logg import *
import json,os,signal
from apps.main.utils.session import handle_session
from datetime import datetime, timezone

app = FastAPI()
router=APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="apps/main/front_end/templates")

 

@router.get('/main/project/edit/{project_id}/')
async def edit_project(project_id: int, request: Request):
    try:
        db_session = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")    

        project = db_session.query(Project).filter(Project.id == project_id).first()

        return templates.TemplateResponse("super_admin/project/edit_project.html", {
            'request': request,
            'project':project,
            "session": session_data
       })
    except Exception as e:
        print(e,"asdf")

 


@router.post('/main/project/update/{project_id}')
async def update_module(project_id: int, request: Request):
    try:
        print("*************************project udpate*******")
        db  = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        lpu_id = session_data['lpu_id']
        lpu_record = db.query(Lpu_management).filter(
                Lpu_management.lpu_id == lpu_id, 
                Lpu_management.lpu_status == False  
            ).all()

        print("lpu_records:",lpu_record)

        if lpu_record:
            return templates.TemplateResponse(
                "super_admin/project/edit_project.html",
                {
                    "request": request,
                    "session": session_data,
                    "project": db.query(Project).filter(Project.id == project_id).first(),
                    "error": f"Kit is offline, cannot update LPU ID '{lpu_id}'."
                },
                status_code=400
            )
            # raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update LPU ID '{lpu_id}'.")
        
        form_data = await request.form()
        project_name = form_data.get('project_name')
       

        print("project_name:",project_name)

        module_to_update = db.query(Project).filter(Project.id == project_id).first()

        if not module_to_update:
            raise HTTPException(status_code=404, detail=f"Project ID {project_id} not found")
    
        module_to_update.project_name = project_name
        module_to_update.updated_status = True
    
        db.commit()
        db.refresh(module_to_update)

        return templates.TemplateResponse("super_admin/project/edit_project.html", {
            "request": request,
            "session": session_data,
            "project": module_to_update,
            "message": "Project  updated successfully."
        })
    except Exception as e:
        print("Error update project",e)





from sqlalchemy.sql import text

@router.get('/available_camera', response_class=JSONResponse)
async def get_available_camera(request: Request):
    try:
        db_session = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        lpu_id = session_data['lpu_id']

        query = text("""
            SELECT DISTINCT ON (camera_ip) camera_ip, camera_status 
            FROM lpu_group 
            WHERE lpu_id = :lpu_id
            ORDER BY camera_ip, updated_at DESC
        """)
        
        cameras = db_session.execute(query, {"lpu_id": lpu_id}).fetchall()
        
        return [{"camera_ip": camera[0], "camera_status": camera[1]} for camera in cameras]
    except Exception as e:
        print(f"Error fetching cameras: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cameras") from e
    finally:
        db_session.close()



@router.get('/available_cameras', response_class=JSONResponse)
async def get_available_cameras():
    try:
        db_session = next(get_db()) 
  
        cameras = db_session.execute(text('SELECT camera_ip FROM lpu_group')).fetchall()
        
        return [{"camera_ip": camera[0]} for camera in cameras]
    except Exception as e:
        print(f"Error fetching cameras: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cameras") from e
    finally:
        db_session.close()





@router.post('/main/add/project')
async def add_project(request: Request):
    data = await request.json()
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    role_id = session_data.get('role_id')
   
    project_name = data.get('project_name')
    camera_ips = data.get('camera_ips')
    camera_status = data.get('camera_status')
    project_id = data.get('project_id')
    analytics = data.get('analytics')

    db_session = next(get_db())
    modulee_id = 5
    show_required_permission = "create" 

    show_required_permission = await has_permission_bool(db_session, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    
    if role_id != 0:
        if not show_required_permission:
            return JSONResponse(
                status_code=403,
                content={"message": "Access Denied: You are not authorized to perform this operation."}
            )

    print("Received data:")
    print(f"project_name: {project_name}")
    print(f"project_id: {project_id}")
    print(f"camera_ips: {camera_ips}")
    print(f"camera_status: {camera_status}")
    print(f"analytics: {analytics}")

    print(f"Session_data:{session_data}")
    print("session_data",session_data['lpu_id'])
    lpu_id=session_data['lpu_id']

    if not all([project_name, project_id, camera_ips, camera_status]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    camera_status = camera_status.lower() == 'true' if isinstance(camera_status, str) else camera_status

    lpu_id=session_data['lpu_id']

    db_session = next(get_db())

    lpu_record = db_session.query(Lpu_management).filter(
            Lpu_management.lpu_id == lpu_id, 
            Lpu_management.lpu_status == False  
        ).all()

    print("lpu_records:",lpu_record)

    if lpu_record:
        print("#######")

        return JSONResponse(
            status_code=400,
            content={"message": f" Kit is offline,cannot add New Project! '{lpu_id}'."}
        )

    try:
  
        last_project = db_session.query(Project).order_by(Project.project_id.desc()).first()
        if last_project:
            new_project_id = int(last_project.project_id) + 1
        else:
            new_project_id = 1

        null_line_crossing = {
            "line_id_1": {
                "topx": None,
                "bottomx": None,
                "topy": None,
                "bottomy": None,
                "direction": None
            },
            "line_id_2": {
                "topx": None,
                "bottomx": None,
                "topy": None,
                "bottomy": None,
                "direction": None
            },
            "line_id_3": {
                "topx": None,
                "bottomx": None,
                "topy": None,
                "bottomy": None,
                "direction": None
            }
        }

        camera_ips_str = json.dumps(camera_ips)  

        new_project = Project(
            project_id=new_project_id,
            project_name=project_name,
            camera_ip=camera_ips_str,
            camera_status=camera_status,
            analytics=analytics,
            updated_status=True,
            lpu_id=lpu_id
        )
        db_session.add(new_project)

        for ip in camera_ips:
            detection_detail = Detection_details(
                project_id=new_project_id,
                camera_ip=ip,
                camera_status=camera_status,
                line_crossing=null_line_crossing,
                lpu_id=lpu_id

            )
            db_session.add(detection_detail)

        default_coordinates = [
                ["polygon_1", {"x1": 0, "y1": 0}],
                ["polygon_2", {"x1": 0, "y1": 0}]
            ]

        polygon_detail = Polygon_details(
            project_id=new_project_id,
            camera_ip=ip,
            coordinates=default_coordinates,
            updated_status=True,
            lpu_id=lpu_id
        )
        db_session.add(polygon_detail)


        db_session.commit()

        return {"message": "Project, detection details, and ROI mappings added successfully"}
    
    except Exception as e:
        print(f"Error adding project: {e}")
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Error adding project")
    
    finally:
        db_session.close()

@router.get('/main/project_id')
async def get_project_id():

    db=next(get_db())
   
    last_project = db.query(Project).order_by(Project.project_id.desc()).first()  
    if last_project:
        try:
   
            new_project_id = int(last_project.project_id) + 1
        except ValueError:
   
            new_project_id = 1
    else:
        
        new_project_id = 1

    print("new_project id value:",new_project_id)

    return {"project_id": new_project_id}


        

@router.get('/camera_status/{camera_ip}', response_class=JSONResponse)
async def get_camera_status(camera_ip: str):
    try:
        db_session = next(get_db())
        print("camera_ip:", camera_ip)

        camera_ips = camera_ip.split(",")
        cam_status = False

        for ip in camera_ips:
            result = db_session.execute(
                text('SELECT camera_status FROM lpu_group WHERE camera_ip = :camera_ip'), 
                {'camera_ip': ip.strip()}
            ).fetchone()

            if result:
                cam_status = True
                break

        if cam_status:
            return {"camera_status": True}
        else:
            raise HTTPException(status_code=404, detail="Camera not found")

    except Exception as e:
        print(f"Error fetching camera status: {e}")
        raise HTTPException(status_code=500, detail="Error fetching camera status") from e
    finally:
        db_session.close()



@router.get('/main/draw_list')
async def draw_list(request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    lpu_ids = session_data.get('lpu_id')
    if not lpu_ids:
        raise HTTPException(status_code=400, detail="Missing lpu_id in session")

    detection = db.query(Project).filter(Project.lpu_id == lpu_ids).all()

    pro_dict = {}
    for detection_item in detection:
    
        if detection_item.camera_ip.startswith('[') and detection_item.camera_ip.endswith(']'):
            camera_ips = detection_item.camera_ip.strip('[]').split(',')
        else:
            camera_ips = [detection_item.camera_ip]

        cleaned_ips = [ip.strip().strip('"').strip("[]").replace('"', '').replace("'", "") for ip in camera_ips]

        print("Available cameras:", cleaned_ips)

        if detection_item.project_id not in pro_dict:
            pro_dict[detection_item.project_id] = {
                "project_id": detection_item.project_id,
                "project_name": detection_item.project_name,
                "camera_ip": detection_item.camera_ip,
                "available_cameras": []
            }
        
        pro_dict[detection_item.project_id]["available_cameras"].extend(cleaned_ips)

    pro_list = list(pro_dict.values())
    print("List:", pro_list)

    return JSONResponse(content={"data": pro_list})
 

@router.get('/main/list_project/')
async def project_list(request:Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    lpu_id=session_data['lpu_id']

    
    
    # detection = db.query(Project).filter(Project.lpu_id == lpu_id).all()
    detection = db.query(Project).filter(Project.lpu_id == lpu_id).order_by(Project.id).all()

  

    line_value = db.query(ROIMapping).order_by(ROIMapping.id).all()
    print("detectiondetectiondetectiondetectiondetection",detection)
    pro_list = []
    for detection_item in detection:
        camera_ips = detection_item.camera_ip.split(',')

        for ip in camera_ips:
            cleaned_ip = ip.strip().strip('"').strip("[]").replace('"', '').replace("'", "")


            detection_log_entry = db.query(Detection_log).filter(
                Detection_log.project_id == detection_item.project_id,
                Detection_log.camera_ip == cleaned_ip
            ).order_by(Detection_log.created_at.desc()).first()  

            
            
            detection_status = detection_log_entry.detection_status if detection_log_entry else "Inactive" 
           
            project_lines = [
                line.lineid for line in line_value
                if line.project_id == detection_item.project_id and line.camera_ip == cleaned_ip
            ]
            polygon=[
                polygon.polygon for polygon in line_value
                if polygon.project_id == detection_item.project_id and polygon.camera_ip == cleaned_ip
            ]
            print("polygon list:",polygon)
            print("cloud status:",detection_item.cloud_status)

            pro_list.append({
                "project_id": detection_item.project_id,
                "project_name": detection_item.project_name,
                "camera_ip": cleaned_ip,
                "line": project_lines,
                "polygon":polygon,
                "detection_status": detection_item.cloud_status,
                "camera_status":detection_item.camera_status
            })

   
    return JSONResponse(content={"data": pro_list})


from sqlalchemy import or_, func





@router.delete('/main/project/delete/{project_id}/{camera_ip}')
async def delete_project(project_id: str, camera_ip: str,request:Request):
    try:
        print(f"Deleting project_id: {project_id}, camera_ip: {camera_ip}")
        db = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")


        lpu_id=session_data['lpu_id']

        project = db.query(Project).filter(
            Project.project_id == project_id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project ID not found")
        
        if project:
            modify_pro =Ondelete(
                             project_id=project_id,
                             camera_ip=camera_ip,
                             status=True,
                             lpu_id=lpu_id

                               
                            )
            print("delete project:", modify_pro.__dict__)
            db.add(modify_pro)

     
        if isinstance(project.camera_ip, str) and project.camera_ip == camera_ip:
            db.delete(project) 
        else:
            try:
                camera_ip_list = json.loads(project.camera_ip) if isinstance(project.camera_ip, str) else project.camera_ip
            except json.JSONDecodeError:
                camera_ip_list = [project.camera_ip] 

            if camera_ip in camera_ip_list:
                print("Camera IP list before removal:", camera_ip_list)
                camera_ip_list.remove(camera_ip)

                if not camera_ip_list:
                    db.delete(project)  
                else:
                    project.camera_ip = json.dumps(camera_ip_list)  
                    db.add(project)
            else:
                raise HTTPException(status_code=404, detail="Camera IP not found in the project")

  
        db.query(Detection_details).filter(
            Detection_details.project_id == project_id,
            Detection_details.camera_ip == camera_ip
        ).delete()

        db.query(ROIMapping).filter(
            ROIMapping.project_id == project_id,
            ROIMapping.camera_ip == camera_ip
        ).delete()

        db.query(Detection_log).filter(
         Detection_log.project_id == project_id,
        Detection_log.camera_ip == camera_ip   
        ).delete()
        db.query(Polygon_details).filter(Polygon_details.project_id ==project_id,Polygon_details.camera_ip==camera_ip).delete()
        db.query(Roi_detection).filter(Roi_detection.project_id == project_id,Roi_detection.camera_ip ==  camera_ip).delete()

        db.commit()
        return {"detail": "Project updated or deleted successfully"}

    except Exception as e:
        import traceback
        print(f"Error updating project: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


import os
import signal
import psutil  # To check if processes are running

from typing import Optional

class Detection(BaseModel):
    id: int
    date_time: Optional[str] = None
    vehicle_id: Optional[int] = None
    vehicle_class_id: Optional[int] = None
    vehicle_name: Optional[str] = None
    direction: Optional[str] = None
    cross_line: Optional[int] = None
    x1_coords: Optional[float] = None
    y1_coords: Optional[float] = None
    x2_coords: Optional[float] = None
    y2_coords: Optional[float] = None
    frame_number: Optional[int] = None
    image_path: Optional[str] = None
    project_id: Optional[int] = None
    line_id: Optional[str] = None
    camera_ip: Optional[str] = None
    ai_class: Optional[str] = None
    audited_class: Optional[str] = None
    is_audit: Optional[bool] = None
    detection_id: Optional[int] = None
    last_modified: Optional[str] = None
    mapped_line: Optional[str] = None
    image_base64: Optional[str] = None

    

class DetectionList(BaseModel):
    detections: List[Detection]




# Define the new base directory where images should be saved
SAVE_DIRECTORY = media_base_path  # Set this to your required location
print("SAVE_DIRECTORY:", SAVE_DIRECTORY)
os.makedirs(SAVE_DIRECTORY, exist_ok=True)  # Ensure base directory exists

# @router.post("/detection_status")
# def receive_detections(detection_data: DetectionList):
#     print("detection_data:", detection_data)
#     try:
#         db = next(get_db())
#         saved_detections = []

#         print("detection_data:", detection_data.detections)

#         for det in detection_data.detections:
#             print("det.image_path:", det.image_path)
#             image_path = det.image_path  # Original path

#             if image_path and "/files/" in image_path:
#                 # Extract path after "/files/"
#                 relative_path = image_path.split("/files/", 1)[-1]
#                 print("relative_path:", relative_path)

#                 # Final save location
#                 final_directory = os.path.join(SAVE_DIRECTORY, os.path.dirname(relative_path))
#                 filename = os.path.basename(relative_path)
#                 print("final_directory:", final_directory)
#                 print("filename:", filename)

#                 # Ensure directory exists
#                 os.makedirs(final_directory, exist_ok=True)

#                 # Final image path
#                 final_image_path = os.path.join(final_directory, filename)
#                 print("final_image_path:", final_image_path)



#             #     # If base64 image is provided, decode and save it
#                 if det.image_base64:
#                     try:
#                         with open(final_image_path, "wb") as img_file:
#                             img_file.write(base64.b64decode(det.image_base64))
#                     except Exception as e:
#                         print(f"Error saving image: {e}")
#                         continue  # Skip if there's an error

#                 new_detection = kit1_objectdetection(
#                     id=det.id,
#                     date_time=det.date_time,
#                     vehicle_id=det.vehicle_id,
#                     vehicle_class_id=det.vehicle_class_id,
#                     vehicle_name=det.vehicle_name,
#                     direction=det.direction,
#                     cross_line=det.cross_line,
#                     x1_coords=det.x1_coords,
#                     y1_coords=det.y1_coords,
#                     x2_coords=det.x2_coords,
#                     y2_coords=det.y2_coords,
#                     frame_number=det.frame_number,
#                     image_path=final_image_path,  # Store updated path
#                     project_id=det.project_id,
#                     line_id=det.line_id,
#                     camera_ip=det.camera_ip,
#                     ai_class=det.ai_class,
#                     audited_class=det.audited_class,
#                     is_audit=det.is_audit,
#                     detection_id=det.detection_id,
#                     last_modified=det.last_modified,
#                     mapped_line=det.mapped_line
#                 )

#                 db.add(new_detection)
#                 saved_detections.append(new_detection)

#         db.commit()
#         return {"status": "success", "message": f"{len(saved_detections)} detections saved successfully."}
    
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Error processing detections: {str(e)}")

# Define the new base directory where images should be saved
SAVE_DIRECTORY = media_base_path  # Set this to your required location
print("SAVE_DIRECTORY:", SAVE_DIRECTORY)
os.makedirs(SAVE_DIRECTORY, exist_ok=True)


@router.post("/detection_status")
def receive_detections(detection_data: DetectionList):
    print("PROCESSING DETECTIONS...")
    try:
        db = next(get_db())
        saved_detections = []

        for det in detection_data.detections:
            # print("det.image_path:", det.image_path)
            image_path = det.image_path  # Original path

            if image_path and "/files/" in image_path:
                # Extract path after "/files/"
                relative_path = image_path.split("/files/", 1)[-1]
                # print("relative_path:", relative_path)

                # Final save location
                final_directory = os.path.join(SAVE_DIRECTORY, os.path.dirname(relative_path))
                filename = os.path.basename(relative_path)
                # print("final_directory:", final_directory)
                # print("filename:", filename)

                # Ensure directory exists
                os.makedirs(final_directory, exist_ok=True)

                # Final image path
                final_image_path = os.path.join(final_directory, filename)
                # print("final_image_path:", final_image_path)

                # Save image if base64 is provided
                if det.image_base64:
                    try:
                        with open(final_image_path, "wb") as img_file:
                            img_file.write(base64.b64decode(det.image_base64))
                    except Exception as e:
                        print(f"Error saving image: {e}")
                        continue  # Skip if there's an error

                # 🔍 Check for existing detection
                existing = db.query(kit1_objectdetection).filter_by(
                    detection_id=det.detection_id,
                    project_id=det.project_id,
                    line_id=det.line_id,
                    camera_ip=det.camera_ip,
                    frame_number=det.frame_number,
                    date_time=det.date_time
                ).first()

                if existing:
                    print(f"Duplicate detection found: {det.detection_id}, skipping...")
                    continue  # Skip if already exists

                # ✅ Insert new detection
                new_detection = kit1_objectdetection(
                    # id=det.id,
                    date_time=det.date_time,
                    vehicle_id=det.vehicle_id,
                    vehicle_class_id=det.vehicle_class_id,
                    vehicle_name=det.vehicle_name,
                    direction=det.direction,
                    cross_line=det.cross_line,
                    x1_coords=det.x1_coords,
                    y1_coords=det.y1_coords,
                    x2_coords=det.x2_coords,
                    y2_coords=det.y2_coords,
                    frame_number=det.frame_number,
                    image_path=final_image_path,
                    project_id=det.project_id,
                    line_id=det.line_id,
                    camera_ip=det.camera_ip,
                    ai_class=det.ai_class,
                    audited_class=det.audited_class,
                    is_audit=det.is_audit,
                    detection_id=det.detection_id,
                    last_modified=det.last_modified,
                    mapped_line=det.mapped_line
                )

                db.add(new_detection)
                saved_detections.append(new_detection)

        db.commit()
        return {"status": "success", "message": f"{len(saved_detections)} new detections saved successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing detections: {str(e)}")


#############################       Cloud_status update    ############################################################################3


@router.post("/main/start")
async def cloud_status_update(request: Request):
    try:
        db=next(get_db())

        data = await request.json()
        project_id = data.get("project_id")
        camera_ip = data.get("camera_ip")
        line = data.get("line")
        polygon=data.get("polygon")
        selected=data.get('selected')
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        lpu_id= session_data['lpu_id']

        active_status= db.query(Lpu_management).filter(Lpu_management.lpu_id == lpu_id).first()

        if active_status and not active_status.lpu_status:
            raise HTTPException(status_code=403, detail="Kit is offline")

        if not project_id or not camera_ip:
            raise HTTPException(status_code=400, detail="Missing required parameters")

        print("line value:", line,"selected:",selected)
        print("data:", data)

        cloud_status_update = db.query(Project).filter(Project.project_id == project_id).first()
        if cloud_status_update:
            cloud_status_update.cloud_status = True
            cloud_status_update.updated_at = datetime.now(timezone.utc)
            cloud_status_update.updated_status = True
            cloud_status_update.mapped_value=selected
            db.commit()
            return {"success": True, "message": "Detection started successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")

    except HTTPException as e:
        db.rollback()
        return {"success": False, "message": str(e.detail)}
    except Exception as e:
        db.rollback()
        print("Error in cloud_status_update:", str(e))
        return {"success": False, "message": "Internal server error"}



@router.post("/stop_cloud")
async def cloud_stop_status(request: Request):
    try:

        db=next(get_db())
        data = await request.json()
        project_id = data.get("project_id")
        camera_ip = data.get("camera_ip")

        if not project_id or not camera_ip:
            raise HTTPException(status_code=400, detail="Missing required parameters")


        cloud_status_update = db.query(Project).filter(Project.project_id == project_id).first()
        if cloud_status_update:
            cloud_status_update.cloud_status = False
            cloud_status_update.updated_at = datetime.now(timezone.utc)
            cloud_status_update.updated_status = True
            db.commit()
            return {"success": True, "message": "Detection stopped successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")

    except HTTPException as e:
        db.rollback()
        return {"success": False, "message": str(e.detail)}
    except Exception as e:
        db.rollback()
        print("Error in cloud_stop_status:", str(e))
        return {"success": False, "message": "Internal server error"}



######################################3 POLYGON DATA SYNC ###########################################################################


class RoiDetection(BaseModel):
    id: int
    date_time: Optional[str]
    vehicle_id: int
    vehicle_class_id: int
    vehicle_name: str
    direction: str
    image_path: str
    project_id: int
    camera_ip: str
    ai_class: str
    detection_id: int
    mapped_polygon: str
    upload_status: Optional[bool] = False
    image_base64: Optional[str]

class RoiDetectionList(BaseModel):
    detections: List[RoiDetection]

@router.post("/roi_data")
def receive_detections(roi_data: RoiDetectionList):
    print("ROI DETECTIONS...")
    try:
        db = next(get_db())
        saved_detections = []

        for det in roi_data.detections:
            print("$%#%$^$%^")
            image_path = det.image_path
            print("image_path in roi:",image_path)

            if image_path and "/files/" in image_path:
                print("###########################################")
                relative_path = image_path.split("/files/", 1)[-1]
                final_directory = os.path.join(SAVE_DIRECTORY, os.path.dirname(relative_path))
                filename = os.path.basename(relative_path)
                print("$$$$$$$$$$$ final directory:",final_directory)
                os.makedirs(final_directory, exist_ok=True)
                final_image_path = os.path.join(final_directory, filename)
                print("final_image_path",final_image_path)

                # Save image from base64
                if det.image_base64:
                    try:
                        with open(final_image_path, "wb") as img_file:
                            print("%$#%$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                            img_file.write(base64.b64decode(det.image_base64))
                    except Exception as e:
                        print(f"Error saving image: {e}")
                        continue

                # 🔍 Check for duplicates in roi_detection
                existing = db.query(Roi_detection).filter_by(
                    detection_id=det.detection_id,
                    project_id=det.project_id,
                    camera_ip=det.camera_ip,
                    date_time=det.date_time
                ).first()

                if existing:
                    print(f"Duplicate detection found: {det.detection_id}, skipping...")
                    continue

                # ✅ Insert new record into roi_detection
                new_detection = Roi_detection(
                    id=det.id,
                    date_time=det.date_time,
                    vehicle_id=det.vehicle_id,
                    vehicle_class_id=det.vehicle_class_id,
                    vehicle_name=det.vehicle_name,
                    direction=det.direction,
                    image_path=final_image_path,
                    project_id=det.project_id,
                    camera_ip=det.camera_ip,
                    ai_class=det.ai_class,
                    detection_id=det.detection_id,
                    mapped_polygon=det.mapped_polygon
                    
                )

                db.add(new_detection)
                saved_detections.append(new_detection)

        db.commit()
        return {"status": "success", "message": f"{len(saved_detections)} new detections saved successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing detections: {str(e)}")

    

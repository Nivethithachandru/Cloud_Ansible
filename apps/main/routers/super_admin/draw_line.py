import json
from typing import Optional
from fastapi import APIRouter ,Request,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from fastapi_utilities import repeat_every
from sqlalchemy import or_, update
import asyncio
from sqlalchemy import text
from apps.main.config import folder
from apps.main.routers.super_admin.kit import mail_trigger
from apps.main.utils.local_vendor import *
from apps.main.database.db import get_db
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
import base64
from apps.main.utils.jwt import *
from apps.main.routers.roles.auth_role import *
import base64
import cv2


router=APIRouter()

templates = Jinja2Templates(directory="apps/main/front_end/templates")

@router.get("/main/draw_line/",response_class=HTMLResponse,name="main.draw_line")
async def get_frame(request:Request):
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        role_id = session_data.get('role_id')
        db = next(get_db())   
        modulee_id = 7
        show_required_permission = "show" 
        
        show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
        print("show_required_permission",show_required_permission)
        if role_id == 0:

            required_permission_s = True
            edit_required_permission_s = True
            delete_required_permission_s = True

            return templates.TemplateResponse("super_admin/project/project_table.html", 
                                            {"request": request, 
                                            'page_permission':required_permission_s,
                                                'edit_permission' :edit_required_permission_s,
                                                'delete_permission' :delete_required_permission_s,                                        
                                            "session": session_data}
                                            )
        
            
        
        else:
            if show_required_permission:
                required_permission= "read"
                required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
                print("required_permission",required_permission)


                edit_required_permission= "update"
                edit_required_permission = await has_permission_bool(db, role_id, modulee_id, edit_required_permission)
                print("edit_required_permission",edit_required_permission)



                delete_required_permission= "delete"
                delete_required_permission = await has_permission_bool(db, role_id, modulee_id, delete_required_permission)
                print("delete_required_permission",delete_required_permission)
            else:
                print("Unautorize user")
                error_page = templates.get_template("error_page.html")
                content = error_page.render({"request": request})
                
                return HTMLResponse(content=content, status_code=403)
            return templates.TemplateResponse("super_admin/project/project_table.html",
                                                {'request': request,
                                                    'page_permission':required_permission,
                                                    'edit_permission' :edit_required_permission,
                                                    'delete_permission' :delete_required_permission,
                                                    "session": session_data})



@router.get("/main/drawline/frame/{project_id}/{camera_ip}")
def drawline_update(request: Request, project_id: int, camera_ip: str):
    db = next(get_db())
    print("project_id:",project_id)
    print("camera_ip:",camera_ip)

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

   
    all_camera_ip = [camera.camera_ip for camera in db.query(LpuGroup.camera_ip).distinct().all()]
    print("@$%#@%#$^$%^$%&",all_camera_ip)


    detection_status_list = [
        {
            'camera_ip': detection.camera_ip,
            'status': detection.camera_status,
            'line_crossing': detection.line_crossing,
        }
        for detection in db.query(Detection_details).filter(Detection_details.camera_status == True).all()
    ]

    print("detection_status_list", detection_status_list)

   
    context = {
        'request': request,
        "session": session_data,
        'camera_details': all_camera_ip,
        'detection_status': detection_status_list,
        'project_id': project_id,  
        'camera_ip': camera_ip,   
    }

    
    return templates.TemplateResponse("super_admin/draw_line/draw_line.html", context)






@router.get("/getframe/{camera_ip}/{project_id}")
def getcurrent_frame(request:Request,camera_ip: str, project_id: str):
    print("Getting a frame . . .", camera_ip, project_id)
    save_filename = camera_ip + '_frame.jpg'
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    1
    lpu_id=session_data['lpu_id']
    print("lpu_id:",lpu_id)

    db = next(get_db())
    existing_camera = db.query(LpuGroup).filter(LpuGroup.camera_ip == camera_ip,LpuGroup.lpu_id ==lpu_id).first()
    print("#@%%#$%% camera ip:",camera_ip,existing_camera)
    
    if existing_camera:
        camera_ip = existing_camera.camera_ip
        camera_username = existing_camera.camera_username
        camera_password = existing_camera.camera_password
        camera_port = existing_camera.camera_port
        camera_live_status = existing_camera.camera_status
        print("camera_live_status:",camera_live_status)

        existing_detection = db.query(Detection_details).filter(Detection_details.camera_ip == camera_ip, Detection_details.project_id == project_id,Detection_details.lpu_id == lpu_id).first()
        
        if existing_detection:
            line_crossing_data = existing_detection.line_crossing

            if line_crossing_data:
                if isinstance(line_crossing_data, str):
                    line_dictall = json.loads(line_crossing_data)
                elif isinstance(line_crossing_data, dict):
                    line_dictall = line_crossing_data
                    print("line:", line_dictall)
                else:
                    line_dictall = None
                    print("Error: line_crossing_data is neither a string nor a dictionary.")
           
                line_dictall = {
                    "first": {
                        "topx_1": line_dictall.get("line_id_1", {}).get("topx", 'null'),
                        "topy_1": line_dictall.get("line_id_1", {}).get("topy", 'null'),
                        "bottomx_1": line_dictall.get("line_id_1", {}).get("bottomx", 'null'),
                        "bottomy_1": line_dictall.get("line_id_1", {}).get("bottomy", 'null'),
                        "direction_1": line_dictall.get("line_id_1", {}).get("direction", '0')
                    },
                    "second": {
                        "topx_2": line_dictall.get("line_id_2", {}).get("topx", 'null'),
                        "topy_2": line_dictall.get("line_id_2", {}).get("topy", 'null'),
                        "bottomx_2": line_dictall.get("line_id_2", {}).get("bottomx", 'null'),
                        "bottomy_2": line_dictall.get("line_id_2", {}).get("bottomy", 'null'),
                        "direction_2": line_dictall.get("line_id_2", {}).get("direction", '0')
                    },
                    "third": {
                        "topx_3": line_dictall.get("line_id_3", {}).get("topx", 'null'),
                        "topy_3": line_dictall.get("line_id_3", {}).get("topy", 'null'),
                        "bottomx_3": line_dictall.get("line_id_3", {}).get("bottomx", 'null'),
                        "bottomy_3": line_dictall.get("line_id_3", {}).get("bottomy", 'null'),
                        "direction_3": line_dictall.get("line_id_3", {}).get("direction", '0')
                    }
                }
                print("dictall:", line_dictall)

                detection_active_status = True
            else:
                line_dictall = None
                detection_active_status = False
        else:
            line_dictall = None
            detection_active_status = True

        # print("###########################################################################################")

        roimapping_records = db.query(ROIMapping).filter(ROIMapping.camera_ip == camera_ip).all()
        all_lineids = []
        if roimapping_records:
            for record in roimapping_records:
                lineid_list = record.lineid
                print("dfdf:", lineid_list)
                all_lineids.append(lineid_list)
            mapping_lineids = list(set(all_lineids))
        else:
            mapping_lineids = []

        current_camera_detection_details = []
        data = {
            'camera_ip': camera_ip,
            'mapping_lineids': mapping_lineids,
            'detection_active_status': detection_active_status,
        }

        current_camera_detection_details.append(data)
        print("Current camera detection detail getting for getframe:", current_camera_detection_details)

        if camera_live_status:
     
            rtsp_link = f"rtsp://{camera_username}:{camera_password}@{camera_ip}:{camera_port}"
            print("rtsp:", rtsp_link)
            roi_frame_path = os.path.join('uploads', save_filename)  
            print("roi_frame:#########", roi_frame_path)          
            with open(roi_frame_path, "rb") as image_file:
                image_bytes = image_file.read()
            frame_base64 = base64.b64encode(image_bytes)

            if line_dictall is None:
                print("#@@#$@$$#%$^$")
                line_length = [0]
                
            else:
                print("line dictall:", line_dictall)
                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                line_length = []
                

             
            invalid_lines = [] 

            if isinstance(line_dictall, dict):
                for line_key, line_data in line_dictall.items(): 
                    for key, value in line_data.items():  
                        if 'topx' in key and (value is None or value == 'null' or value == ''):
                            line_id = int(key.split('_')[1])
                            invalid_lines.append(line_id)
                            print("Invalid topx value for line_id:", line_id)
                            print("Invalid lines:", invalid_lines)


            if 3 in invalid_lines:
                line_length = [3]
            elif len(invalid_lines) == 0:
                line_length = []  
            else:
                line_length = invalid_lines  

            print("null_topx_line_ids", line_length)
               
            
            

            

            # print("null_topx_line_ids", line_length)


            data = {
                "camera_ip": camera_ip,
                "rtsp_url": rtsp_link,       
                "line_dictall": line_dictall,
                "frame_baseurl": frame_base64,
                "line_length": line_length,  
                "camera_live_status": camera_live_status,
                "current_camera_detection_details": current_camera_detection_details,
                
            }
            # print("frd:::",data)

            return {"message": "success", "data": data}
        else:
            return {"message": "error", "data": {}, "error": "Camera not found"}
    else:
        raise HTTPException(status_code=404, detail="Camera not found")





def capture_frame(camera):
    try:
        print("!%#####")
        camera_ip = camera.camera_ip
        username = camera.camera_username
        password = camera.camera_password
        camera_status = camera.camera_status

        if camera_status:
            camera_port = 554
            rtsp_link = f"rtsp://{username}:{password}@{camera_ip}:{camera_port}"
            print("Connecting to RTSP stream:", rtsp_link)
            
            cap = cv2.VideoCapture(rtsp_link)
            if not cap.isOpened():
                print(f"[RTSP Error]: Could not open RTSP stream at {rtsp_link}")
                return

            ret, frame = cap.read()
            cap.release()
            
            if ret:
                save_filename = f'{camera_ip}_frame.jpg'
                save_path = os.path.join(folder,'draw_line', save_filename)
                print("save_path:",save_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                cv2.imwrite(save_path, frame)
                print(f"[DRAW ROI - IMAGE SAVED] ------ Active Camera First frame Storing {save_path}")                 

            else:
                print("[RTSP Error]: Failed to capture frame from RTSP stream.")
    
    except Exception as e:
        print(f"Exception occurred while processing {camera_ip}: {e}")


async def camera_firstframe_snap():
    try:
        db=next(get_db())
        all_camera_list = db.query(LpuGroup).all()
        print("askjagdsjL:",all_camera_list)
        
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, capture_frame, camera)
                for camera in all_camera_list
            ]

            print("camera_list:", all_camera_list)
            await asyncio.gather(*tasks)

    except Exception as e:
        print(f"Exception occurred in camera_firstframe_snap: {e}")




@router.put("/update_roi/{camera_ip}")
async def update_database(request:Request,camera_ip: str, data: dict = None):
    print("Value to update", data)
    print("-------------------------------------------")
    print("--------------------------------------------")
    print("----------------------------------------------")
    print("mapped_roi_checked", data.get("mapped_roi_checked"))
    roi_line_id = data.get("mapped_roi_checked")

    line_id_str = ','.join(roi_line_id) if isinstance(roi_line_id, list) else (roi_line_id or "")
    print("line_id_str:", line_id_str)





    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    lpu_id=session_data['lpu_id']
    if error_response:
        return RedirectResponse(url="/")

    
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    db = next(get_db())
    

    lpu_id=session_data['lpu_id']

    lpu_record = db.query(Lpu_management).filter(
            Lpu_management.lpu_id == lpu_id, 
            Lpu_management.lpu_status == False  
        ).all()

    print("lpu_records:",lpu_record)

    if lpu_record:
        raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update Drawline coordinates -LPU ID '{id}'.")
    
    project_id = data.get("project_id")
    print("project_id", project_id)
    
    if not project_id:
        raise HTTPException(status_code=400, detail="Project ID is required")
   
    

    print("db_session:", db)
    print("camera_ip:", camera_ip)
    print("project_id:", project_id)
 
    print("Updating the Response ROI", data)


    existing_mapping = db.query(ROIMapping).filter(
        ROIMapping.project_id == project_id,
        ROIMapping.camera_ip == camera_ip,
    ).first()


    if existing_mapping:
        existing_mapping.lineid = line_id_str
        existing_mapping.updated_status = True
        existing_mapping.datetime=datetime.now()
        db.commit()
        db.refresh(existing_mapping)
    else:
        new_mapping = ROIMapping(
            camera_ip=camera_ip,
            project_id=project_id,
            lineid=line_id_str,
            polygon=None,
            updated_status=True,
            datetime=datetime.now()
        )
        db.add(new_mapping)
        db.commit()
        db.refresh(new_mapping)

    

   
    id_value_pairs = data.get('idValuePairs', {})
    if not id_value_pairs:
        raise HTTPException(status_code=400, detail="No idValuePairs provided")


    
    line_crossing = {}

    
    for key, value in id_value_pairs.items():
        line_id = value.get("line_id")
        if not line_id:
            continue

        line_data = {}

        for i in range(1, 4):
            topx_key = f"topx_{i}"
            bottomx_key = f"bottomx_{i}"
            topy_key = f"topy_{i}"
            bottomy_key = f"bottomy_{i}"
            direction_key = f"direction_{i}"

            if f"topx_{line_id}" in value and value[f"topx_{line_id}"] != 'null':
                line_data['topx'] = value.get(f"topx_{line_id}")
            else:
                line_data['topx'] = None

            if f"bottomx_{line_id}" in value and value[f"bottomx_{line_id}"] != 'null':
                line_data['bottomx'] = value.get(f"bottomx_{line_id}")
            else:
                line_data['bottomx'] = None

            if f"topy_{line_id}" in value and value[f"topy_{line_id}"] != 'null':
                line_data['topy'] = value.get(f"topy_{line_id}")
            else:
                line_data['topy'] = None

            if f"bottomy_{line_id}" in value and value[f"bottomy_{line_id}"] != 'null':
                line_data['bottomy'] = value.get(f"bottomy_{line_id}")
            else:
                line_data['bottomy'] = None

            
            if f"direction_{line_id}" in value and value[f"direction_{line_id}"] != 'null' and value[f"direction_{line_id}"] != '':
                line_data['direction'] = value.get(f"direction_{line_id}")
            else:
                if line_id == 1:
                    line_data['direction'] = 1
                elif line_id == 2:
                    line_data['direction'] = 0
                elif line_id == 3:
                    line_data['direction'] = 2


        line_crossing[f"line_id_{line_id}"] = line_data


    print("line_crossing to be applied:", line_crossing)

   
    
    stmt = update(Detection_details).where(Detection_details.project_id == project_id,Detection_details.camera_ip == camera_ip,Detection_details.lpu_id == lpu_id).values(line_crossing=line_crossing,updated_status=True)
    print("Generated SQL Update Statement:", stmt)

    try:
        result = db.execute(stmt)
        db.commit()
       
        print("Update executed successfully")
    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    if result.rowcount == 1:

        return {"message": "line_crossing updated successfully", "status_code": 1}
    else:
        return {"message": "Failed to update line_crossing", "status_code": 0}


class ImageRequest(BaseModel):
    frameImage: str  
    project_id: int   
    camera_ip: str


@router.post("/main/save_frame_image")
async def save_frame_image(request: ImageRequest):
    try:
        print("HHH")
      
        frame_image = request.frameImage
        project_id = str(request.project_id)
        camera_ip=request.camera_ip
        print("Requested details:",project_id,camera_ip)

        
        if frame_image.startswith("data:image/jpeg;base64,"):
            print("$#%$^")
            frame_image = frame_image.replace("data:image/jpeg;base64,", "")
            print("frame_image")
        elif frame_image.startswith("data:image/png;base64,"):
            print("5467")
            frame_image = frame_image.replace("data:image/png;base64,", "")
        else:
            raise HTTPException(status_code=400, detail="Invalid image format.")

        image_data = base64.b64decode(frame_image)
        file_name = f"{camera_ip}_project_id_{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

        directory = os.path.join(folder,"updated_frames", project_id, camera_ip)
     
        os.makedirs(directory, exist_ok=True)

        for existing_file in os.listdir(directory):
            existing_file_path = os.path.join(directory, existing_file)
            if os.path.isfile(existing_file_path): 
            
                os.remove(existing_file_path)
                
        file_path = os.path.join(directory, file_name)
      


        with open(file_path, "wb") as img_file:
            img_file.write(image_data)

    
        return {"status_code": 1, "message": "Image saved successfully.", "file_path": file_path}

    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")


@router.get('/draw_line/camera_ip/{project_id}', response_class=JSONResponse)
async def get_camera_ip(project_id: str):
    try:
        db_session = next(get_db())
        print("project_id:", project_id)

        result = db_session.execute(
            text('SELECT camera_ip FROM detection_details WHERE project_id = :project_id'),
            {'project_id': project_id}
        ).fetchall()

        camera_ips = []
        for row in result:
            ip_data = row[0]
            if isinstance(ip_data, str):
                try:
                    parsed_ips = json.loads(ip_data)
                    if isinstance(parsed_ips, list):
                        camera_ips.extend(parsed_ips)
                    else:
                        camera_ips.append(parsed_ips)
                except json.JSONDecodeError:
                    camera_ips.append(ip_data)
            elif isinstance(ip_data, list):
                camera_ips.extend(ip_data)

      
        camera_ips = list(set(camera_ips))
        print("camera_ip:####:", camera_ips)

        if camera_ips:
            
            if len(camera_ips) == 1:
                return {"camera_ip": camera_ips[0]}  
            else:
                return {"camera_ip_up": camera_ips[0], "camera_ip_down": camera_ips[1] if len(camera_ips) > 1 else None}
        else:
            raise HTTPException(status_code=404, detail="Camera not found")
    except Exception as e:
        print(f"Error fetching camera status: {e}")
        raise HTTPException(status_code=500, detail="Error fetching camera status") from e
    finally:
        db_session.close()


########################################## CLOUD TO KIT API CALL ##################################################################### 



########################################## CAMERA FRAME SAVE API ####################################################################################################

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class ImageUpload(BaseModel):
    camera_ip: str
    image_data: str

@router.post("/upload")
async def upload_file(data: ImageUpload):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, f"{data.camera_ip}_frame.jpg")
        with open(file_path, "wb") as buffer:
            buffer.write(base64.b64decode(data.image_data))
            
        


        response_data = {
            "message": "File uploaded successfully",
            "filename": f"{data.camera_ip}_frame.jpg",
            "path": file_path,
            
        }

        return response_data

    except Exception as e:
        print("Exception occurred:", str(e))
        return {"error": str(e)}
    




###################################### DASHBOARD DATA - KIT DATA API #############################################################



class KitDataSchema(BaseModel):
    lpu_id: int
    total_disk_gb: float
    used_disk_gb: float
    free_disk_gb: float
    cpu_core: int
    kit_fan_speed: int
    cpu_temperature: float
    gpu_temperature: Optional[float]
    gpu_usage: Optional[float]
    cpu_percentage_usage: float
    ram_percentage_usage: float
    system_uptime: str
    total_ram_gb: float
    used_ram_gb: float
    kit_time: datetime
    camera_status: bool
    storage_status: bool
    temp_status: bool
    # download_speed: float
    # upload_speed: float
    # camera_fps: float
    download_speed: Optional[float] = 0.0
    upload_speed: Optional[float] = 0.0
    camera_fps: Optional[float] = 0.0


@router.post("/kit_data")
async def insert_or_update_kit_data(request: Request):
    body = await request.json()
    print("Received $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$Request Data:", body)

    if isinstance(body, dict):  
        body = [body] 
    
    if not isinstance(body, list):
        raise HTTPException(status_code=400, detail="Invalid input: Expected a list or object.")
     

    try:
        db = next(get_db())

        updated_kits = []
        new_kits = []
        received_lpu_ids = set()


        for item in body:
            api_lpu_id = item.get("lpu_id")

            kit_data = KitDataSchema(**item)  
            received_lpu_ids.add(kit_data.lpu_id) 
            print("recieved lpu id:",received_lpu_ids)

 
            existing_kit = db.query(KitMonitoring).filter(KitMonitoring.lpu_id == kit_data.lpu_id).first()

            print("recieved lpu ids:",received_lpu_ids)

            if existing_kit:
                print("@#$@#$@#$@#$@$@#$#@$")
                existing_kit.total_disk_gb = kit_data.total_disk_gb
                existing_kit.used_disk_gb = kit_data.used_disk_gb
                existing_kit.free_disk_gb = kit_data.free_disk_gb
                existing_kit.cpu_core = kit_data.cpu_core
                existing_kit.kit_fan_speed = kit_data.kit_fan_speed
                existing_kit.cpu_temperature = kit_data.cpu_temperature
                existing_kit.gpu_temperature = kit_data.gpu_temperature
                existing_kit.gpu_usage = kit_data.gpu_usage
                existing_kit.cpu_percentage_usage = kit_data.cpu_percentage_usage
                existing_kit.ram_percentage_usage = kit_data.ram_percentage_usage
                existing_kit.system_uptime = kit_data.system_uptime
                existing_kit.total_ram_gb = kit_data.total_ram_gb
                existing_kit.used_ram_gb = kit_data.used_ram_gb
                existing_kit.kit_time = kit_data.kit_time
                existing_kit.camera_status = kit_data.camera_status
                existing_kit.storage_status = kit_data.storage_status
                existing_kit.temp_status = kit_data.temp_status
                existing_kit.updated_at = datetime.utcnow()

                # existing_kit.download_speed = kit_data.download_speed
                # existing_kit.upload_speed = kit_data.upload_speed

                existing_kit.download_speed = kit_data.download_speed if kit_data.download_speed is not None else 0.00
                existing_kit.upload_speed = kit_data.upload_speed if kit_data.upload_speed is not None else 0.00

                existing_kit.camera_fps = kit_data.camera_fps if kit_data.camera_fps is not None else 0.00


                updated_kits.append(existing_kit)
            else:
                print("1111111111111111111111111111111111111111111111111111111111123123123123")
                new_kit = KitMonitoring(
                    lpu_id=kit_data.lpu_id,
                    total_disk_gb=kit_data.total_disk_gb,
                    used_disk_gb=kit_data.used_disk_gb,
                    free_disk_gb=kit_data.free_disk_gb,
                    cpu_core=kit_data.cpu_core,
                    kit_fan_speed=kit_data.kit_fan_speed,
                    cpu_temperature=kit_data.cpu_temperature,
                    gpu_temperature=kit_data.gpu_temperature,
                    gpu_usage=kit_data.gpu_usage,
                    cpu_percentage_usage=kit_data.cpu_percentage_usage,
                    ram_percentage_usage=kit_data.ram_percentage_usage,
                    system_uptime=kit_data.system_uptime,
                    total_ram_gb=kit_data.total_ram_gb,
                    used_ram_gb=kit_data.used_ram_gb,
                    kit_time=kit_data.kit_time,
                    camera_status=kit_data.camera_status,
                    storage_status=kit_data.storage_status,
                    temp_status=kit_data.temp_status,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    # download_speed=kit_data.download_speed,
                    # upload_speed=kit_data.upload_speed,
                    download_speed=kit_data.download_speed if kit_data.download_speed is not None else 0.00,
                    upload_speed=kit_data.upload_speed if kit_data.upload_speed is not None else 0.00,

                    camera_fps=kit_data.camera_fps if kit_data.camera_fps is not None else 0.00
                )

                db.add(new_kit)
                new_kits.append(new_kit)

        db.commit()

   

        for kit in updated_kits:
            db.refresh(kit)
        for kit in new_kits:
            db.refresh(kit)

        
        # TO UPDATE THE LPU_ACTIVE STATUS AND UPDATED_AT TIME 

        db.query(Lpu_management).filter(Lpu_management.lpu_id.in_(received_lpu_ids)).update({Lpu_management.lpu_status: True,Lpu_management.updated_at:datetime.now()}) 
       


        db.commit()


        lpu_records = db.query(LpuGroup).filter(LpuGroup.lpu_id.in_(received_lpu_ids),LpuGroup.updated_status ==True).all()
        lpu_data = [
            {
                "id": lpu.id,
                "lpu_id": lpu.lpu_id,
                "lpu_name": lpu.lpu_name,
                "lpu_ip": lpu.lpu_ip,
                "camera_ip": lpu.camera_ip,
                "camera_name": lpu.camera_name,
                "camera_port": lpu.camera_port,
                "camera_username": lpu.camera_username,
                "camera_password": lpu.camera_password,
                "camera_status": lpu.camera_status,
                "kit_status": lpu.kit_status,
                "lpu_status":lpu.lpu_status,
                "camera_id":lpu.camera_id
            }
            for lpu in lpu_records
        ]

        print("lpu_data:",lpu_data)


        org_records=db.query(Lpu_management).filter(Lpu_management.lpu_id.in_(received_lpu_ids),Lpu_management.updated_status ==True).all()

        org_data= [
            {
                "id":org.id,
                "org_name":org.org_name,
                "lpu_id":org.lpu_id,
                "lpu_ip":org.lpu_ip,
                "device_id":org.lpu_serial_num,
                "lpu_name":org.lpu_name,
                "lpu_status":org.lpu_status,
                "updated_status":org.updated_status,
               
                
            }for org in org_records
        ]

        if isinstance(api_lpu_id, int):  
            api_lpu_id = [api_lpu_id]  # Convert to a list

        project_record = db.query(Project).filter(Project.lpu_id.in_(api_lpu_id)).all()
        print(project_record)

        # Convert project_record list to JSON-serializable format
        project_record_data = [
            {
                "cloud_status": demo.cloud_status,
                "updated_status": demo.updated_status,
                "lpu_id": demo.lpu_id,
                "project_id": demo.project_id
            }
            for demo in project_record
        ]
      

        response_data= {
            "message": "Kit data processed successfully",
            "updated_kit_ids": [kit.id for kit in updated_kits],
            "new_kit_ids": [kit.id for kit in new_kits],
            "lpu_data": lpu_data if lpu_data else None,
            "org_data":org_data if org_data else None,
            "detectionstatus":project_record_data
            
        }
        db.query(LpuGroup).filter(LpuGroup.updated_status == True).update({"updated_status": False})
        db.query(Lpu_management).filter(Lpu_management.updated_status == True).update({"updated_status": False})
        db.commit()

        return response_data
        

    except Exception as e:
        # db.rollback()
        print(f"Error processing data: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")
    


##########################################    LPU DATA STATUS CHECK  ######################################################################

class Lpupdate(BaseModel):
    statuses: dict  

lpu_status = {
 
    "statuses": {
        "lpu_status": False,
       
    }
}

@router.post("/lpu_status")
async def lpu_status_update(update: Lpupdate):
    try:
        global lpu_status  
      
        lpu_status["statuses"] = update.statuses 

        print("statuses:", update.statuses)

        return {"received": {"message": "Received db response"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lpu_status_info")
async def get_status_update():
    try:
        return {"latest_status": lpu_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




########################################## KIT ACTIVE /INACTIVE STATUS UPDATE FOR EVERY 30 SECS #####################################################

@router.on_event("startup")
@repeat_every(seconds=30)
async def check_active():
    db = next(get_db())
    print("Checking LPU status and sending alerts...")

    update_time_check = datetime.now() - timedelta(minutes=1)

    db.query(Lpu_management).filter(
        Lpu_management.lpu_status == True,
        or_(Lpu_management.updated_at < update_time_check, Lpu_management.updated_at == None)
    ).update({Lpu_management.lpu_status: False})

    db.commit()

    lpus = db.query(Lpu_management, settings).join(
        settings, Lpu_management.lpu_id == settings.lpu_id
    ).all()

    for lpu, alert in lpus:
        #If kit is online  and mail_status is False 
        if lpu.lpu_status == True and  alert.last_mail_status != "online":
            print(f"Sending ONLINE mail for LPU ID {lpu.lpu_id}")
            # await mail_trigger()
            # db.query(settings).filter(settings.lpu_id == lpu.lpu_id).update({"last_mail_status": "online"})

        # If kit is offline  and mail_status is True 
        elif lpu.lpu_status == False and alert.last_mail_status != "offline":
            print(f"Sending OFFLINE mail for LPU ID {lpu.lpu_id}")
            # await mail_trigger()
            # db.query(settings).filter(settings.lpu_id == lpu.lpu_id).update({"last_mail_status": "offline"})


        

    db.commit()
    print("Mail processing completed.")

   


################################################# CLOUD DATA SENT API ###################################################################
from typing import List

class CloudDataRequest(BaseModel):
    lpu_id: List[int] 


@router.post("/clouddata")
async def cloud_data(request: CloudDataRequest):
    db = next(get_db())

    
    print("kishoreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    print("kishoreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    print("kishoreeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    print("*********RRR",request)

    if request.lpu_id:
        active_lpu_ids = int(request.lpu_id[0])
    else:
        active_lpu_ids = None          
        print("No active LPU IDs received.")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Active LPU IDs:", active_lpu_ids)
 
    print("Active LPU IDs:", active_lpu_ids)
    try:
          # if updated_status =True, then it will send the data

        org_records=db.query(Lpu_management).filter(Lpu_management.updated_status == True, Lpu_management.lpu_id == active_lpu_ids).all()  
        org_data= [
            {
                "id":org.id,
                "org_name":org.org_name,
                "lpu_id":org.lpu_id,
                "lpu_ip":org.lpu_ip,
                "device_id":org.lpu_serial_num,
                "lpu_name":org.lpu_name,
                "lpu_status":org.lpu_status
                
            }for org in org_records
        ]
        print("org data:",org_data)
        print("$#############################################")


        project_details = db.query(Project).filter(Project.updated_status == True,Project.lpu_id ==active_lpu_ids).all()
        project_data = [
            {
                "id": project.id,
                "project_id": project.project_id,
                "project_name": project.project_name,
                "camera_ip": project.camera_ip,
                "camera_status": project.camera_status,
                "analytics": project.analytics,
                'lpu_id':project.lpu_id,
                'updated_at' : project.updated_at,
                'created_at' : project.created_at,
                'cloud_status':project.cloud_status,
                'mapped_value':project.mapped_value
            }
            for project in project_details
        ]

        print("project_details:",project_data)

        print("$#############################################")

     
        custom_classes = db.query(CustomClasses).filter(CustomClasses.updated_status == True,CustomClasses.lpu_id==active_lpu_ids).all()
        custom_data = []
        for custom in custom_classes:
            custom_data.append(
                {
                    "id": custom.id,
                    "custom_class": custom.custom_class,
                    "created_at": custom.created_at,
                    "updated_at": custom.updated_at,
                    'lpu_id':custom.lpu_id
                }
            )
        print("&&&&&&&&&&&&&&&&&&&&&&sdfgsdfgsdgsdfgcustom",custom_data)
        mappings_data = db.query(MappingCustomClasses).filter(MappingCustomClasses.updated_status == True,MappingCustomClasses.lpu_id==active_lpu_ids).all()
        mapping_data = []
        for mapping in mappings_data:
                
            mapping_data.append({
                    "id": mapping.id,
                    "custom_class_id": mapping.custom_class_id,
                    "model_class_id": mapping.model_class_id,
                    "created_at": mapping.created_at,
                    'lpu_id':mapping.lpu_id
                })

        print("$#############################################")
        print("mapping data:",mapping_data)
        print("$#############################################")


        roi_records = db.query(ROIMapping).filter(ROIMapping.updated_status == True).all()
        roi_details = [
            {
                "id": roi.id,
                "camera_ip": roi.camera_ip,
                "line_id": roi.lineid,
                "project_id": roi.project_id,
                "datetime": roi.datetime,
                "polygon":roi.polygon
            }
            for roi in roi_records
        ]

        print("roi details:",roi_details)

        polygon_records = db.query(Polygon_details).filter(Polygon_details.updated_status == True).all()
        print("Updated statuses:", [record.updated_status for record in polygon_records])  

        polygon_details = [
            {
                "id": poly.id,
                "camera_ip": poly.camera_ip,
                "coordinates": poly.coordinates,
                "project_id": poly.project_id,
                "lpu_id": poly.lpu_id,
            }
            for poly in polygon_records
        ]

        print("polygon_details:", polygon_details)



     
        detection_records = db.query(Detection_details).filter(Detection_details.updated_status == True,Detection_details.lpu_id==active_lpu_ids).all()
        detection_data = []
        for record in detection_records:
            line_crossing_data = record.line_crossing

            if isinstance(line_crossing_data, str):
                line_crossing_data = json.loads(line_crossing_data)

            formatted_line_crossing = {
                key: {
                    "topx": str(value["topx"]) if value["topx"] is not None else "",
                    "bottomx": str(value["bottomx"]) if value["bottomx"] is not None else "",
                    "topy": str(value["topy"]) if value["topy"] is not None else "",
                    "bottomy": str(value["bottomy"]) if value["bottomy"] is not None else "",
                    "direction": str(value["direction"]) if value["direction"] is not None else "0",
                }
                for key, value in line_crossing_data.items()
            }

            detection_data.append(
                {
                    "id": record.id,
                    "project_id": record.project_id,
                    "camera_status": str(record.camera_status).lower(),
                    "camera_ip": record.camera_ip,
                    "line_crossing": formatted_line_crossing,
                    "updated_status": record.updated_status,
                }
            )

        print("drawline data:",detection_data)

        print("$#############################################")

        response_data = {
            "message": "message recieved successfully",
            "detection_data": detection_data,
            "project_data": project_data,
            "roi_details": roi_details,
            "custom_data": custom_data,
            "mapping_data":mapping_data,
        
            "org_data":org_data,
            "polygon_data":polygon_details
        }

   
       # after defining the response data , update the Updated status to FALSE
       
        db.query(Project).filter(Project.updated_status == True).update({"updated_status": False})
        
        
        db.query(ROIMapping).filter(ROIMapping.updated_status == True).update({"updated_status": False})
        
        db.query(Lpu_management).filter(Lpu_management.updated_status == True).update({"updated_status": False})
        
        db.query(Detection_details).filter(Detection_details.updated_status == True).update({"updated_status": False})
        
        db.query(CustomClasses).filter(CustomClasses.updated_status == True).update({"updated_status": False})
        
        db.query(MappingCustomClasses).filter(MappingCustomClasses.updated_status == True).update({"updated_status": False})
        db.query(Polygon_details).filter(Polygon_details.updated_status == True).update({"updated_status": False})

        db.commit()

        return response_data

    except Exception as e:
        print("Exception occurred:", str(e))
        return {"error": str(e)}



#################################### CLOUD DATA STATUS CHECK API ###############################################################

class StatusUpdate(BaseModel):
    message: str
    updated: bool 
    statuses: dict  

latest_status = {
    "updated": False,
    "message": "No updates yet",
    "statuses": {
        "kit_status": False,
        "detection_status": False,
        "project_status": False,
        "custom_status": False,
        "mapping_status": False,
        "lpu_status": False,
        "roi_status": False,
        "polygon_status":False
    }
}

@router.post("/status")
async def receive_status_update(update: StatusUpdate):
    try:
        global latest_status  
        latest_status["updated"] = update.updated
        latest_status["message"] = update.message
        latest_status["statuses"] = update.statuses 

        print("db_status:", update.updated)
        print("message:", update.message)
        print("statuses:", update.statuses)

        return {"received": {"message": "Received db response"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status_info")
async def get_status_update():
    try:
        return {"latest_status": latest_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







class Deletedata(BaseModel):
    lpu_id: int 


@router.post("/delete_data")
async def delete_data(request: Deletedata):
    try:
        lpu_id = request.lpu_id
        db=next(get_db())
        print("delete data lpu_id:", lpu_id)

     
        delete_data = db.query(Ondelete).filter(Ondelete.status == True,Ondelete.lpu_id == lpu_id).all()

        if delete_data:
            response_data = [
                {
                    "id": delete.id,
                    "project_id": delete.project_id,
                    "camera_ip": delete.camera_ip,
                    "custom_class": delete.custom_class,
                    "detection_id":delete.detection_id,
                    "lpu_id": delete.lpu_id
                }
                for delete in delete_data
            ]
        else:
            response_data = []

        print("delete data:", response_data)
      
        db.execute(text("TRUNCATE TABLE ondelete"))
        db.commit()
        print("Ondelete table truncated.")

        return {
            "message": "message received successfully",
            "delete_data": response_data
        }


    except Exception as e:
        db.rollback()
        print(f"Error in delete_data: {e}")
        return {"message": "Error processing request", "error": str(e)}

##################################################################################################################################




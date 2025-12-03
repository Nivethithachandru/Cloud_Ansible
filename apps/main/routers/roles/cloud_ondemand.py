from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.jwt import *
from fastapi.templating import Jinja2Templates
from apps.main.routers.roles.auth_role import *
import threading
from fastapi import FastAPI, File, UploadFile, Query
import shutil
from pathlib import Path
import subprocess
from fastapi.responses import FileResponse

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")




@router.post("/cloud/videorequest/error_handle/")
async def update_failed_statuscode_videoreq(update_data: dict):
    try:
        print("[VMS PART - ONDEMAND ERROR HANDLE ACK]---------- Function started")
        db = next(get_db())
        pending_ids = update_data.get("pending_ids", []) 
        file_status_code = update_data.get("file_status_code")  
        file_status_code = int(file_status_code)        
        if not pending_ids:
            raise HTTPException(status_code=400, detail="Missing required data (pending_ids )")
        updated_count = db.query(cloud_vms).filter(cloud_vms.id.in_(pending_ids)).update(
            {"file_status_code":file_status_code}, synchronize_session=False
        )
        db.commit()

        if updated_count == 0:
            print("[VMS PART - ONDEMAND ERROR HANDLE ACK]---------- No records updated")
            return JSONResponse(content={"message": "No records updated."}, status_code=404)
        return JSONResponse(content={
            "message": "Failed Status acknowledgment  successfully.",
            "updated_ids": pending_ids
        })
    except Exception as e:
        
        print("[VMS PART - ONDEMAND ERROR VIDEO REQ ACKNOWLEDGMENT ERROR]:", e)
        raise HTTPException(status_code=500, detail="Error processing acknowledgment")

@router.post("/cloud/videorequest/merging/acknowledge/")
async def acknowledge_merging_video_request(update_data: dict):
    try:
        print("[VMS PART - MERGING REQUEST HANDLE ACK]---------- Funcation started")
        db = next(get_db())
        
        pending_ids = update_data.get("pending_ids", [])  
        all_file_list = update_data.get("all_file_list", [])
        print("Received all_file_list:", all_file_list)

        if not pending_ids or not all_file_list:
            raise HTTPException(status_code=400, detail="Missing required data (pending_ids or all_file_list)")

        # Update status to 'Processing'
        updated_count = db.query(cloud_vms).filter(cloud_vms.id.in_(pending_ids)).update(
            {"file_status_code": 2}, synchronize_session=False
        )
        db.commit()

        # if updated_count == 0:
        #     print("[VMS PART - MERGING REQUEST HANDLE ACK]---------- No record")
        #     return JSONResponse(content={"message": "No records updated."}, status_code=404)

        # Get the first record to retrieve project_id, camera_ip, and detection_id
        existing_video_req = db.query(cloud_vms).filter(cloud_vms.id.in_(pending_ids)).first()
        print("existing_video_reqexisting_video_req",existing_video_req)
        print("^&&&&&&&&&&&&&&&&&",pending_ids)
        # Start the video concatenation in a separate thread
        file_upload_thread_obj = threading.Thread(
            target=file_concatenate_vps, args=(existing_video_req, pending_ids, all_file_list,)
        )
        file_upload_thread_obj.start()

        return JSONResponse(content={
            "message": "Merging acknowledgment processed successfully.",
            "updated_ids": pending_ids
        })

    except Exception as e:
        print("[VMS PART - MERGING REQUEST HANDLE ACK]---------- ")
        print("[MERGING ACKNOWLEDGMENT ERROR]:", e)
        raise HTTPException(status_code=500, detail="Error processing acknowledgment")


def file_concatenate_vps(existing_video_req, pending_ids, all_file_list):
    try:
        project_id = existing_video_req.project_id
        camera_ip = existing_video_req.camera_ip
        detection_id = existing_video_req.detection_id

        file_upload_directory = Path(BASE_UPLOAD_DIRECTORY) / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
        file_upload_directory.mkdir(parents=True, exist_ok=True)

        text_file_path = file_upload_directory / "file_list.txt"
        #video_filename = f"{existing_video_req.request_start_time}.mp4"
        video_filename = f"{existing_video_req.request_start_time}_to_{existing_video_req.request_end_time}.mp4"


        # Writing the filenames in a format suitable for FFmpeg concatenation
        with open(text_file_path, "w") as text_file:
            for file_name in all_file_list:
                file_path = file_upload_directory / file_name
                text_file.write(f"file '{file_path}'\n")
        
        print(f"[VMS-PART]Created file_list.txt in {text_file_path}")

        # Call video concatenation function
        concatenate_videos(pending_ids, text_file_path, file_upload_directory,video_filename)

    except Exception as e:
        print("[VMS- PART MERGING FILE CONCATENATION ERROR]:", e)


def concatenate_videos(pending_ids, text_file_path, file_upload_directory,video_filename):
    try:
        db = next(get_db())
        
        output_mp4 = file_upload_directory / video_filename

        ffmpeg_command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(text_file_path),
            "-c", "copy", str(output_mp4)
        ]

        subprocess.run(ffmpeg_command, check=True)
        print(f"Concatenated video saved to {output_mp4}")

        db.query(cloud_vms).filter(cloud_vms.id.in_(pending_ids)).update(
            {"file_status_code": 3}, synchronize_session=False
        )
        db.commit()

    except subprocess.CalledProcessError as e:
        print(f"[VMS-PART ERROR] Video merging failed: {e}")
        raise HTTPException(status_code=500, detail="FFmpeg error during video merging")
    
    
######################################################################
@router.get("/cloud/videorequest/local/download")
async def download_videorequest(project_id, detection_id, camera_ip,request_start_time,request_end_time):
    try:
        
        db = next(get_db())
        existing_video_req = (
                db.query(cloud_vms)
                .filter(
                    cloud_vms.project_id == project_id,
                    cloud_vms.detection_id == detection_id,
                    cloud_vms.camera_ip == camera_ip,
                    cloud_vms.request_start_time == request_start_time,
                    cloud_vms.request_end_time == request_end_time,
                )
                .first()
            )
        if not existing_video_req:
                raise HTTPException(status_code=404, detail="No record found for the given project and detection details")

        #filename = f"{existing_video_req.request_start_time}.mp4"
        filename = f"{existing_video_req.request_start_time}_to_{existing_video_req.request_end_time}.mp4"

        file_directoy_directory = Path(BASE_UPLOAD_DIRECTORY) / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
        print("****************!!!!!!",file_directoy_directory)
        output_mp4 = file_directoy_directory / filename
        print("******output_mp4***",output_mp4)
        if not output_mp4.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
                output_mp4,
                media_type="video/mp4",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
    except Exception as e:
        print("[CLOUD-ONDEMAND] Download eerrror",e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
######################################################################

@router.post("/cloud/videorequest/acknowledge/")
async def acknowledge_video_request(update_data: dict):
    try:
        db = next(get_db())
        updated_ids = update_data.get("updated_ids", [])
        file_status_code = update_data.get("file_status_code", None) 
        print("*******updated_data",update_data)
        if not updated_ids or file_status_code != 1:
            raise HTTPException(status_code=400, detail="Invalid request payload")

        db.query(cloud_vms).filter(cloud_vms.id.in_(updated_ids)).update(
            {"file_status_code": 1}, synchronize_session=False
        )
        db.commit()

        return JSONResponse(content={"message": "Acknowledgment processed successfully.", "updated_ids": updated_ids})

    except Exception as e:
        print("[VMS -PART ACKNOWLEDGMENT ERROR]:", e)
        raise HTTPException(status_code=500, detail="Error processing acknowledgment")


# for progress file upload and pending file upload process

@router.post("/cloud/videorequest/update_status/")
async def update_upload_status(payload: dict):
    try:
        db = next(get_db())
        request_id = payload.get("request_id")
        upload_count = payload.get("upload_count")
        file_count = payload.get("file_count")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")

        print(f"[CLOUD API] Received update_status: request_id={request_id}, upload_count={upload_count}, file_count={file_count}")


        if request_id is None:
            return JSONResponse(status_code=400, content={"message": "request_id is required."})

        video_entry = db.query(cloud_vms).filter(cloud_vms.id == request_id).first()
        if not video_entry:
            return JSONResponse(status_code=404, content={"message": "Video request not found."})

        if upload_count is not None:
            video_entry.upload_count = upload_count
        if file_count is not None:
            video_entry.file_count = file_count

        db.commit()
        return {"message": "Status updated successfully."}

    except Exception as e:
        print("[CLOUD ERROR]", e)
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("**************")
        print("erorrrrrrrrrrrrrrrr")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

    

@router.get("/cloud/videorequest/device/{lpu_id}/")
async def get_videoreq_cloud_deviceid(lpu_id: str):
    try:
        db = next(get_db())
        print("[CLOUD] Device ID ", lpu_id)
        vms_records = db.query(cloud_vms).filter( 
            cloud_vms.lpu_id == lpu_id ,          
            cloud_vms.file_status_code == 0
        ).all()
        request_list = [
            {
                "s_id": record.id,
                "project_id": record.project_id,
                "detection_id": record.detection_id,
                "camera_ip": record.camera_ip,
                "request_start_time": record.request_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "request_end_time": record.request_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_status_code": record.file_status_code
            }
            for record in vms_records
        ]
        print("request_list",request_list)
        return JSONResponse(content=
            {
                "data": request_list,
                "message": "Video request in progress. File will be ready in ~5 minutes, depending on internet speed."
            })

    except Exception as e:
        print("Error [VMS-PART CLOUD CRON]:",e)
        raise HTTPException(status_code=500, detail="Error fetching video requests")
        
from sqlalchemy import or_

@router.get("/main/videorequest/vms/project/{project_id}/camera_ip/{camera_ip}/detection/{detection_id}/")
async def video_detection_log(request: Request, project_id: int, camera_ip: str, detection_id: int):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        db = next(get_db())

        print("Project ID:", project_id, "Type:", type(project_id))
        print("Camera IP:", camera_ip, "Type:", type(camera_ip))
        print("Detection ID:", detection_id, "Type:", type(detection_id))

        # Query database for matching records
        vms_records = (db.query(cloud_vms).filter(
                cloud_vms.project_id == project_id,
                cloud_vms.camera_ip == camera_ip,
                cloud_vms.detection_id == detection_id,
                cloud_vms.file_status_code.in_([0, 1,3,2,4,5,6,7]),
                or_(cloud_vms.row_status == None, cloud_vms.row_status != "deleted")
            )
            .order_by(cloud_vms.id.asc())  
            .all()
        )


        if not vms_records:
            return JSONResponse(content={"data": [], "message": "No records found."})

        print("VMS Records Found:", len(vms_records))

        request_list = [
            {
                "pk_id":record.id,
                "project_id": record.project_id,
                "detection_id": record.detection_id,
                "camera_ip": record.camera_ip,
                "event_time": record.event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "request_start_time": record.request_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "request_end_time": record.request_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_status_code": record.file_status_code,
                "upload_count": record.upload_count,
                "file_count": record.file_count
            }
            for record in vms_records
        ]

        return JSONResponse(content={"data": request_list, "message": "Records retrieved successfully."})

    except Exception as e:
        print(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail="Error fetching records")

 

################## RESUME / RESTART ##################
@router.put("/main/ondemand/resume/{pk_id}/{project_id}/{detection_id}")
async def pause_hold_maintain(request: Request, pk_id: int, project_id: int, detection_id: int):
    try:
        print("################################## ON - DEMAND RESUME / RESTART ################################")
        print("[ON - DEMAND REstart / resume] pk_id", pk_id)
        print("[ON - DEMAND restart / resume] project_id", project_id)
        print("[ON - DEMAND restart / resume] detection_id", detection_id)
        db = next(get_db())

        data = db.query(cloud_vms).filter(
            cloud_vms.id == pk_id,
            cloud_vms.detection_id == detection_id,
            cloud_vms.project_id == project_id
        ).first()

        if not data:
            return {"error": "No matching entry found"}
        
        print("Existing Entry:", data)
        print("request_start_time:", data.request_start_time)
        print("request_end_time:", data.request_end_time)
        print("file_status_code:", data.file_status_code)
        print("row_status:", data.row_status)
        print("event_time:", data.event_time)
        print("Camera IP:", data.camera_ip)

        data.file_status_code = 7  #RESUME
        data.row_status = "resume"

        db.commit()
        db.refresh(data)
         
        return {
            "message": "Resume request received",
            "pk_id": pk_id,
            "project_id": project_id,
            "detection_id": detection_id
        }
    
    except Exception as e:
        print("[Restart / Resume On-Demand] Error:", e)
        return {"error": str(e)}

################## PAUSE / HOLD ##################
@router.put("/main/ondemand/hold/{pk_id}/{project_id}/{detection_id}")
async def pause_hold_maintain(request: Request, pk_id: int, project_id: int, detection_id: int):
    try:
        print("################################## ON - DEMAND PAUSE / HOLD ################################")
        print("[ON - DEMAND PAUSE / HOLD] pk_id", pk_id)
        print("[ON - DEMAND PAUSE / HOLD] project_id", project_id)
        print("[ON - DEMAND PAUSE / HOLD] detection_id", detection_id)

        db = next(get_db())

        data = db.query(cloud_vms).filter(
            cloud_vms.id == pk_id,
            cloud_vms.detection_id == detection_id,
            cloud_vms.project_id == project_id
        ).first()

        if not data:
            return {"error": "No matching entry found"}

        print("Existing Entry:", data)
        print("request_start_time:", data.request_start_time)
        print("request_end_time:", data.request_end_time)
        print("file_status_code:", data.file_status_code)
        print("row_status:", data.row_status)
        print("event_time:", data.event_time)
        print("Camera IP:", data.camera_ip)

        data.file_status_code = 6  #HOLD
        data.row_status = "hold"

        db.commit()
        db.refresh(data)
         
        return {
            "message": "Hold request received",
            "pk_id": pk_id,
            "project_id": project_id,
            "detection_id": detection_id
        }
    except Exception as e:
        print("[PAUSE / HOLD On-Demand] Error:", e)
        return {"error": str(e)}
################## PAUSE / HOLD ##################



@router.delete('/main/ondemand/delete/{pk_id}/{project_id}/{detection_id}')
async def delete_classes(request: Request, pk_id: int, project_id: int, detection_id: int):
    db = next(get_db())
    print("On demand deletion ID:", pk_id)
    print("On demand project ID:", project_id)
    print("On demand Detection ID:", detection_id)

    # Update the row_status to "deleted"
    rows_updated = db.query(cloud_vms).filter(
        cloud_vms.id == pk_id,
        cloud_vms.project_id == project_id,
        cloud_vms.detection_id == detection_id
    ).update({"row_status": "deleted"})

    db.commit()
    print("Successfully ON demand video request deleted [updated row status] . . . . . . . .  .")
    if rows_updated == 0:
        return JSONResponse(
            status_code=404,
            content={"message": f"No matching record found for id={pk_id}, project_id={project_id}, detection_id={detection_id}"}
        )

    return JSONResponse(content={"message": f"Request {pk_id} deleted successfully."})



@router.post('/main/cloud/videorequest/')
async def video_management_request(request: Request):
    try:
        print("&&&&&&&&&&&&&&&&&&&weqrwqerqwrewqerwqerwqer")
        db= next(get_db())  
        session_data, error_response = handle_session(request)
        if error_response:
            return JSONResponse(status_code=401, content={"message": "Unauthorized access."})

        data = await request.json()
        print("Received Data:", data)
        try:
            request_start_time = datetime.fromisoformat(data["request_start_time"])
            request_end_time = datetime.fromisoformat(data["request_end_time"])
        except ValueError:
            return JSONResponse(status_code=400, content={"message": "Invalid datetime format. Use ISO format."})

        video_req_directory = (
            Path(media_base_path) / "cloud_video"
            / f"proj_id_{data['project_id']}"
            / f"camera_{data['camera_ip']}"
            / f"detect_id_{data['detection_id']}"
        )


        # video_req_directory = Path(media_base_path) / "cloud_video" / f"proj_id_{data["project_id"]}" / f"camera_{data["camera_ip"]}" / f"detect_id_{data["detection_id"]}"
        print("video_req_directory", video_req_directory)
        video_req_directory.mkdir(parents=True, exist_ok=True)

        existing_entry = db.query(cloud_vms).filter(
            cloud_vms.project_id == data["project_id"],
            cloud_vms.camera_ip == data["camera_ip"],            
            cloud_vms.detection_id == data["detection_id"],
            cloud_vms.request_start_time == request_start_time,
            cloud_vms.request_end_time == request_end_time,
            cloud_vms.row_status == None
        ).first()

        if existing_entry:
            return JSONResponse(
                status_code=400,
                content={"message": "A request with the same start and end time already exists."}
            )
        print("typeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",type(data['project_id']))
        print("priject iddddddddddddddddddddddddddddddd",data['project_id'])
        lpu_entry = db.query(Project).filter(Project.project_id == data["project_id"]).first()
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&lpu_entry",lpu_entry)
        new_request = cloud_vms(
            lpu_id=lpu_entry.lpu_id,
            project_id=data["project_id"],
            camera_ip=data["camera_ip"],
            detection_id=data["detection_id"],
            event_time = datetime.now(),
            request_start_time=request_start_time,
            request_end_time=request_end_time,
            file_status_code=0  
        )

        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        return JSONResponse(
            status_code=201,
            content={"message": "Video request in progress. File will be ready in ~5 minutes, depending on internet speed", "request_id": new_request.id}
        )

    except HTTPException as http_error:
        return JSONResponse(status_code=http_error.status_code, content={"message": str(http_error.detail)})
    
    except Exception as e:
        print(f"Internal Server Error: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

from typing import List

@router.post("/cloud/videorequest/upload_video/")
async def upload_video(
    files: List[UploadFile] = File(...),
    project_id: int = Query(..., description="Project ID"),
    camera_ip: str = Query(..., description="Camera IP"),
    detection_id: int = Query(..., description="Detection ID")
):
    try:
        # Define upload path: BASE_UPLOAD_DIRECTORY/proj_id_x/camera_y/detect_id_z
        upload_directory = Path(BASE_UPLOAD_DIRECTORY) / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
        upload_directory.mkdir(parents=True, exist_ok=True)  # Create the directory structure if it doesn't exist

        print(f"[INFO] Upload directory created or already exists at: {upload_directory}")

        saved_files = []

        for file in files:
            file_path = upload_directory / file.filename
            print(f"[INFO] Saving file: {file.filename} to {file_path}")
            
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            saved_files.append(file.filename)

        # Print the summary of uploaded files
        print(f"[INFO] Total files uploaded: {len(saved_files)}")
        print(f"[INFO] Uploaded file names: {saved_files}")

        return {
            "message": "All files uploaded successfully",
            "uploaded_files": saved_files
        }

    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# @router.post("/cloud/videorequest/upload_video/")
# async def upload_video(
#     file: UploadFile = File(...),
#     project_id: int = Query(..., description="Project ID"),
#     camera_ip: str = Query(..., description="Camera IP"),
#     detection_id: int = Query(..., description="Detection ID")
# ):
#     try:
#         upload_directory = Path(BASE_UPLOAD_DIRECTORY) / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
#         upload_directory.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

#         file_path = upload_directory / file.filename
#         with file_path.open("wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         return {
#             "message": "Upload successful",
#             "file_name": file.filename,
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from apps.main.routers.datatable import table,detection_table
from apps.main.routers.report import rvtl_report
from aiocron import crontab
import asyncio


import threading
from apps.main.routers.super_admin import loggger, super_admin,draw_line,polygon,roi,roles,project,user,pmodules,lpu,hlslive,classes,permission,audit_report,mailer,alerts,view_report,kit
from apps.main.routers.roles import auth_role,auth_dashboard,cloud_live,cloud_ondemand
from apps.main.routers.syncing import cloud_sending
from apps.main.routers.super_admin import report_monitor
from fastapi.staticfiles import StaticFiles
from apps.main.models.model import SuperAdmin 
from apps.main.utils.jwt import * 
from apps.main.database.db import get_db 
from fastapi_utilities import repeat_every
from pathlib import Path

templates = Jinja2Templates(directory="apps/main/front_end/templates")

app = FastAPI()
app.mount("/front_end/static", StaticFiles(directory="apps/main/front_end/static"), name="static")

app.include_router(super_admin.router, tags=['Super Admin'])
app.include_router(auth_role.router, tags=['Roles Login'])
app.include_router(auth_dashboard.router, tags=['Roles Dashboard'])
app.include_router(roles.router, tags=['Roles Management'])
app.include_router(user.router, tags=['User Management'])
app.include_router(pmodules.router, tags=['Modules Management'])
app.include_router(lpu.router, tags=['LPU Management'])
app.include_router(draw_line.router, tags=['Draw Line'])
app.include_router(polygon.router,tags=['Polygon'])
app.include_router(roi.router, tags=['ROI Mapping'])
app.include_router(project.router, tags=['Project Management'])
app.include_router(view_report.router,tags=['View Report'])
app.include_router(classes.router, tags=['Model Classes'])
app.include_router(table.router,tags=['Record table'])
app.include_router(detection_table.router,tags=['Detection table'])
app.include_router(rvtl_report.router,tags=['Report'])


app.include_router(permission.router, tags=['Role Permission'])
app.include_router(audit_report.router, tags=['Report Management'])
app.include_router(mailer.router, tags=['Email Alert'])
app.include_router(alerts.router, tags=['Alert Setting'])
app.include_router(loggger.router, tags=['Loggs Management'])
app.include_router(kit.router, tags=['kit'])
app.include_router(report_monitor.router, tags=['Report Monitor'])



#app.include_router(hlslive.router, tags=['Live View'])

app.include_router(cloud_live.router, tags=['Cloud Live'])
app.include_router(cloud_ondemand.router, tags=['Cloud Live'])

# app.include_router(cloud_sending.router,tags=['Cloud Data Sending'])

# -----------------------------------------------------------------------------------
from starlette.middleware.base import BaseHTTPMiddleware

def translate_method_to_action(method: str) -> str:
    method_permission_mapping = {
        'GET': 'read',
        'POST': 'write',
        'PUT': 'update',
        'DELETE': 'delete',
    }
    return method_permission_mapping.get(method.upper(), 'read')



class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_method = request.method.upper()
        action = translate_method_to_action(request_method)
        resource = request.url.path[1:]  
        response = await call_next(request)
        if resource.startswith("front_end"):
            return response
        if resource == "":
            log_message = f"Method: {request_method}, Action: {action}, Resource: / (Entry Point), Status: {response.status_code}"
        else:
            log_message = f"Method: {request_method}, Action: {action}, Resource: {resource}, Status: {response.status_code}"
        # print(log_message)

        if response.status_code == 404:
            return templates.TemplateResponse("page_not_found.html", {"request": request}, status_code=404)
        
        return response

app.add_middleware(LoggingMiddleware)


# -----------------------------------------------------------------------------------
# from apps.main.routers.dbsync.hostdb_sync import export_data,audit_data
# from fastapi_utils.tasks import repeat_every
# import threading

 

# @app.on_event("startup")
# @repeat_every(seconds=10) 
# async def scheduled_export():    
#     print("Calling third sync data funciton ............. 33333")   
#     threading.Thread(target=export_data, daemon=True).start()



# # -----------------------------------------------------------------------------------
# @crontab('10 0 * * *')
# async def cron_job():
#     print("Checking Camera status  cron job every minutes . . . . .")
#     threading.Thread(target=audit_data, daemon=True).start()



@app.get("/check_db/")
async def check_database(request: Request, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            return {"message": "Database connected Successfully!"}
        else:
            raise HTTPException(status_code=500, detail="Database connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

###################################### SYNC DB ###################################################
# @app.on_event("startup")
# async def startup_event():

#     task = asyncio.create_task(sync_db.schedule_sync())
#     app.state.sync_task = task 


# @app.on_event("shutdown")
# async def shutdown_event():
   
#     task = app.state.sync_task
#     if task:
#         task.cancel()
#         try:
#             await task  
#         except asyncio.CancelledError:
#             print("Sync task successfully cancelled.")

##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################
##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################
##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################



# @app.on_event('startup')
# @repeat_every(seconds=10)
# async def cron_job():
#     await monitor_background_video_file_db()


async def monitor_background_video_file_db():
    try:
        db_session = next(get_db())
        alldetectionlogs = db_session.query(Detection_log).filter(Detection_log.vms_status == True).all()
        # print(f'[VMS] Current Detection Execute:  {len(alldetectionlogs)}')
        for vms_storing_log in alldetectionlogs:            
            await process_camera_section([vms_storing_log], db_session) 
    except Exception as e:
        print("Error:from monitor_background_video_file_db1", e)


async def process_camera_section(vms_storing_log, db_session: Session):
    try:
        for vms in vms_storing_log:
            project_id = vms.project_id
            camera_ip = vms.camera_ip
            detection_id = vms.detection_id

            cameraId_folder = Path(media_base_path) / "VMS" / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
            # print(f'[VMS] Video Storing Camera ID Folder path is:  {cameraId_folder}')

            segments_file_path = os.path.join(cameraId_folder, "segments.txt")
            # print(f'[VMS] Video Storing Camera Segment text file  path is:  {segments_file_path}')

            if not os.path.exists(cameraId_folder):
                # print(f"[VMS] Folder not found for project id {project_id} camera ip {camera_ip} detection id {detection_id}: {cameraId_folder}")
                continue  

            existing_segments = set()
            if os.path.exists(segments_file_path):
                with open(segments_file_path, "r") as file:
                    existing_segments = set(file.read().splitlines())

            new_segments = [
                filename.strip() for filename in os.listdir(cameraId_folder)
                if filename.endswith(".ts") and filename.strip() not in existing_segments
            ]

            for segment in new_segments:
                # print(f'[VMS] New segment detected: {segment} for project id {project_id} camera ip {camera_ip} detection id {detection_id}: {cameraId_folder}')
                try:
                    time_str = segment[:-3]  # Remove `.ts` extension
                    segment_start_time = datetime.strptime(time_str, "%Y-%m-%d-%H-%M-%S")

                
                    existing_video = db_session.query(VideosTsList).filter_by(
                        project_id=project_id,
                        camera_ip=camera_ip,
                        detection_id=detection_id,
                        file_name=segment
                    ).first()

                    if existing_video:
                        # print(f"[VMS] Segment {segment} already exists in the database. Skipping insertion.")
                        continue
                    
                    new_video = VideosTsList(
                        project_id=project_id,
                        camera_ip=camera_ip,
                        detection_id=detection_id,
                        start_time=segment_start_time,
                        file_name=segment,                    
                    )
                    db_session.add(new_video)
                    db_session.commit()
                    # print(f"[VMS]  Inserted new segment: {segment} in Database")
                    existing_segments.add(segment)

                except Exception as e:
                    print(f"[VMS] Error processing segment {segment}: {e}")  
            
            if new_segments:
                try:
                    with open(segments_file_path, "a") as file:
                        file.write("\n".join(new_segments) + "\n")
                except Exception as e:
                    print(f"[VMS] Error updating segments file for project id {project_id} camera ip {camera_ip} detection id {detection_id}: {cameraId_folder}: {e}")

    except Exception as e:
        print("[VMS] Error in processing section:", e)








##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################
##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################
##########################   FFMPEG STREAMING SEGMENT STORED IN DATABASE  #####################

import cv2
import base64
import json
import numpy as np
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# clients = set() 

# @app.websocket("/ws/stream/1/")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     clients.add(websocket)
#     print(f"Viewer connected: {websocket.client}")

#     try:
#         while True:
#             frame = await websocket.receive_bytes()  
            
#             for client in list(clients):
#                 if client != websocket:
#                     try:
#                         await client.send_bytes(frame) 
                        
#                     except:
#                         clients.remove(client)  
                        
#     except WebSocketDisconnect:
#         print(f"Viewer disconnected: {websocket.client}")
#         clients.remove(websocket)


########################################################################################################
########################################################################################################
# from typing import Dict, Set

# clients: Dict[int, Set[WebSocket]] = {}

# @app.websocket("/ws/stream/{lpu_id}/{camera_id}/")
# async def websocket_endpoint(websocket: WebSocket, lpu_id:int,camera_id: int):
#     await websocket.accept()
#     print("88888888888888888888888888888888")
#     camera_id = int(camera_id)
#     lpu_id = int(lpu_id)

#     if camera_id not in clients:
#         clients[camera_id] = set()
#     clients[camera_id].add(websocket)

#     print(f"Viewer connected: {websocket.client} for lpu {lpu_id}, Camera {camera_id}")

#     try:
#         while True:
#             message = await websocket.receive_text()
#             data = json.loads(message)
#             # print("message in web socket:",message)

#             image_data = data.get("frame")  
#             if image_data:
#                 # print("📥 Received image frame")
#                 message = json.dumps({"img": "data:image/jpeg;base64," + image_data})

#             frame = data.get("frame")


#             for client in list(clients[camera_id]):

#                 if client != websocket:
#                     try:
#                         await client.send_text(json.dumps({"lpu_id": lpu_id, "camera_id": camera_id, "frame": frame}))
#                     except:
#                         clients[camera_id].remove(client)

#     except WebSocketDisconnect:
#         print(f"Viewer disconnected: {websocket.client} from lpu {lpu_id}, Camera {camera_id}")
#         clients[camera_id].remove(websocket)

from typing import Dict, Set


clients: Dict[int, Set[WebSocket]] = {}
viewer_active: Dict[int, int] = {}
camera_stream_allowed: Dict[int, bool] = {}

# Viewer WebSocket
@app.websocket("/ws/stream/view/{lpu_id}/{camera_id}/")
async def viewer_websocket(websocket: WebSocket, lpu_id: int, camera_id: int):
    await websocket.accept()

    if camera_id not in clients:
        clients[camera_id] = set()
    clients[camera_id].add(websocket)

    viewer_active[camera_id] = viewer_active.get(camera_id, 0) + 1
    camera_stream_allowed[camera_id] = True

    print(f"[VIEW] Viewer connected to camera {camera_id}")

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        print(f"[VIEW] Viewer disconnected from camera {camera_id}")
        clients[camera_id].remove(websocket)
        viewer_active[camera_id] = max(0, viewer_active.get(camera_id, 1) - 1)

        if viewer_active[camera_id] == 0:
            camera_stream_allowed[camera_id] = False
            print(f"[VIEW] No viewers. Stream disabled for camera {camera_id}")

# Kit sends stream to server
@app.websocket("/ws/stream/camera/{lpu_id}/{camera_id}/")
async def camera_stream(websocket: WebSocket, lpu_id: int, camera_id: int):
    # Ensure stream is allowed
    if not camera_stream_allowed.get(camera_id, False):
        await websocket.close()
        print(f"[SERVER] Rejected stream from camera {camera_id}: No active viewer.")
        return

    await websocket.accept()
    print(f"[SERVER] Camera {camera_id} started streaming...")

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            frame = data.get("frame")

            # Broadcast to viewers
            for client in list(clients.get(camera_id, [])):
                try:
                    await client.send_text(json.dumps({
                        "lpu_id": lpu_id,
                        "camera_id": camera_id,
                        "frame": frame
                    }))
                except Exception:
                    clients[camera_id].remove(client)
    except WebSocketDisconnect:
        print(f"[SERVER] Camera {camera_id} disconnected.")

# API: Viewer status
@app.get("/ws/stream/viewer-status/{camera_id}")
async def get_viewer_status(camera_id: int):
    return {"viewer_active": viewer_active.get(camera_id, 0) > 0}

# API: Stream permission
@app.get("/ws/stream/camera-status/{camera_id}")
async def get_camera_stream_status(camera_id: int):
    return {"camera_stream_allowed": camera_stream_allowed.get(camera_id, False)}
########################################################################################################
########################################################################################################        


from fastapi import APIRouter, Query ,Request,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy import text
from apps.main.config import folder
from apps.main.utils.local_vendor import *
from apps.main.database.db import get_db
from apps.main.utils.jwt import *
from apps.main.routers.roles.auth_role import *
from apps.main.models.model import * 


from pathlib import Path
from fastapi.responses import FileResponse
import subprocess
from pathlib import Path
from datetime import timedelta


router=APIRouter()

templates = Jinja2Templates(directory="apps/main/front_end/templates")

@router.get("/main/view_report/",response_class=HTMLResponse,name="main.viewreport")
async def get_frame(request:Request):
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        role_id = session_data.get('role_id')
        db = next(get_db())   
        modulee_id = 9
        show_required_permission = "show" 
        
        show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
        print("show_required_permission",show_required_permission)
        if role_id == 0:

            required_permission_s = True
            edit_required_permission_s = True
            delete_required_permission_s = True

            return templates.TemplateResponse("super_admin/generate report/view_report.html", 
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
            return templates.TemplateResponse("super_admin/generate report/view_report.html",
                                                {'request': request,
                                                    'page_permission':required_permission,
                                                    'edit_permission' :edit_required_permission,
                                                    'delete_permission' :delete_required_permission,
                                                    "session": session_data})
        


@router.get('/main/report_list')
async def report_list():
    db = next(get_db())
    print("********")
    print("********")
    print("********")
    detection_logs = db.query(Detection_log).order_by(Detection_log.id.desc()).all()
    # detection_logs = db.query(Detection_log).filter(Detection_log.cloud_delete == False).order_by(Detection_log.id).all()

    print("Detection log",detection_logs)
    projects = db.query(Project).order_by(Project.id).all()
    
    project_mapping = {project.project_id: project.project_name for project in projects}
    print("Project mapping:", project_mapping)

    pro_list = []
    for detection_item in detection_logs:
        project_name = project_mapping.get(detection_item.project_id, "Unknown Project")
        
        
        formatted_start_time = (
            detection_item.start_time.strftime("%d%b %H:%M:%S") 
            if isinstance(detection_item.start_time, datetime) else detection_item.start_time
        )
        formatted_end_time = (
            detection_item.end_time.strftime("%d%b %H:%M:%S") 
            if isinstance(detection_item.end_time, datetime) else detection_item.end_time
        )

        print("Formatted detection start time:", formatted_start_time)

        line_id = detection_item.line_id if detection_item and detection_item.line_id else None
        if line_id:
            line_id = line_id.replace("{", "").replace("}", "")
        if not line_id:
            line_id = getattr(detection_item, 'mapped_polygon', None)

        pro_list.append({
            "id": detection_item.id,
            "project_id": detection_item.project_id,
            "detection_id":detection_item.detection_id,
            "project_name": project_name,  
            "camera_ip": detection_item.camera_ip,
            "start_time": formatted_start_time,
            "end_time": formatted_end_time,
            "line_id": line_id,
            "vms_status": detection_item.vms_status
        })

    print("Full project list:", pro_list)

    return JSONResponse(content={"data": pro_list})





# @router.get("/hourly/download/{project_id}/{detection_id}/{camera_ip}")
# async def hourly_report(request: Request, project_id: int, detection_id: int,camera_ip:str):
#     try:
#         session_data, error_response = handle_session(request)
#         if error_response:
#             return RedirectResponse(url="/")

#         db_session= next(get_db())

#         detection_log = db_session.query(Detection_log).filter(
#             Detection_log.detection_id == detection_id,
#             Detection_log.project_id == project_id,
#         ).first()

#         project = db_session.execute(
#             text('SELECT project_id, project_name FROM project WHERE project_id = :project_id'),
#             {'project_id': project_id}
#         ).fetchone()

#         if not project:
#             raise HTTPException(status_code=404, detail="Invalid project value")

#         project_name = project[1]

#         print("project_name:",project_name)


     


#         if detection_log:
#             start_time = detection_log.start_time
#             end_time = detection_log.end_time
#             line_id = detection_log.line_id

#             print("start_time:", start_time)
#             print("end_time:", end_time)

#             hourly_intervals = []

#             # First interval ends at the next top of the hour
#             first_end = (start_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

#             if first_end > end_time:
#                 first_end = end_time

#             hourly_intervals.append({
#                 "start": start_time.strftime("%Y-%m-%d %I:%M %p"),
#                 "end": first_end.strftime("%Y-%m-%d %I:%M %p")
#             })

#             current_start = first_end

#             while current_start < end_time:
#                 next_end = current_start + timedelta(hours=1)
#                 if next_end > end_time:
#                     next_end = end_time

#                 hourly_intervals.append({
#                     "start": current_start.strftime("%Y-%m-%d %I:%M %p"),
#                     "end": next_end.strftime("%Y-%m-%d %I:%M %p")
#                 })

#                 print("current interval:", current_start, "→", next_end, "| line_id:", line_id)

#                 current_start = next_end

#             context_data = {
#                 "request": request,
#                 "project_id": project_id,
#                 "project_name":project_name,
#                 "detection_id": detection_id,
#                 "camera_ip": detection_log.camera_ip,
#                 # "hourly_intervals": hourly_intervals,
#                 "hourly_intervals":list(reversed(hourly_intervals)),
#                 "line_id":line_id,
#                 "session": session_data,
#                 "message": "data_success"
#             }

#             return templates.TemplateResponse("super_admin/project/excel_table.html", context_data)

#         else:
#             context_data = {
#                 "request": request,
#                 "project_id": project_id,
#                 "detection_id": detection_id,
#                 "session": session_data,
#                 "message": "data_failed"
#             }
#             return templates.TemplateResponse("super_admin/project/excel_table.html", context_data)

#     except Exception as e:
#         print(f"Error fetching records: {e}")
#         raise HTTPException(status_code=500, detail="Error fetching records") from e
async def get_custom_module_name(db,lpu_id):
    cust_data = db.query(CustomClasses).filter(CustomClasses.lpu_id==lpu_id).all()
    return cust_data

async def get_orginal_module_name(db):
    orgi_data = db.query(ModuleClassesGroup).order_by(ModuleClassesGroup.id).all()  
    return orgi_data

@router.get("/hourly/download/{project_id}/{detection_id}/{camera_ip}")
async def hourly_report(request: Request, project_id: int, detection_id: int,camera_ip:str):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        db_session= next(get_db())
        lpu_id=session_data['lpu_id']
        get_custom_class_name = await get_custom_module_name(db_session,lpu_id)
        get_orignial_class_name = await get_orginal_module_name(db_session)

        detection_log = db_session.query(Detection_log).filter(
            Detection_log.detection_id == detection_id,
            Detection_log.project_id == project_id,
        ).first()

        project = db_session.execute(
            text('SELECT project_id, project_name FROM project WHERE project_id = :project_id'),
            {'project_id': project_id}
        ).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Invalid project value")

        project_name = project[1]

        print("project_name:",project_name)


        # Fetch custom classes dynamically
     # Fetch custom classes dynamically, ordered by id ascending
        custom_classes = db_session.query(CustomClasses).filter(
            CustomClasses.lpu_id == lpu_id
        ).order_by(CustomClasses.id.asc()).all()


     


        if detection_log:
            start_time = detection_log.start_time
            end_time = detection_log.end_time
            line_id = detection_log.line_id

            print("start_time:", start_time)
            print("end_time:", end_time)

            hourly_intervals = []

            # First interval ends at the next top of the hour
            first_end = (start_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

            if first_end > end_time:
                first_end = end_time

            hourly_intervals.append({
                "start": start_time.strftime("%Y-%m-%d %I:%M %p"),
                "end": first_end.strftime("%Y-%m-%d %I:%M %p")
            })

            current_start = first_end

            while current_start < end_time:
                next_end = current_start + timedelta(hours=1)
                if next_end > end_time:
                    next_end = end_time

                hourly_intervals.append({
                    "start": current_start.strftime("%Y-%m-%d %I:%M %p"),
                    "end": next_end.strftime("%Y-%m-%d %I:%M %p")
                })

                print("current interval:", current_start, "→", next_end, "| line_id:", line_id)

                current_start = next_end

            context_data = {
                "request": request,
                "project_id": project_id,
                "project_name":project_name,
                "detection_id": detection_id,
                "camera_ip": detection_log.camera_ip,
                "hourly_intervals":list(reversed(hourly_intervals)),
                "line_id":line_id,
                "custom_class": get_custom_class_name,
                "original_class": get_orignial_class_name,
                "session": session_data,
                "custom_classes": custom_classes ,
                "message": "data_success"
            }

            return templates.TemplateResponse("super_admin/project/excel_table.html", context_data)

        else:
            context_data = {
                "request": request,
                "project_id": project_id,
                "detection_id": detection_id,
                "session": session_data,
                "custom_class": get_custom_class_name,
                "custom_classes": custom_classes ,
                "original_class": get_orignial_class_name,
                "message": "data_failed"
            }
            return templates.TemplateResponse("super_admin/project/excel_table.html", context_data)

    except Exception as e:
        # print(f"Error fetching records: {e}")
        # raise HTTPException(status_code=500, detail="Error fetching records") from e
        print(f"Error fetching records: {e}")
        # always render the same page with error message
        return templates.TemplateResponse(
            "super_admin/project/excel_table.html",
            {
                "request": request,
                "project_id": project_id,
                "detection_id": detection_id,
                "custom_classes": custom_classes,
                "session": session_data if 'session_data' in locals() else None,
                "custom_class": locals().get("get_custom_class_name"),
                "original_class": locals().get("get_orignial_class_name"),
                "message": "error"
            }
        )


###########################################   VMS VIDEO VIEW #####################################################

###########################################   VMS VIDEO VIEW #####################################################

###########################################   VMS VIDEO VIEW #####################################################
@router.get("/detection/vms/project/{project_id}/detection/{detection_id}/")
async def video_detection_log(request: Request, project_id: int, detection_id: int):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        db_session = next(get_db())
      
        print("Project Id:", project_id, type(project_id))
        print("Detection Id:", detection_id, type(detection_id))

        detection_log = db_session.query(Detection_log).filter(
            Detection_log.detection_id == detection_id,
            Detection_log.project_id == project_id,
        ).first()
        print("detection_log", detection_log)

        if detection_log:
            print("detection_log", detection_log)
            print(f"Detection Log Found: Start Time - {detection_log.start_time}, End Time - {detection_log.end_time}")
            
            start_time = detection_log.start_time.strftime("%Y-%m-%d %H:%M:%S") if detection_log.start_time else None
            end_time = detection_log.end_time.strftime("%Y-%m-%d %H:%M:%S") if detection_log.end_time else None

            context_data = {
                "request": request,
                "project_id": project_id,
                "detection_id": detection_id,
                "camera_ip": detection_log.camera_ip,
                "start_time": start_time,
                "WEBSOCKET_CLOUD_URL":WEBSOCKET_CLOUD_PREVIEW,
                "end_time": end_time,
                "session": session_data,
                "message": "data_success"
            }

            return templates.TemplateResponse("report_template/vms_videolist.html", context_data)
        else:
            context_data = {
                "request": request,
                "project_id": project_id,
                "detection_id": detection_id,
                "session": session_data,
                "WEBSOCKET_CLOUD_URL":WEBSOCKET_CLOUD_PREVIEW,
                "message": "data_failed"
            }

            return templates.TemplateResponse("report_template/vms_videolist.html", context_data)

    except Exception as e:
        print(f"111111111111Error fetching records: {e}")
        raise HTTPException(status_code=500, detail="Error fetching records") from e



@router.get("/vms/filter/project/{project_id}/camera_ip/{camera_ip}/detection_id/{detection_id}/start_time/{start_time}/end_time/{end_time}/")
async def filter_vms_data(project_id: int, camera_ip: str, detection_id: int, start_time: str, end_time: str):
    try:
        print("Project ID", project_id, type(project_id))
        print("Camera IP", camera_ip, type(camera_ip))
        print("Detection ID", detection_id, type(detection_id))
        print("Start Time", start_time, type(start_time))
        print("End Time", end_time, type(end_time))

        start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        if end_time.lower() == 'null':
            end_time_obj = datetime.now()
        else:
            end_time_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")



        db_session = next(get_db())
        print("end_time_obj",end_time_obj)
         

        query = text(''' 
            SELECT 
                DATE_TRUNC('hour', start_time) AS minute_group, 
                STRING_AGG(file_name, ', ' ORDER BY start_time) AS file_list
            FROM video_ts_data
            WHERE detection_id = :detection_id 
            AND start_time BETWEEN :start_time AND :end_time
            GROUP BY minute_group
            ORDER BY minute_group;
        ''')


        results = db_session.execute(query, {
            "detection_id": detection_id,
            "start_time": start_time_obj,
            "end_time": end_time_obj
        }).fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No data found for the given filters")

        print("results",results)
        data = []
        for row in results:
            original_start_time = row[0]  # ? Keep original start time unchanged
            print("original_start_time",original_start_time)
            # ? Correctly round end_time
            if original_start_time.minute > 0 or original_start_time.second > 0:
                end_time = original_start_time.replace(minute=0, second=0) + timedelta(hours=1)
            else:
                end_time = original_start_time + timedelta(hours=1)

            data.append({
                "project_id": project_id,
                "detection_id": detection_id,
                "camera_ip": camera_ip,
                "start_time": str(original_start_time),  # ? Use the unmodified start_time
                "end_time": str(end_time),  # ? Correctly rounded end_time
                "minute_group": str(original_start_time),  # ? Ensure it's the correct grouping time
                "file_list": row[1].split(", ")   
            })



        
        vms_directory = Path(media_base_path) / "VMS" / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
        print("vms_directory", vms_directory)

        if not vms_directory.exists():
            print(f"Directory {vms_directory} does not exist.")
            raise HTTPException(status_code=404, detail="VMS directory not found")

        for entry in data:
            minute_group_folder = vms_directory / entry["minute_group"]
            minute_group_folder.mkdir(parents=True, exist_ok=True)
            text_file_path = minute_group_folder / "file_list.txt"

            sorted_files = sorted(entry["file_list"])  

            with open(text_file_path, "w") as text_file:
                for file_name in sorted_files:
                    text_file.write(f"file '{vms_directory / file_name}'\n")

            print(f"Created file_list.txt in {minute_group_folder} with sorted file names.")


        return {"message": "Data fetched successfully", "data": data}

    except Exception as e:
        print(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail="Error processing files") from e


############################################ VMS DOWNLOAD NOTIFICATION  ###################################
@router.put("/notifications/{notification_id}")
async def mark_notification_as_read(notification_id: int):
    try:
        db_session = next(get_db())
        notification = db_session.query(Vms_notification).filter(
            Vms_notification.id == notification_id
        ).first()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_visit = False
        db_session.commit()
        return {"message": "Notification marked as read"}

    except Exception as e:
        print(f"Error Mark  files: {e}")



@router.post("/notifications/mark_all_as_read")
async def mark_all_as_read():
    try:
        db = next(get_db())
        # Update all notifications where is_visit is True to set it as False
        db.query(Vms_notification).filter(Vms_notification.is_visit == True).update({"is_visit": False})
        db.commit()
        return {"message": "All notifications marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while marking all notifications.")



@router.get("/files/{notification_id}")
async def get_file(notification_id: int):
    try:
        db_session = next(get_db())

        Vms_notification_data = db_session.query(Vms_notification).filter(
            Vms_notification.id == notification_id
        ).first()

        if not Vms_notification_data:
            raise HTTPException(status_code=404, detail="Notification not found")

        vms_directory = Vms_notification_data.vms_directory
        filename = Vms_notification_data.vms_download_filename

        if os.path.exists(vms_directory):
            return FileResponse(
                vms_directory,
                media_type="video/mp4", 
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        print(f"Error Download files: {e}")

############################################ VMS DOWNLOAD NOTIFICATION  ###################################

@router.post("/vms/download/")
async def download_vms_files(request: Request):
    try:
        data = await request.json()
        detection_id = data.get('detection_id')
        minute_group = data.get('minute_group')

        db_session = next(get_db())
        detection_log = db_session.query(Detection_log).filter(
            Detection_log.detection_id == detection_id
        ).first()

        if not detection_log:
            raise HTTPException(status_code=404, detail="Detection log not found")

        project_id = detection_log.project_id
        camera_ip = detection_log.camera_ip

        vms_download_directory = Path(media_base_path) / "VMS" / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}" / minute_group

        vms_notification_download_filename = f'p{project_id}_d{detection_id}_T{minute_group}.mp4'
        file_list_txt_path = vms_download_directory / "file_list.txt"
        output_mp4 = vms_download_directory / vms_notification_download_filename
        
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
       
        vms_notification_diretory = Path(media_base_path) / "VMS" / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}" / minute_group / vms_notification_download_filename

        vms_record = Vms_notification(
            project_id=project_id,
            camera_ip=camera_ip,
            detection_id=detection_id,
            vms_directory=str(vms_notification_diretory),
            vms_download_filename = str(vms_notification_download_filename),
            is_visit=False 
        )
        db_session.add(vms_record)
        db_session.commit()
        new_vms_record_id = vms_record.id

        try:
            ffmpeg_command = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(file_list_txt_path),
                "-c", "copy", str(output_mp4)
            ]

            subprocess.run(ffmpeg_command, check=True)
            print(f"Concatenated video saved to {output_mp4}")

            db_session.query(Vms_notification).filter(
                Vms_notification.id == new_vms_record_id
            ).update({"is_visit": True})
            db_session.commit()

        except subprocess.CalledProcessError as e:
            print(f"Error concatenating video: {e}")
            raise HTTPException(status_code=500, detail="Error merging video files")

        return FileResponse(
            path=str(output_mp4),
            media_type="video/mp4",
            headers={"Content-Disposition": f'attachment; filename="{output_mp4.name}"'}
        )
    except Exception as e:
        print(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail="Error processing files")



###########################################   VMS VIDEO VIEW #####################################################

###########################################   VMS VIDEO VIEW #####################################################

###########################################   VMS VIDEO VIEW #####################################################
@router.get("/main/view/datatable/{project_id}/{camera_ip}/{detection_id}")
def drawline_update(request: Request, project_id: int, camera_ip: str, detection_id: str):
    try:
        db_session = next(get_db())

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        project = db_session.execute(
            text('SELECT project_id, project_name FROM project WHERE project_id = :project_id'),
            {'project_id': project_id}
        ).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Invalid project value")

        project_name = project[1]

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching records") from e
    finally:
        db_session.close()

    return templates.TemplateResponse("report_template/realtimereport.html", 
                                      {"request": request, 
                                       "project_name": project_name, 
                                       "camera_ip": camera_ip, 
                                       "project_id": project_id, 
                                       "detection_id": detection_id, 
                                       "session": session_data})



@router.get("/main/view/datatable/data/{project_id}/{camera_ip}/{detection_id}")
def fetch_datatable_data(
    request: Request,
    project_id: int,
    camera_ip: str,
    detection_id: str,
    start: int = 0,
    length: int = 10,
    search: str = Query(None)  
):
    try:
        print("kishore .................................. .")
        db_session = next(get_db())

        project = db_session.execute(
            text('SELECT project_id, project_name FROM project WHERE project_id = :project_id'),
            {'project_id': project_id}
        ).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Invalid project value")
        print("detection_id:",detection_id)
        
        det=db_session.query(Detection_log).filter(Detection_log.detection_id == detection_id).first()
        if det:
            print("mapped_polygon value:",det.mapped_polygon)
            print("line id :",det.line_id)
            analytics = det.mapped_polygon if not det.line_id else det.line_id
            print("analytics inside det:",analytics)
        print("analytics:",analytics)
        
    
        if analytics and analytics.startswith("polygon-"):
            table_name = "kit1_objectdetection"
            select_fields = '''
                r.id, r.date_time, r.direction, r.vehicle_id, 
                r.vehicle_class_id, COALESCE(cc.custom_class, r.ai_class) AS ai_class,
                r.image_path, r.mapped_line AS line_id, r.detection_id
            '''
        else:
            table_name = "kit1_objectdetection"
            select_fields = '''
                r.id, r.date_time, r.direction, r.vehicle_id, 
                r.vehicle_class_id, COALESCE(cc.custom_class, r.ai_class) AS ai_class,
                r.image_path, r.line_id, r.detection_id
            '''
            print("drawline . . . . . .")
            

        project_id = int(project[0])
        project_name = project[1]

        base_query = f'''
        FROM {table_name} r
        LEFT JOIN module_class_group mcg ON r.vehicle_class_id = mcg.m_classes_id
        LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id) AND mcc.custom_class_id = 1
        LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
        WHERE project_id = :project_id AND camera_ip = :camera_ip AND detection_id = :detection_id

        '''

        query_params = {
            'project_id': project_id,
            'camera_ip': camera_ip,
            'detection_id': detection_id
        }

      
        if search:
            if search.strip() in ["0", "1"]:  
                base_query += " AND r.direction = :direction"
                query_params['direction'] = int(search.strip()) 
            else:  
                base_query += " AND COALESCE(cc.custom_class, r.ai_class) ILIKE :vehicle_name"
                query_params['vehicle_name'] = f"%{search.strip()}%" 

        
        total_count_query = f"SELECT COUNT(*) {base_query}"
        total_count = db_session.execute(text(total_count_query), query_params).scalar()

        
        records_query = f'''
                    SELECT {select_fields}
                    {base_query}
                    ORDER BY r.id DESC
                    LIMIT :length OFFSET :start
                '''


        query_params.update({'length': length, 'start': start})

        records = db_session.execute(text(records_query), query_params).fetchall()

        results = []
        for record in records:
            modified_time = record[1].astimezone().strftime("%B %d, %Y, %I:%M:%S %p")
            image_path = record[6]
            ai_class = record[5]

            if not os.path.exists(image_path):
                image_path = "/movable/No_Image_found.jpg"
            else:
                detection_id_path_part = "/".join(image_path.split("/")[-3:])
                image_path = f'/movable/ATCC/{project_id}/{camera_ip}/{detection_id}/{detection_id_path_part}'

           

            if analytics and analytics.startswith("polygon-"):
   
                direction = os.path.basename(os.path.dirname(record[6])) 
                filename = os.path.basename(record[6]) 
                image_path = f"/movable/ATCC/{detection_id}/roi_cropped/{direction}/{filename}"


            line_id = record[7].replace("{", "").replace("}", "") if record[7] else 'polygon'
            
            print("image_path in view report:",image_path)

            results.append({
                "detection_id": record[8],
                "project_name": project_name,
                "vehicle_name": ai_class,
                "vehicle_id": record[3],
                "image_path": image_path,
                "direction": record[2],
                "date_time": modified_time,
                "line_id": line_id
            })

    except Exception as e:
        print(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail="Error fetching records") from e
    finally:
        db_session.close()

    return {"data": results, "recordsTotal": total_count, "recordsFiltered": total_count}


@router.delete('/main/detection/delete/{detection_id}')
async def delete_project(detection_id: str):
    try:
        print(f"Deleting detection_id: {detection_id}")
        db = next(get_db())


        # db.query(Detection_log).filter(
        #     Detection_log.detection_id == detection_id
            
        # ).delete()

        db.query(Detection_log).filter(
            Detection_log.detection_id == detection_id
        ).update(
            {Detection_log.cloud_delete: True}
        )

        db.query(cloud_vms).filter(       
            cloud_vms.detection_id == detection_id
        ).update({"row_status": "dlog_deleted"})

        #update the cloud status true for this detection log id;

        db.commit()
        return {"detail": "detection deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
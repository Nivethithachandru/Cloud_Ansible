from apps.main.models.model import Detection_log
from apps.main.routers.report.day_report import daily_download
from fastapi import FastAPI,APIRouter
from fastapi.responses import StreamingResponse
from datetime import datetime,timedelta
import io,os
from apps.main.database.db import get_db
from sqlalchemy import text
from fastapi.templating import Jinja2Templates


router=APIRouter()
app=FastAPI()
templates = Jinja2Templates(directory="apps/main/front_end/templates")
 

from main import previous_file_path


@router.get('/realtime/dayreport', response_class=StreamingResponse)
async def day_report(start_time: str, end_time: str, project_id: int, camera_ip: str, detection_id: int, line_id: str):
    db_session = next(get_db())

    first_entry = (
        db_session.query(Detection_log)
        .filter(Detection_log.project_id == project_id,
                Detection_log.camera_ip == camera_ip,
                Detection_log.detection_id == detection_id)
        .order_by(Detection_log.start_time.asc())
        .first()
    )

    last_entry = (
        db_session.query(Detection_log)
        .filter(Detection_log.project_id == project_id,
                Detection_log.camera_ip == camera_ip,
                Detection_log.detection_id == detection_id)
        .order_by(Detection_log.end_time.desc())
        .first()
    )

    start_date = first_entry.start_time if first_entry else None
    end_date = last_entry.end_time if last_entry else None
    if not end_date:
        end_date = datetime.now()
        
    print("line id in report:",line_id)
    
    #end_date += timedelta(days=1)

    print("Formatted Start Date:", start_date, project_id, camera_ip)
    print("Formatted End Date:", end_date)
    if line_id and line_id.startswith("polygon-"):
        print("its polygon")
    else:
        line_ids = [lid.strip() for lid in line_id.split(',')]

        all_line_ids_query = db_session.execute(text('SELECT DISTINCT line_id FROM kit1_objectdetection')).fetchall()
        all_line_ids = {row[0] for row in all_line_ids_query}

        resolved_line_ids = []
        for lid in line_ids:
            if lid == "line_id_3":
                resolved_line_ids.extend(["line_id_3_up", "line_id_3_down"])
            else:
                matched_ids = [db_lid for db_lid in all_line_ids if db_lid.startswith(lid)]
                if matched_ids:
                    resolved_line_ids.extend(matched_ids)
                else:
                    resolved_line_ids.append(lid)

        print(f"Resolved Line IDs: {resolved_line_ids}")

    project_query = db_session.execute(text('SELECT project_name FROM project WHERE project_id = :project_id'),
                                       {'project_id': project_id}).fetchall()
    project_name = project_query[0][0] if project_query else "Unknown"

    vehicle_classes_query = db_session.execute(text('SELECT custom_class FROM custom_classes')).fetchall()
    vehicle_classes = {row[0]: 0 for row in vehicle_classes_query}

    line_1_data = {}
    line_2_data = {}
    line_3_up_data = {}
    line_3_down_data = {}
    polygon_1_data={}
    polygon_2_data={}
    polygon_3_data={}
    vehicle_counts_up={}
    vehicle_counts_down={}

    if line_id and line_id.startswith("line_"):
        print("querying polygon data")
        for lid in resolved_line_ids:
            print("lid:",lid)
            kit1_data = db_session.execute(text(''' 
                SELECT r.id, r.date_time, r.vehicle_id, 
                    r.vehicle_class_id, COALESCE(cc.custom_class, r.ai_class) AS ai_class
                FROM kit1_objectdetection r
                LEFT JOIN module_class_group mcg ON r.vehicle_class_id = mcg.m_classes_id
                LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
                LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
                WHERE r.project_id = :project_id AND camera_ip = :camera_ip 
                    AND detection_id = :detection_id AND r.line_id = :line_id AND cc.id IS NOT NULL
                ORDER BY r.id DESC
            '''), {'project_id': project_id, 'camera_ip': camera_ip, 'detection_id': detection_id, 'line_id': lid}).fetchall()

            vehicle_counts = {
                (start_date + timedelta(days=x)).date().isoformat(): {
                    hour: {cls: 0 for cls in vehicle_classes} for hour in range(24)
                }
                for x in range((end_date - start_date).days + 2)
            }

            for row in kit1_data:
                date_time = row[1]
                vehicle_name = row[4]
                date_str = date_time.date().isoformat()
                hour = date_time.hour

                if date_str in vehicle_counts:
                    if vehicle_name in vehicle_counts[date_str][hour]:
                        vehicle_counts[date_str][hour][vehicle_name] += 1

        
            if lid == "line_id_1":
                line_1_data[lid] = vehicle_counts
            elif lid == "line_id_2":
                line_2_data[lid] = vehicle_counts
            elif lid == "line_id_3_up":
                line_3_up_data[lid] = vehicle_counts
            elif lid == "line_id_3_down":
                line_3_down_data[lid] = vehicle_counts
    else:
        vehicle_counts={}
        print("mapped_polygon:",line_id)
        if line_id =='polygon-up':
            mapped_polygon="up"
        elif line_id =='polygon-down':
            mapped_polygon="down"
        elif line_id =='polygon-up,down':
            print("$##")
            mapped_polygon="up,down"
        
        resolved_line_ids=line_id
            
        polygon_data = db_session.execute(text(''' 
                SELECT r.id, r.date_time, r.vehicle_id, 
                    r.vehicle_class_id, COALESCE(cc.custom_class, r.ai_class) AS ai_class,r.direction
                FROM kit1_objectdetection r
                LEFT JOIN module_class_group mcg ON r.vehicle_class_id = mcg.m_classes_id
                LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
                LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
                WHERE r.project_id = :project_id AND camera_ip = :camera_ip 
                    AND detection_id = :detection_id AND r.mapped_line = :mapped_polygon AND cc.id IS NOT NULL
                ORDER BY r.id DESC
            '''), {'project_id': project_id, 'camera_ip': camera_ip, 'detection_id': detection_id, 'mapped_polygon': mapped_polygon}).fetchall()

        vehicle_counts_up = {
            (start_date + timedelta(days=x)).date().isoformat(): {
                hour: {cls: 0 for cls in vehicle_classes} for hour in range(24)
            }
            for x in range((end_date - start_date).days + 1)
        }
        vehicle_counts_down = {

            (start_date + timedelta(days=x)).date().isoformat(): {
                hour: {cls: 0 for cls in vehicle_classes} for hour in range(24)
            }
            for x in range((end_date - start_date).days + 2)
        }

        for row in polygon_data:
            date_time = row[1]
            vehicle_name = row[4]
            direction = row[5]
            date_str = date_time.date().isoformat()
            hour = date_time.hour

            if mapped_polygon == "up,down":
                if direction == "North":
                    if date_str in vehicle_counts_up and vehicle_name in vehicle_counts_up[date_str][hour]:
                        vehicle_counts_up[date_str][hour][vehicle_name] += 1
                elif direction == "South":
                    if date_str in vehicle_counts_down and vehicle_name in vehicle_counts_down[date_str][hour]:
                        vehicle_counts_down[date_str][hour][vehicle_name] += 1
            else:
                if date_str in vehicle_counts_up and vehicle_name in vehicle_counts_up[date_str][hour]:
                    vehicle_counts_up[date_str][hour][vehicle_name] += 1

        if mapped_polygon == "up":
            polygon_1_data[line_id] = vehicle_counts_up
        elif mapped_polygon == "down":
            polygon_2_data[line_id] = vehicle_counts_up
        elif mapped_polygon == "up,down":
            polygon_3_data["up"] = vehicle_counts_up
            polygon_3_data["down"] = vehicle_counts_down
  
    print("-- - - - - -sLine 1 Data:", line_1_data)

    print("Line 2 Data:", line_2_data)
    print("Line 3 Up Data:", line_3_up_data)
    print("Line 3 Down Data:", line_3_down_data)
    print("polygon_1_data:",polygon_1_data)
    print("polygon 2 data:",polygon_2_data)
    print("polygon_3_data:",polygon_3_data)

    db_session.close()

    output = io.BytesIO()
    daily_download(project_name, line_id,camera_ip,vehicle_counts, vehicle_counts_up,vehicle_counts_down,vehicle_classes, start_date, end_date, 
                   line_1_data, line_2_data, line_3_up_data, line_3_down_data, output,resolved_line_ids,polygon_1_data,polygon_2_data,polygon_3_data)

    output.seek(0)

    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={"Content-Disposition": "attachment; filename=summary_Movable.xlsx"})
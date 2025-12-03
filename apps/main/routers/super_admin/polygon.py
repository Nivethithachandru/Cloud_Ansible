import json
from fastapi import APIRouter ,Request,HTTPException
from fastapi.responses import HTMLResponse
import base64
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from PIL import Image as PILImage
import os
from sqlalchemy import text
from sqlalchemy import or_, update
from apps.main.database.db import get_db
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
import base64
from sqlalchemy.exc import SQLAlchemyError
from apps.main.utils.jwt import *
from apps.main.routers.roles.auth_role import *


router=APIRouter()

templates = Jinja2Templates(directory="apps/main/front_end/templates")


@router.get("/main/polygon/frame/{project_id}/{camera_ip}")
def drawline_update(request: Request, project_id: int, camera_ip: str):
    db = next(get_db())
    print("project_id:",project_id)
    print("camera_ip:",camera_ip)

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

   
    all_camera_ip = [camera.camera_ip for camera in db.query(LpuGroup.camera_ip).distinct().all()]
    print("@$%#@%#$^$%^$%&",all_camera_ip)


    if not project_id or not camera_ip:
        raise HTTPException(status_code=400, detail="Missing project_id or camera_ip")

    polygons = db.query(Polygon_details).filter(
        Polygon_details.project_id == project_id,
        Polygon_details.camera_ip == camera_ip
    ).all()
    print("polygons", polygons)

    polygon_list = [
    {"coordinates": poly.coordinates} for poly in polygons
]
    print("polygons", polygon_list)
   
    context = {
        'request': request,
        "session": session_data,
        'camera_details': all_camera_ip,
        'polygon_list': json.dumps(polygon_list),
        'project_id': project_id,  
        'camera_ip': camera_ip,   
    }  
    return templates.TemplateResponse("super_admin/draw_line/polygon.html", context)

from typing import List, Dict, Any

@router.post("/main/polygon/Polygon_coords")
async def update_polygon(request: Request):
    try:
        data = await request.json()
        print("In polygon:", data)

        project_id = data.get("project_id")
        camera_ip = data.get("camera_ip")
        points = data.get("points")
        polygon = data.get('polygon')
        print("polygon_id:", polygon)

        if not project_id or not camera_ip or not polygon:
            raise HTTPException(status_code=400, detail="Missing required fields: project_id, camera_ip, points, or polygon")

        print("camera_ip:", camera_ip)
        print("project_id:", project_id)
        print("points before rounding:", points)

        formatted_points = [{f"x{i}": int(point['x']), f"y{i}": int(point['y'])} for i, point in enumerate(points, start=1)]
        polygon_entry = [polygon] + formatted_points
        print("Formatted Polygon Entry:", polygon_entry)

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        lpu_id = session_data.get("lpu_id")
        if not lpu_id:
            raise HTTPException(status_code=400, detail="LPU ID not found in session")

        db = next(get_db())

        existing_polygon = db.query(Polygon_details).filter(
            Polygon_details.project_id == project_id,
            Polygon_details.camera_ip == camera_ip
        ).first()

        if existing_polygon:
            if not isinstance(existing_polygon.coordinates, list):
                existing_polygon.coordinates = []

            updated_coords = []
            replaced = False

            for poly in existing_polygon.coordinates:
                if isinstance(poly, list) and len(poly) > 0 and poly[0] == polygon:
                    updated_coords.append(polygon_entry)  
                    replaced = True
                else:
                    updated_coords.append(poly)

            if not replaced:
                updated_coords.append(polygon_entry) 

            existing_polygon.coordinates = updated_coords
            existing_polygon.updated_status = True
            db.commit()

            return {"success": True, "message": f"{polygon} updated successfully"}


        else:
          
            new_polygon = Polygon_details(
                project_id=project_id,
                camera_ip=camera_ip,
                coordinates=[polygon_entry],
                lpu_id=lpu_id,
                updated_status=True
            )
            db.add(new_polygon)
            db.commit()
            return {"success": True, "message": f"{polygon} added successfully as new"}
        
    except HTTPException as http_err:
        raise http_err
    except SQLAlchemyError as db_err:
        print(f"Database error: {db_err}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")



@router.get("/polygon/datatable")
async def get_polygon_data(request: Request):
    db = next(get_db())
    print("IN POLYGON: #@$@@@@@@@@@")
    project_id = request.query_params.get("project_id")
    camera_ip = request.query_params.get("camera_ip")

    if not project_id or not camera_ip:
        raise HTTPException(status_code=400, detail="Missing project_id or camera_ip")

    polygons = db.query(Polygon_details).filter(
        Polygon_details.project_id == project_id,
        Polygon_details.camera_ip == camera_ip
    ).all()

    formatted_data = []

    for polygon in polygons:
        if polygon.coordinates:
            for polygon_data in polygon.coordinates: 
                if not polygon_data:
                    continue
                polygon_name = polygon_data[0]  
                print("polygon name:",polygon_name)
               
                coords = []

                for coord in polygon_data[1:]:  
                    x = next((v for k, v in coord.items() if isinstance(k, str) and k.startswith("x")), None)
                    y = next((v for k, v in coord.items() if isinstance(k, str) and k.startswith("y")), None)
                    if x is not None and y is not None:
                        coords.append(f"({x},{y})")

                formatted_data.append({
                    "polygon": polygon_name,
                    "coordinates": "".join(coords),
                   
                })

    print("Formatted Data:", formatted_data)

    return {"data": formatted_data}



def export_roi_data_to_excel(project_id,camera_ip,output_file="ROI_Detection_Report.xlsx"):
  

    try:
        db=next(get_db())
      
        roi_data = db.query(Roi_detection).filter(
            Roi_detection.project_id == project_id,
            Roi_detection.camera_ip == camera_ip,
        ).all()


        wb = Workbook()
        ws = wb.active
        ws.title = "ROI Detections"
        headers = ["Date & Time", "Vehicle ID","Project ID", "Camera IP","AI Class",
                   "Direction","Image"]
        ws.append(headers)

        for idx, record in enumerate(roi_data, start=2):
            ws.append([
                record.date_time,
                record.vehicle_id,
                record.project_id,
                record.camera_ip,
                record.ai_class,
                record.direction
                
            ])

         
            if record.image_path and os.path.exists(record.image_path):
                try:
                    with PILImage.open(record.image_path) as img:
                        img.thumbnail((100, 100))
                        temp_path = f"temp_thumb_{idx}.png"
                        img.save(temp_path)

                        excel_img = ExcelImage(temp_path)
                        ws.add_image(excel_img, f"J{idx}")
                        os.remove(temp_path)
                except Exception as img_err:
                    print(f" Image error at row {idx}: {img_err}")
            else:
                print(f" Image not found: {record.image_path}")

       
        wb.save(output_file)
        print(f" Excel file '{output_file}' created successfully.")

    except Exception as e:
        print(f" Error exporting to Excel: {e}")

from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.jwt import *
from fastapi.templating import Jinja2Templates
from apps.main.routers.roles.auth_role import *
from sqlalchemy import text


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")

@router.get("/main/roi/frame/{project_id}/{camera_ip}")
async def roi_mapping_update(request: Request, project_id: int, camera_ip: str):
    try:
        db = next(get_db())
        print("project_id:",project_id)
        print("camera_ip:",camera_ip)

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        project_details = db.query(Project).filter(Project.id == project_id).first()

        context = {
            'request': request,
            "session": session_data,
            'project_id': project_id, 
            'project_name':project_details.project_name, 
            'camera_ip': camera_ip,   
        }
        return templates.TemplateResponse("super_admin/roi/roi.html", context)
    
    except Exception as e:
        print("Roi Mapping error,",e)


@router.get('/main/roi', response_class=HTMLResponse, name="main.roi")
async def group_classes_management(request: Request):
    db = next(get_db())   

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")   

    role_id = session_data.get('role_id')
    modulee_id = 7
    show_required_permission = "show" 
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    


    if role_id == 0:
        return templates.TemplateResponse("super_admin/roi/roi.html", 
                                    {"request": request,
                                
                                     "session": session_data
                                     })
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/roi/roi.html", 
                                    {"request": request,
                        
                                     "session": session_data
                                     })
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)
        

@router.get('/main/line_count/{camera_ip}/{project_id}', response_class=JSONResponse)
async def get_line_count(camera_ip: str, project_id: str):
    try:
        print("Fetching line crossing data...", camera_ip, project_id)
        db = next(get_db())
        
        detection_details = db.query(Detection_details).filter(
            Detection_details.project_id == project_id,
            Detection_details.camera_ip == camera_ip
        ).first()

        if not detection_details or not detection_details.line_crossing:
            raise HTTPException(status_code=400, detail="No line crossing data found")

        line_crossing = detection_details.line_crossing
        print("Line crossing data:", line_crossing)

        valid_lines = {
            line_id: line_data for line_id, line_data in line_crossing.items()
            if line_data.get('topx') not in ['null', None] and line_data.get('topy') not in ['null', None]
            and line_data.get('bottomx') not in ['null', None] and line_data.get('bottomy') not in ['null', None]
        }

        print("Filtered line_crossing:", valid_lines)

        line_ids = list(valid_lines.keys())
        print("Valid line IDs:", line_ids)

        polygon_entry = db.query(Polygon_details).filter(
            Polygon_details.camera_ip == camera_ip,
            Polygon_details.project_id == project_id
        ).first()

        valid_polygons = {}
        polygon_options={}
        if polygon_entry and polygon_entry.coordinates:
            try:
                coordinates = polygon_entry.coordinates
                for polygon in coordinates:
                    if len(polygon) > 1 and isinstance(polygon[1], dict):  
                        valid_polygons[polygon[0]] = polygon[1:]  
            except Exception as e:
                print(f"Polygon parsing failed: {e}")

        
        polygon_options = {name: "up" if idx == 0 else "down" for idx, name in enumerate(valid_polygons)}
        print("poly options:",polygon_options)

        mapping_ids = db.query(ROIMapping).filter(
            ROIMapping.camera_ip == camera_ip,
            ROIMapping.project_id == project_id
        ).first()
       

        existing_polygon = []  
        if mapping_ids:
            print("existing mapped polygon:", mapping_ids.polygon)
            existing_polygon = mapping_ids.polygon if mapping_ids.polygon else []
            print("existing polygon id:",existing_polygon)


        existing_mapping_ids = list(mapping_ids.lineid.split(',')) if mapping_ids and mapping_ids.lineid else []
        print("Existing mapping line ids:", existing_mapping_ids)



        return JSONResponse(content={"line_ids": line_ids, "line_count": len(line_ids), "existing_mapping": existing_mapping_ids,"existing_polygon":existing_polygon,"poly_options":polygon_options})
    
    except Exception as e:
        print(f"Error occurred: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    

# @router.post('/main/mapping_line/update')
# async def roi_map(request: Request):
#     data = await request.json()

#     project_id = data.get('project_id')
#     camera_ips = data.get('camera_ip')
#     line_id = data.get('line_id')

#     session_data, error_response = handle_session(request)
#     if error_response:
#         return RedirectResponse(url="/")

#     print("Received data:")
#     print(f"project_id: {project_id}")
#     print(f"camera_ips: {camera_ips}")
#     print(f"line_id: {line_id}")

#     if not all([project_id, camera_ips]):
#         raise HTTPException(status_code=400, detail="Missing required fields")

#     db_session = next(get_db())
#     lpu_id=session_data['lpu_id']

#     lpu_record = db_session.query(Lpu_management).filter(
#             Lpu_management.lpu_id == lpu_id, 
#             Lpu_management.lpu_status == False  
#         ).all()

#     print("lpu_records:",lpu_record)

#     if lpu_record:
#         raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update ROI Mapping -LPU ID '{id}'.")

#     existing_mapping = db_session.query(ROIMapping).filter(
#         ROIMapping.project_id == project_id,
#         ROIMapping.camera_ip == camera_ips,
        
#     ).first()

    

#     if existing_mapping:
        
#         existing_mapping.lineid = line_id
#         existing_mapping.updated_status = True
#         db_session.commit()
#         return {"message": "ROI mapping updated successfully"}
#     else:
        
#         mapping = ROIMapping(
#             project_id=project_id,
#             camera_ip=camera_ips,
#             lineid=line_id,
#             updated_status = True
#         )
#         db_session.add(mapping)
#         db_session.commit()
#         return {"message": "ROI mapping added successfully"}


# @router.post('/main/mapping_line/update')
# async def roi_map(request: Request):
#     data = await request.json()

#     project_id = data.get('project_id')
#     camera_ips = data.get('camera_ip')
#     line_id = data.get('line_id')

#     session_data, error_response = handle_session(request)
#     if error_response:
#         return RedirectResponse(url="/")

#     print("Received data:")
#     print(f"project_id: {project_id}")
#     print(f"camera_ips: {camera_ips}")
#     print(f"line_id: {line_id}")

#     if not all([project_id, camera_ips]):
#         raise HTTPException(status_code=400, detail="Missing required fields")

#     db_session = next(get_db())
#     lpu_id = session_data['lpu_id']

#     lpu_record = db_session.query(Lpu_management).filter(
#         Lpu_management.lpu_id == lpu_id, 
#         Lpu_management.lpu_status == False  
#     ).all()

#     print("lpu_records:", lpu_record)

#     if lpu_record:
#         raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update ROI Mapping - LPU ID '{lpu_id}'.")

#     existing_mapping = db_session.query(ROIMapping).filter(
#         ROIMapping.project_id == project_id,
#         ROIMapping.camera_ip == camera_ips,
#     ).first()

 
#     is_polygon = line_id in ["up", "down"]

#     if existing_mapping:
#         if is_polygon:
#             existing_mapping.polygon = line_id
#         else:
#             existing_mapping.lineid = line_id
#         existing_mapping.updated_status = True
#         db_session.commit()
#         return {"message": "ROI mapping updated successfully"}
#     else:
#         mapping = ROIMapping(
#             project_id=project_id,
#             camera_ip=camera_ips,
#             polygon=line_id if is_polygon else None,
#             lineid=None if is_polygon else line_id,
#             updated_status=True
#         )
#         db_session.add(mapping)
#         db_session.commit()
#         return {"message": "ROI mapping added successfully"}





@router.post('/main/mapping_line/update')
async def roi_map(request: Request):
    data = await request.json()

    project_id = data.get('project_id')
    camera_ips = data.get('camera_ip')
    line_id = data.get('line_id')
    selected = data.get('selected')

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    print(f"Received data:\nproject_id: {project_id}\ncamera_ips: {camera_ips}\nline_id: {line_id}\nselected value: {selected}")

    if not all([project_id, camera_ips]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    db_session = next(get_db())
    lpu_id = session_data.get('lpu_id')

    lpu_record = db_session.query(Lpu_management).filter(
        Lpu_management.lpu_id == lpu_id,
        Lpu_management.lpu_status == False
    ).all()

    print("lpu_records:", lpu_record)

    if lpu_record:
        raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update ROI Mapping - LPU ID '{lpu_id}'.")

    existing_mapping = db_session.query(ROIMapping).filter(
        ROIMapping.project_id == project_id,
        ROIMapping.camera_ip == camera_ips,
    ).first()

    
    line_id_str = ','.join(line_id) if isinstance(line_id, list) else (line_id or "")
    print("line_id_str:", line_id_str)

    if existing_mapping:
        if selected == "polygon":
            existing_mapping.polygon = line_id_str
            
        else:
            existing_mapping.lineid = line_id_str
         
        existing_mapping.updated_status = True
        db_session.commit()
        return {"message": "ROI mapping updated successfully"}
    else:
        mapping = ROIMapping(
            project_id=project_id,
            camera_ip=camera_ips,
            polygon=line_id_str if selected == "polygon" else None,
            lineid=line_id_str if selected != "polygon" else None,
            updated_status=True
        )
        db_session.add(mapping)
        db_session.commit()
        return {"message": "ROI mapping added successfully"}



@router.get('/roi/camera_ip/{project_id}', response_class=JSONResponse)
async def get_camera_ip(project_id: str):
    try:
        db_session = next(get_db())  
        print("project_id:",project_id)
      
        result = db_session.execute(text('SELECT camera_ip FROM project WHERE project_id = :project_id'), {'project_id':project_id}).fetchone()
        print("camera_ip:####:",result)
        if result:
            return {"camera_ip": result[0]}  
        else:
            raise HTTPException(status_code=404, detail="Camera not found")
    except Exception as e:
        print(f"Error fetching camera status: {e}")
        raise HTTPException(status_code=500, detail="Error fetching camera status") from e
    finally:
        db_session.close()




##############################  TO CHECK WHETHER LINE CAN BE CLEARED OR NOT BASED ON MAPPED LINES ####################################

@router.post('/main/roi_unmap')
async def roi_unmap(request: Request):
    data = await request.json()
    project_id = data.get('project_id')
    line_id = data.get('lineNumber')
    camera_ip= data.get('camera_ip')

    print("line number:", line_id,camera_ip)
    print("project_id:", project_id)

    db_session = next(get_db())

    existing_mapping = db_session.query(ROIMapping).filter(
        ROIMapping.project_id == project_id,
        ROIMapping.camera_ip == camera_ip
    ).first()

    formatted_line_id = f"line_id_{line_id}"

    if not existing_mapping:
        return {"message": f"No mapping details found. Line ID {formatted_line_id} can be cleared."}

    if existing_mapping.lineid and formatted_line_id in existing_mapping.lineid:
        raise HTTPException(status_code=400, detail=f"Line ID {formatted_line_id} is mapped to project {project_id} and cannot be cleared")

    return {"message": f"Line ID {formatted_line_id} is not mapped and can be cleared"}


   

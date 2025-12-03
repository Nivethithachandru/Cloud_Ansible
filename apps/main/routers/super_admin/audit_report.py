from fastapi import  APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.jwt import * 
from apps.main.utils.session import * 
from sqlalchemy import text
import os
from datetime import datetime
from main import STORE_ROOT
from apps.main.config import *
from logg import *


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")

 

@router.get('/main/report/audit/', response_class=HTMLResponse, name="main.report_preview")
async def report_management(request: Request):
    
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db())   
    modulee_id = 10
    show_required_permission = "show" 
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    lpu_groups = db.query(LpuGroup).all() 
    lpu_dropdown_data = [{"id": lpu.id,"lpu_id":lpu.lpu_id ,"name": lpu.lpu_name} for lpu in lpu_groups]
  
    mapping_custom_classes = (
        db.query(MappingCustomClasses, CustomClasses.custom_class)
        .join(CustomClasses, MappingCustomClasses.custom_class_id == CustomClasses.id)
        .all()
    )

    module_classes = {m_class.m_classes_id: m_class.m_classes_name for m_class in db.query(ModuleClassesGroup).all()}

    custom_class_group_data = []
    for mcc in mapping_custom_classes:
        model_class_ids = mcc.MappingCustomClasses.model_class_id
        model_class_names = [module_classes.get(class_id, "Unknown") for class_id in model_class_ids]

        model_classes = [{"id": class_id, "name": class_name} for class_id, class_name in zip(model_class_ids, model_class_names)]

        custom_class_group_data.append({
            "id": mcc.MappingCustomClasses.id,
            "custom_class_name": mcc.custom_class,
            "model_classes": model_classes  
        })

    if role_id == 0:

        required_permission_s = True
        
        return templates.TemplateResponse("super_admin/report/report.html", 
                                        {"request": request,
                                          "lpu_dropdown": lpu_dropdown_data,
                                        'page_permission':required_permission_s,
                                        'custom_classes':custom_class_group_data,
                                        'AUDIT_DATE_FILTER':AUDIT_DATE_FILTER,
                                        "session": session_data}
                                        )
     
    else:
        if show_required_permission:
            required_permission= "read"
            required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
            print("required_permission",required_permission)

            return templates.TemplateResponse("super_admin/report/report.html", 
                                        {"request": request, 
                                          "lpu_dropdown": lpu_dropdown_data,
                                           'custom_classes':custom_class_group_data,
                                        'AUDIT_DATE_FILTER':AUDIT_DATE_FILTER,
                                        'page_permission':required_permission,
                                        "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)


async def fetch_custom_class1(db, m_classes_name):
    module_class_query = text('''
        SELECT m_classes_id FROM module_class_group WHERE m_classes_name = :m_classes_name
    ''')
    module_class_result = db.execute(module_class_query, {"m_classes_name": m_classes_name}).fetchone()

    if module_class_result:
        m_classes_id = module_class_result[0]

        mapping_query = text('''
            SELECT custom_class_id FROM mapping_custom_classes 
            WHERE :m_classes_id = ANY(model_class_id::int[])
        ''')
        mapping_result = db.execute(mapping_query, {"m_classes_id": m_classes_id}).fetchone()
        print("mapping_result:",mapping_result)

        if mapping_result:
            custom_class_id = mapping_result[0]

            custom_class_query = text('''
                SELECT custom_class FROM custom_classes WHERE id = :custom_class_id
            ''')
            custom_class_result = db.execute(custom_class_query, {"custom_class_id": custom_class_id}).fetchone()
            print("#%^$^")
            if custom_class_result:
                print("custom class result:",custom_class_result)
                return custom_class_result[0]  

    return None  


 
def get_audited_class_name(db, m_classes_id):
    audited_class = db.query(ModuleClassesGroup).filter(ModuleClassesGroup.m_classes_id == m_classes_id).first()    
    if audited_class:
        print("rtrty",audited_class)
        return audited_class.m_classes_name
    else:
        return None
    

def get_user_pid_by_username(db, user_name):
    user = db.query(UserGroup).filter(UserGroup.user_name == user_name).first()
    if user:
        return user.id
    else:
        return None


def get_lpu_id_by_kit_name(db, kit_name):
    lpu_group = db.query(LpuGroup).filter(LpuGroup.lpu_name == kit_name).first()
    if lpu_group:
        return lpu_group.lpu_id   
    return None

def get_playstreamid_by_objectid(db,id,table_name,vms_table_name):
    
    query = text(f"""
        SELECT play_stream_id 
        FROM {table_name}
        WHERE id = :id
    """)
    result = db.execute(query, {"id":id}).fetchone()
    play_stream_id =result.play_stream_id

    query_update = text(f"""
        UPDATE {vms_table_name} 
        SET  file_upload = False
        WHERE id = :play_stream_id
    """)

    db.execute(query_update, {
        "play_stream_id": play_stream_id   
    })
    return play_stream_id if result else None



def update_combine_kit_audit_upload_status(db, play_stream_id):
    try:
        print("play_stream_id:", play_stream_id)
        
        query_update = text(""" 
            UPDATE combined_kit 
            SET audit_upload = TRUE
            WHERE :kit1_vms_id = ANY(kit1_vms_id) OR :kit2_vms_id = ANY(kit2_vms_id)
        """)
        result = db.execute(
            query_update, 
            {"kit1_vms_id": play_stream_id, "kit2_vms_id": play_stream_id}
        )
       
        db.commit()
        print("Update committed combined audit flag status successfully.")
    except Exception as e:
        print("Error updating combined kit data:", e)
        db.rollback()


def get_createdtime_by_id(db, id, table_name):
    query = text(f"""
        SELECT date_time
        FROM {table_name}
        WHERE id = :id
    """)
    result = db.execute(query, {"id": id}).fetchone()
    print("get created time by id:",result)
    return result.date_time if result else None





@router.post('/main/report/update_audited_class/')
async def update_audited_class(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())
    try:

        data = await request.json()
        id = data.get('id')        
        vehicle_id = data.get('vehicle_id')
        ai_class = data.get('ai_class')
        m_classes_id = data.get('audited_class')   
        print(f'*******kishore*************  {id} ----  {vehicle_id} ----  {ai_class} ---- {m_classes_id} ---- ')
        print("#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",data)
        role_id = session_data.get('role_id')
        s_user_name = session_data.get('user_name')
        print("fgrfryht",role_id,s_user_name)

        project_id=data.get('project_id')
        camera_ip=data.get('camera_ip')

        table_name="kit1_objectdetection"
        print("table:",table_name,project_id,camera_ip)


        # lpu_id = get_lpu_id_by_kit_name(db, kit_name)


        # play_stream_id = get_playstreamid_by_objectid(db, id,table_name,vms_table_name)
        # print("play_stream_id",play_stream_id)



        # Get the audited class name
        audited_class_name = get_audited_class_name(db, m_classes_id)
        print("audited class name:",audited_class_name)
        # if audited_class_name is None:
             
        #     raise HTTPException(status_code=400, detail="Audited class not found.")

        query = text(f'''
            UPDATE kit1_objectdetection
            SET ai_class = :ai_class, audited_class = :audited_class, is_audit = TRUE, last_modified = :user_id,
            vehicle_class_id = :vehicle_class_id
            WHERE id = :id  
        ''')
        
        if role_id == 0:
            user_pid = 0
            print("##3user_pid:",user_pid)
        else:
            user_pid = get_user_pid_by_username(db, s_user_name)
            print("user_pid:",user_pid)


        print("user name:",user_pid)
        print("audited class name:",audited_class_name)
        print("custom audit class:",m_classes_id)
        

        result = db.execute(query, {
            "id": id,
            "ai_class": audited_class_name,
            "audited_class": audited_class_name,
            "user_id": user_pid,  
            "vehicle_class_id": m_classes_id  
        })
        print("result:",result)
        # update_combine_kit_audit_upload_status(db, play_stream_id)
        if result.rowcount > 0:
            print("%^^%$&")
            db.commit()

            

            custom_audit_class = await fetch_custom_class1(db, audited_class_name)
            
            if custom_audit_class is None:
                custom_audit_class = audited_class_name
            # AUDIT_LOGGER.info(
            #     f"[AUDIT] - Vehicle ID '{vehicle_id}' changed from vehicle name '{ai_class}' to '{audited_class_name}' "
            #     f"with AI classification '{custom_audit_class}'. Update performed by user '{s_user_name}'."
            # )

            actual_datetime = get_createdtime_by_id(db, id, table_name)
            print("actual:",actual_datetime,vehicle_id,id)

            try:
                existing_audit_log = db.query(Audit_activity).filter(
                
                    Audit_activity.obj_pid == id,
                    Audit_activity.vehicle_id == vehicle_id,
                ).first()

                print("existing audit log:",existing_audit_log)
                if existing_audit_log:
                    print("existing audit %^$6y5",user_pid)
                    existing_audit_log.m_classes_id = m_classes_id
                    existing_audit_log.last_modified = user_pid
                    existing_audit_log.updated_at = datetime.now() 
                    existing_audit_log.camera_ip =camera_ip 
                    existing_audit_log.project_id =project_id 
         
                else:
                    new_audit_log = Audit_activity(
                        obj_pid = id,
                        vehicle_id=vehicle_id,
                        m_classes_id=m_classes_id,
                        last_modified=user_pid,
                        actual_datetime=actual_datetime,
                        updated_at=datetime.now(),
                        project_id=project_id,
                        camera_ip =camera_ip
                    )
                    db.add(new_audit_log)
                    print("new audit log:",new_audit_log)
                    db.commit()
            except Exception  as e:
                print("Error audit ",e)

            
           

            print("user name:",s_user_name)
            print("audited class name:",audited_class_name)
            print("custom audit class:",custom_audit_class)



 
            return {
                "status": "success", 
                "message": "Audited class updated successfully.",
                "updated_audit_class1": audited_class_name,
                "updated_audit_class": custom_audit_class,
                "last_updated_username":  s_user_name
            }
        else:
            raise HTTPException(status_code=404, detail="Record not found.")

    except Exception as e:
        AUDIT_LOGGER.error(
            f"[ERROR] - Failed to update Vehicle ID '{vehicle_id}' from vehicle name '{ai_class}' to '{audited_class_name}' "
            f"with AI classification '{custom_audit_class}'. Reason: {e}. "
            f"Attempted update performed by user '{s_user_name}'."
        )





@router.get('/main/audit/transaction/', response_class=HTMLResponse, name="main.report_list_preview")
async def report_logs_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db()) 
    modulee_id = 11
    show_required_permission = "show" 
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    lpu_groups = db.query(LpuGroup).all() 
    lpu_dropdown_data = [{"id": lpu.id,"lpu_id":lpu.lpu_id ,"name": lpu.lpu_name} for lpu in lpu_groups]
  
    if role_id == 0:
        required_permission_s = True        
        return templates.TemplateResponse("super_admin/report/report_transaction.html", 
                                        {"request": request, 
                                        'page_permission':required_permission_s,
                                          "lpu_dropdown": lpu_dropdown_data,  
                                        'AUDIT_DATE_FILTER':AUDIT_DATE_FILTER,                                     
                                        "session": session_data}
                                        )     
    else:
        if show_required_permission:
            required_permission= "read"
            required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
            print("required_permission",required_permission)
            return templates.TemplateResponse("super_admin/report/report_transaction.html", 
                                        {"request": request,                                           
                                        'page_permission':required_permission,
                                        'AUDIT_DATE_FILTER':AUDIT_DATE_FILTER,
                                          "lpu_dropdown": lpu_dropdown_data,
                                        "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)

 
@router.get('/main/report/query/filter_data/')
async def filter_audite_datarange(
    request: Request,
    project_id: int,
    camera_ip: str,
    from_date: str,
    to_date: str,
    start: int = 0,
    length: int = 10,
    search: str = ""  
): 
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        db = next(get_db()) 

        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            print("from date:",from_date)
        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            print("to date:",to_date)

        kit1_data = db.execute(text('''
            SELECT r.id, r.date_time, r.vehicle_id, r.vehicle_name,
                    COALESCE(cc.custom_class, r.ai_class) AS ai_class, 
                    r.audited_class, r.direction, r.image_path, r.last_modified,r.detection_id,r.mapped_line
            FROM kit1_objectdetection r
            LEFT JOIN module_class_group mcg ON r.ai_class = mcg.m_classes_name
            LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
            LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
            WHERE r.date_time >= :from_date AND r.date_time <= :to_date 
                    AND r.project_id = :project_id AND r.camera_ip = :camera_ip 
                    AND cc.id IS NOT NULL                                    
                    AND (
                        CAST(r.vehicle_id AS TEXT) ILIKE :search OR
                        r.vehicle_name ILIKE :search OR
                        r.ai_class ILIKE :search OR
                        r.audited_class ILIKE :search
                    )
            ORDER BY r.id DESC
            LIMIT :limit OFFSET :offset
        '''), {
            'from_date': from_date, 
            'to_date': to_date, 
            'project_id': project_id, 
            'camera_ip': camera_ip,
            'limit': length,
            'offset': start,
            'search': f"%{search}%" 

        }).fetchall()


        if not kit1_data:
            return JSONResponse(content={"data": [], "recordsTotal": 0, "recordsFiltered": 0})

        # Count total rows (without pagination)
        total_count = db.execute(text('''
            SELECT COUNT(*) 
            FROM kit1_objectdetection r
            LEFT JOIN module_class_group mcg ON r.ai_class = mcg.m_classes_name
            LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
            LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
            WHERE r.date_time >= :from_date 
              AND r.date_time <= :to_date 
              AND r.project_id = :project_id 
              AND r.camera_ip = :camera_ip 
              AND cc.id IS NOT NULL
        '''), {
            'from_date': from_date,
            'to_date': to_date,
            'project_id': project_id,
            'camera_ip': camera_ip
        }).scalar()


        report_list = []
        for row in kit1_data:
            formatted_date_time = row[1].astimezone().strftime("%b %d, %Y , %I:%M:%S %p")
            analytics=row[6]
            image_path = row[7] if row[7] else "/movable/No_Image_found.jpg"
            filename = os.path.basename(image_path) if image_path else "No_Image_found.jpg"

            detection_id_path_part = "/".join(image_path.split("/")[-3:])  
            detection_id=row[9]
            print("$%#^$%:",detection_id_path_part)

            checking_local_image_path = os.path.join(image_path)
            
            if not os.path.exists(checking_local_image_path):
                image_path = "/movable/No_Image_found.jpg"
            else:
                image_path = f'/movable/ATCC/{project_id}/{camera_ip}/{detection_id}/{detection_id_path_part}'
            print("analytics :",analytics)
            if analytics and (analytics.startswith("South") or analytics.startswith("North")):
                print("in else")

                direction = os.path.basename(os.path.dirname(row[7])) 
                filename = os.path.basename(row[7]) 
                image_path = f"/movable/ATCC/{detection_id}/roi_cropped/{direction}/{filename}"
            print("image_path:",image_path)
            report_list.append({
                "id": row[0],
                "vehicle_id": row[2],
                "vehicle_name": row[3],
                "ai_class": row[4],
                "audited_class": row[5],
                "direction": row[6],
                "image_path": image_path,
                "date_time": formatted_date_time,
                "last_modified": row[8],
                "detection_id" :row[9]
            })


        # return JSONResponse(content={"data": report_list})
        return JSONResponse(content={
            "data": report_list,
            "recordsTotal": total_count,
            "recordsFiltered": total_count
        })

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    
@router.post('/main/report/filter_data/')
async def filter_data_range(request: Request):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        with next(get_db()) as db:  # Ensure DB session closes properly

            data = await request.json()
            project_id = data.get('project_id')
            camera_ip = data.get('camera_ip')
            from_date = data.get('from_date')
            to_date = data.get('to_date')

            print("data:",data)

            if from_date:
                print("#$^^^^^^^^^^^^^")
                from_date = datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                print("from date:",from_date)
            if to_date:
                print("@@@@@@@@@@@@@2")
                to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                print("to date:",to_date)

            kit1_data = db.execute(text('''
                SELECT r.id, r.date_time, r.vehicle_id, r.vehicle_name,
                       COALESCE(cc.custom_class, r.ai_class) AS ai_class, 
                       r.audited_class, r.direction, r.image_path, r.last_modified,r.detection_id,r.mapped_line
                FROM kit1_objectdetection r
                LEFT JOIN module_class_group mcg ON r.ai_class = mcg.m_classes_name
                LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
                LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
                WHERE r.date_time >= :from_date AND r.date_time <= :to_date 
                      AND r.project_id = :project_id AND r.camera_ip = :camera_ip 
                      AND cc.id IS NOT NULL
                ORDER BY r.id DESC
            '''), {
                'from_date': from_date, 
                'to_date': to_date, 
                'project_id': project_id, 
                'camera_ip': camera_ip
            }).fetchall()
            print("%%%%%%%%%$$$^%^&^&&$###$")
            print("$#%#$^ kit1 data:",kit1_data)
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

            if not kit1_data:
                return JSONResponse(content={"data": []})  # No data found case

            report_list = []
            for row in kit1_data:
                formatted_date_time = row[1].astimezone().strftime("%b %d, %Y , %I:%M:%S %p")
                analytics=row[6]
                image_path = row[7] if row[7] else "/movable/No_Image_found.jpg"
                filename = os.path.basename(image_path) if image_path else "No_Image_found.jpg"

                detection_id_path_part = "/".join(image_path.split("/")[-3:])  
                detection_id=row[9]
                print("$%#^$%:",detection_id_path_part)

                checking_local_image_path = os.path.join(image_path)
                
                if not os.path.exists(checking_local_image_path):
                    image_path = "/movable/No_Image_found.jpg"
                else:
                    image_path = f'/movable/ATCC/{project_id}/{camera_ip}/{detection_id}/{detection_id_path_part}'
                print("analytics :",analytics)
                if analytics and (analytics.startswith("South") or analytics.startswith("North")):
                    print("in else")
   
                    direction = os.path.basename(os.path.dirname(row[7])) 
                    filename = os.path.basename(row[7]) 
                    image_path = f"/movable/ATCC/{detection_id}/roi_cropped/{direction}/{filename}"
                print("image_path:",image_path)
                report_list.append({
                    "id": row[0],
                    "vehicle_id": row[2],
                    "vehicle_name": row[3],
                    "ai_class": row[4],
                    "audited_class": row[5],
                    "direction": row[6],
                    "image_path": image_path,
                    "date_time": formatted_date_time,
                    "last_modified": row[8],
                    "detection_id" :row[9]
                })

                print("report_list:",report_list)

        return JSONResponse(content={"data": report_list})

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    




@router.post('/main/report/transaction_audit_filter/')
async def recent_audit_filter_data_range(request: Request):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        db = next(get_db())

        data = await request.json()
      
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        project_id = data.get('project_id')
        camera_ip = data.get('camera_ip')
 
       
        table_name = 'kit1_objectdetection'
        
        
        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
 
        result = db.execute(text('''
                    SELECT
                        r.vehicle_id,
                        COALESCE(MAX(cc.custom_class), r.ai_class) AS ai_class,  
                        COALESCE(MAX(cc.custom_class), r.audited_class) AS audited_class,
                        r.vehicle_name,
                        r.direction,
                        r.image_path,
                        r.date_time,
                        r.detection_id,
                        al.last_modified AS audit_last_modified,
                        al.updated_at,
                        r.ai_class
                    FROM kit1_objectdetection r
                    LEFT JOIN module_class_group mcg ON r.ai_class = mcg.m_classes_name
                    LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
                    LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id
                    LEFT JOIN audit_logs al ON r.vehicle_id = al.vehicle_id AND r.project_id = al.project_id AND r.camera_ip = al.camera_ip
                    WHERE r.date_time >= :start_date 
                    AND r.date_time <= :end_date 
                    AND r.project_id = :project_id 
                    AND r.camera_ip = :camera_ip
                    AND r.ai_class = r.audited_class
                    GROUP BY r.ai_class, r.vehicle_name, r.vehicle_id, r.direction, 
                    r.image_path, r.last_modified, r.date_time, r.audited_class,r.detection_id, al.last_modified, al.updated_at
                                 
'''), {'start_date': from_date, 'end_date': to_date, 'project_id': project_id, 'camera_ip': camera_ip}).fetchall()
        

        print("11111111111111111111111111111111111111111111111$##%$6result:",result)
        
        if not result:
            raise HTTPException(status_code=404, detail="No records found.")

        audit_data = []
        for row in result:
            print("11111111111111111111111111111111111$#^$^&%^&%^8",row[6],row[5])
            analytics=row[4]
            
            formatted_date_time = row[6].astimezone().strftime("%b %d, %Y , %I:%M:%S %p")

            last_modified = row[8] if row[8] else "0"
            updated_at = row[9].astimezone().strftime("%B %d, %Y , %I:%M:%S %p") if row[9] else "N/A"



            print("$%&$^&*#*",last_modified,updated_at)
            detection_id=row[7]


            image_path = row[5] if row[5] else "/movable/No_Image_found.jpg"
            filename = os.path.basename(image_path) if image_path else "No_Image_found.jpg"

            detection_id_path_part = "/".join(image_path.split("/")[-4:])  
            print("$%#^$%:",detection_id_path_part)

            checking_local_image_path = os.path.join(image_path)
            
            if not os.path.exists(checking_local_image_path):
                image_path = "/movable/No_Image_found.jpg"
            else:
                image_path = f'/movable/ATCC/{project_id}/{camera_ip}/{detection_id_path_part}'
            
            if analytics and (analytics.startswith("South") or analytics.startswith("North")):
                    print("in else")
   
                    direction = os.path.basename(os.path.dirname(row[5])) 
                    filename = os.path.basename(row[5]) 
                    image_path = f"/movable/ATCC/{detection_id}/roi_cropped/{direction}/{filename}"
            print("image_path:",image_path)
           
            audit_data.append({
                "vehicle_id": row[0],  
                "last_modified": last_modified,  
                "updated_at": updated_at,  
                "direction": row[4],
                "vehicle_name": row[3],
                "audited_class": row[2],
                "image_path": image_path,
                "default_audited_class" :row[10]
            })

        print("Audit data:", audit_data)
        return JSONResponse(content={"data": audit_data})


    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please provide dates in YYYY-MM-DD format.")
   
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



@router.get('/main/report/fetch_audit')
async def filter_data_range(request: Request):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        with next(get_db()) as db:  # Ensure DB session closes properly

            kit1_data = db.execute(text('''
                SELECT r.id, r.date_time, r.vehicle_id, r.vehicle_name,
                       COALESCE(cc.custom_class, r.ai_class) AS ai_class, 
                       r.audited_class, r.direction, r.image_path, r.last_modified,r.detection_id,r.mapped_line,r.project_id,r.camera_ip
                FROM kit1_objectdetection r
                LEFT JOIN module_class_group mcg ON r.ai_class = mcg.m_classes_name
                LEFT JOIN mapping_custom_classes mcc ON mcg.m_classes_id = ANY(mcc.model_class_id)
                LEFT JOIN custom_classes cc ON mcc.custom_class_id = cc.id AND cc.id IS NOT NULL
                ORDER BY r.id DESC LIMIT 10
            ''')).fetchall()
            print("%%%%%%%%%$$$^%^&^&&$###$")
            print("$#%#$^ kit1 data:",kit1_data)
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

            if not kit1_data:
                return JSONResponse(content={"data": []})  # No data found case

            report_list = []
            for row in kit1_data:
                formatted_date_time = row[1].astimezone().strftime("%b %d, %Y , %I:%M:%S %p")
                analytics=row[6]
                image_path = row[7] if row[7] else "/movable/No_Image_found.jpg"
                filename = os.path.basename(image_path) if image_path else "No_Image_found.jpg"

                detection_id_path_part = "/".join(image_path.split("/")[-3:])  
                detection_id=row[9]
                project_id=row[11]
                camera_ip=row[12]
                print("project id and camera_ip:",project_id,camera_ip)
                print("$%#^$%:",detection_id_path_part)

                checking_local_image_path = os.path.join(image_path)
                
                if not os.path.exists(checking_local_image_path):
                    image_path = "/movable/No_Image_found.jpg"
                else:
                    image_path = f'/movable/ATCC/{project_id}/{camera_ip}/{detection_id}/{detection_id_path_part}'
                print("analytics :",analytics)
                if analytics and (analytics.startswith("South") or analytics.startswith("North")):
                    print("in else")
   
                    direction = os.path.basename(os.path.dirname(row[7])) 
                    filename = os.path.basename(row[7]) 
                    image_path = f"/movable/ATCC/{detection_id}/roi_cropped/{direction}/{filename}"
                print("image_path:",image_path)
                report_list.append({
                    "id": row[0],
                    "vehicle_id": row[2],
                    "vehicle_name": row[3],
                    "ai_class": row[4],
                    "audited_class": row[5],
                    "direction": row[6],
                    "image_path": image_path,
                    "date_time": formatted_date_time,
                    "last_modified": row[8],
                    "project_id":project_id,
                    "camera_ip":camera_ip
                })

                # print("report_list:",report_list)

        return JSONResponse(content={"data": report_list})

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

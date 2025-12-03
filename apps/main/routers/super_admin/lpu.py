from fastapi import  APIRouter, Query, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.jwt import * 
from apps.main.utils.session import * 

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")



@router.get('/main/lpu/', response_class=HTMLResponse, name="auth.lpu_management")
async def modules_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db())   
    modulee_id = 4
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    if role_id == 0:
        return templates.TemplateResponse("super_admin/lpu/add_lpu.html", 
                                        {'request': request,"session": session_data})
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/lpu/add_lpu.html", 
                                        {'request': request,"session": session_data})
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)


@router.get('/main/lpu/list/', response_class=HTMLResponse, name="auth.lpu_preview")
async def lpu_preview(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    role_id = session_data.get('role_id')
    db = next(get_db())   
    modulee_id = 4
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    if role_id == 0:

        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True

        return templates.TemplateResponse("super_admin/lpu/list_lpu.html", 
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


            return templates.TemplateResponse("super_admin/lpu/list_lpu.html",
                                        {'request': request,
                                            'page_permission':required_permission,
                                            'edit_permission' :edit_required_permission,
                                            'delete_permission' :delete_required_permission,
                                            "session": session_data})
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)



@router.get('/main/lpu/lpulist/')
async def lpulist(request:Request):
    db = next(get_db())

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    lpu_id=session_data['lpu_id']
    lpu=db.query(LpuGroup).filter(LpuGroup.lpu_id == lpu_id).all()

    lpu_list = [
        {
            "id": lpu.id,
            "lpu_id": lpu.lpu_id,
            "lpu_name": lpu.lpu_name,
            "lpu_ip": lpu.lpu_ip,
            "camera_ip": lpu.camera_ip,
            "camera_name": lpu.camera_name,
            "camera_username": lpu.camera_username,
        }
        for lpu in lpu
    ]
    
 
    return JSONResponse(content={"data": lpu_list})

@router.get("/main/lpu/status_check")
async def lpu_active(request:Request):
    session_data,error_response= handle_session(request)
    if error_response:
            return RedirectResponse(url="/")
    
    db=next(get_db())
    lpu_id=session_data['lpu_id']

    lpu_record = db.query(Lpu_management).filter(
                Lpu_management.lpu_id == lpu_id, 
                Lpu_management.lpu_status == False  
            ).all()

    print("lpu_records:",lpu_record)

    if lpu_record:
        return JSONResponse(
                status_code=400,
                content={"message": f"KIT is Offline.Cannot Add classes!."}
            )
    
    
    
def get_next_camera_id(db, lpu_id):
    max_camera = db.query(LpuGroup).filter(LpuGroup.lpu_id == lpu_id).order_by(LpuGroup.camera_id.desc()).first()
    return (max_camera.camera_id + 1) if max_camera and max_camera.camera_id else 1





@router.post('/main/lpu/add/')
async def users_add(request: Request):
    try:
        data = await request.json()

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        role_id = session_data.get('role_id')
        db = next(get_db())

        modulee_id = 4
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission", required_permission)

        lpu_id = data.get('lpu_id')
        lpu_name = data.get('lpu_name')
        lpu_ip = data.get('lpu_ip')
        
        camera_ip = data.get('camera_ip') 
        camera_name = data.get('camera_name')
        camera_port = data.get('camera_port')
        camera_username = data.get('camera_username')
        camera_password = data.get('camera_password')

        print("lpu_id:",lpu_id)

        lpu_record = db.query(Lpu_management).filter(
            Lpu_management.lpu_id == lpu_id, 
            Lpu_management.lpu_status == False  
        ).all()

        print("lpu_records:",lpu_record)

        if lpu_record:
            print("#######")

            return JSONResponse(
                status_code=400,
                content={"message": f" Kit is offline,cannot add camera! '{lpu_id}'."}
            )
        
        existing_camera = db.query(LpuGroup).filter(LpuGroup.camera_ip == camera_ip,LpuGroup.lpu_id == lpu_id).first()
        if existing_camera:
            return JSONResponse(
                status_code=400,
                content={"message": f"Camera IP '{camera_ip}' already exists, cannot add."}
            )

        camera_count = db.query(LpuGroup).filter(LpuGroup.lpu_id == lpu_id).count()
        if camera_count >= 2:
            return JSONResponse(
                status_code=400,
                content={"message": f" Only two cameras can be registered for LPU ID '{lpu_id}'."}
            )
        
        
        camera_ids = get_next_camera_id(db, lpu_id)


        add_new_lpu = LpuGroup(
            lpu_id=lpu_id,
            lpu_name=lpu_name, 
            lpu_ip=lpu_ip, 
            camera_ip=camera_ip, 
            camera_name=camera_name, 
            camera_port=camera_port, 
            camera_username=camera_username, 
            camera_password=camera_password,   
            updated_status=True,
            camera_id=camera_ids       
        )
        
        db.add(add_new_lpu)
        db.commit()
        db.refresh(add_new_lpu)

        return JSONResponse(content={"message": "LPU added successfully.", 
                                     "lpu": add_new_lpu.lpu_ip})
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




@router.delete('/main/lpu/delete/{lpu_id}')
async def delete_lpu(lpu_id: str):
    try:
        db = next(get_db())
        lpu = db.query(LpuGroup).filter(LpuGroup.lpu_id == lpu_id).first()
        if not lpu:
            raise HTTPException(status_code=404, detail="LPU ID not found")

        db.delete(lpu)
        db.commit()
        return {"detail": "LPU deleted successfully"}

    except Exception as e:
        print(f"Error deleting LPU: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    




@router.post('/main/lpu/update/{id}')
async def update_module(id: str, request: Request):
    print("*************************lpu*******")
    db  = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    lpu_id = session_data['lpu_id']
    form_data = await request.form()
    camera_ip = form_data.get('camera_ip')
    camera_name = form_data.get('camera_name')
    camera_port = form_data.get('camera_port')
    camera_username = form_data.get('camera_username')
    camera_password = form_data.get('camera_password')

    print("lpu:",camera_ip,camera_name,camera_port)

    


    module_to_update = db.query(LpuGroup).filter(LpuGroup.id == id).first()

    lpu_id=session_data['lpu_id']

    lpu_record = db.query(Lpu_management).filter(
            Lpu_management.lpu_id == lpu_id, 
            Lpu_management.lpu_status == False  
        ).all()

    print("lpu_records:",lpu_record)

    if lpu_record:
        raise HTTPException(status_code=400, detail=f"Kit is offline, cannot update LPU ID '{lpu_id}'.")


    
    if not module_to_update:
        raise HTTPException(status_code=404, detail=f"LPU ID {id} not found")
   
    module_to_update.camera_ip = camera_ip
    module_to_update.camera_name = camera_name
    module_to_update.camera_port = camera_port
    module_to_update.camera_username = camera_username
    module_to_update.camera_password = camera_password
    module_to_update.updated_status = True


    db.commit()
    db.refresh(module_to_update)

    return templates.TemplateResponse("super_admin/lpu/edit_lpu.html", {
        "request": request,
        "session": session_data,
        "lpu": module_to_update,
        "message": "Camera updated successfully."
    })


@router.get('/main/lpu/edit/{id}')
async def edit_lpu(id: str, request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())
    
    lpu = db.query(LpuGroup).filter(LpuGroup.id == id).first()

    
    if not lpu:
        raise HTTPException(status_code=404, detail=f"LPU ID {id} not found")

    return templates.TemplateResponse("super_admin/lpu/edit_lpu.html", {
        'request': request,
        "lpu": lpu,
        "session": session_data
    })



@router.get("/check_camera_ip")
def check_camera_ip(request:Request,camera_ip: str = Query(...),id: int = Query(None)):

    db=next(get_db())

    session_data, error_response = handle_session(request)
    if error_response:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    lpu_id = session_data['lpu_id']
    print("lpu_id",lpu_id,id)
    existing_ip = db.query(LpuGroup).filter(
        LpuGroup.camera_ip == camera_ip,
        LpuGroup.lpu_id == lpu_id  
    ).first() 
    
    if existing_ip:
        
        if existing_ip.id == id:
            return JSONResponse(status_code=200, content={"exists": False})
        return JSONResponse(status_code=200, content={"exists": True})

    return JSONResponse(status_code=200, content={"exists": False})
    
    

    





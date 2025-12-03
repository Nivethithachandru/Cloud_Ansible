from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from apps.main.models.model import SuperAdmin 
from apps.main.database.db import get_db ,initialize_database
from apps.main.utils.jwt import *
from apps.main.utils.session import *
from apps.main.config import *
from apps.main.utils.local_vendor import *


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")
 

# ------------

@router.on_event("startup")
async def startup_event():
    await initialize_database()   
    db = next(get_db())  

    if not db.query(SuperAdmin).filter_by(email="superadmin@gmail.com").first():
        super_admin = SuperAdmin(
            name="superadmin",
            email="superadmin@gmail.com", 
            password=get_hashed_password("superadmin123"),
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        print("Super Admin row data created.")
    else:
        print("Super Admin row data  already exists.")

permis_list_message = {}

@router.get("/main/map_permission/", response_class=HTMLResponse, name="main.map_permis")
async def mapping_permission(request: Request):
    global permis_list_message  

    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    roles = db.query(RoleGroup).outerjoin(Permissionlistmapping, RoleGroup.id == Permissionlistmapping.role_id).order_by(RoleGroup.id).all()

    permission_mapping = {pm.role_id: pm.is_permit for pm in db.query(Permissionlistmapping).all()}

    message = permis_list_message.get("message", None)
    if message:
        del permis_list_message["message"]

    return templates.TemplateResponse("mapp_permission.html", {
                "request": request,
                "roles": roles,
                "session": session_data, 
                "permission_mapping": permission_mapping,
                "message": message   
            })

@router.post("/main/mapping_permis/")
async def save_permissions(request: Request):
    global permis_list_message 
    
    form_data = await request.form()
    session_data, error_response = handle_session(request)

    if error_response:
        return RedirectResponse(url="/")

    db = next(get_db())

    all_roles = db.query(RoleGroup).all()
    role_ids = [role.id for role in all_roles]  
    
    for role_id in role_ids:
        is_permit = str(role_id) in form_data          
        permission_mapping = db.query(Permissionlistmapping).filter_by(role_id=role_id).first()
        if permission_mapping:
            permission_mapping.is_permit = is_permit
        else:
            new_permission = Permissionlistmapping(role_id=role_id, is_permit=is_permit)
            db.add(new_permission)

    db.commit()

    permis_list_message["message"] = "Permissions saved successfully."
    return RedirectResponse(url="/main/map_permission/", status_code=303)


    
@router.get("/main/kit/view/", response_class=HTMLResponse, name="main.lpu_view_monitor")
async def lpu_view_monitoring(request: Request):
    db = next(get_db())  
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    print("session_data",session_data)
    if error_response:
        return RedirectResponse(url="/")

    role_id = session_data.get('role_id')
    active_lpu_id=session_data['lpu_id']


    modulee_id = 6
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    get_all_camera_list = await get_all_camera_by_lpu(active_lpu_id)
    
    if role_id == 0:
        return templates.TemplateResponse("lpu_view_monitor.html", {
                "request": request,
                "session": session_data,
                "WEBSOCKET_CLOUD_URL":WEBSOCKET_CLOUD_URL,
                "cameras": get_all_camera_list  
            })
    else:
        if show_required_permission:
            return templates.TemplateResponse("lpu_view_monitor.html", {
                "request": request,
                "session": session_data,
                "WEBSOCKET_CLOUD_URL":WEBSOCKET_CLOUD_URL,
                "cameras": get_all_camera_list  
            })
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)




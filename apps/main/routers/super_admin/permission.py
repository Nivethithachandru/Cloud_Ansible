from fastapi import  APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import RoleGroup, ModulesGroup, RolePermissions
import json
from apps.main.utils.jwt import *
from apps.main.routers.roles.auth_role import *

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")


 
def get_role_modules_permissions(role_id: str):
    db = next(get_db())
    role = db.query(RoleGroup).filter(RoleGroup.id == role_id).first()
    modules = db.query(ModulesGroup).all()
    permissions = db.query(RolePermissions).filter(RolePermissions.role_id == role_id).all()
    permissions_dict = {perm.module_id: perm for perm in permissions}
    return role, modules, permissions_dict


@router.get('/main/roles/permission/{id}')
async def permission_role(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    role_id = session_data.get('role_id')



    permission_list_mapping = {
        pm.role_id: pm.is_permit 
        for pm in db.query(Permissionlistmapping).all() 
        if pm.is_permit
    }

    permitted_list_role_ids = [role_id for role_id, is_permit in permission_list_mapping.items() if is_permit]
    permitted_list_role_ids.append(0)   

  
    print("permitted_list_role_ids",permitted_list_role_ids)


    if role_id not in permitted_list_role_ids:
        print("Unauthorized user")
        error_page = templates.get_template("error_page.html")
        content = error_page.render({"request": request})
        return HTMLResponse(content=content, status_code=403)
    
    role, modules, permissions_dict = get_role_modules_permissions(id)

    role_valid = db.query(RoleGroup).filter(RoleGroup.id == id).first()
    
    if not role_valid:
        raise HTTPException(status_code=404, detail=f"Role with id {id} not found")


    alert_message = session_permission_alert_message.copy()
    session_permission_alert_message.clear()

    return templates.TemplateResponse("super_admin/roles/permission_role.html", {
        "request": request,
        "role": role,
        "modules": modules,
        "session": session_data,
        "alert_message": alert_message,
        "permissions_dict": permissions_dict  
    })




# ------------------------------------------------------
session_permission_alert_message = []


def update_or_create_permissions(permissions_data, db):
    for permission in permissions_data:
        existing_permission = db.query(RolePermissions).filter(
            RolePermissions.role_id == permission['role_id'],
            RolePermissions.module_id == permission['module_id']
        ).first()
       
        if existing_permission:
            existing_permission.show = permission['show']
            existing_permission.create = permission['create']
            existing_permission.read = permission['read']
            existing_permission.update = permission['update']
            existing_permission.delete = permission['delete']
        else:
            new_permission = RolePermissions(
                role_id=permission['role_id'],
                module_id=permission['module_id'],
                show=permission['show'],
                create=permission['create'],
                read=permission['read'],
                update=permission['update'],
                delete=permission['delete']
            )
            db.add(new_permission)


async def update_session_permissions(role_id: str, form_data: dict, modules: list):
    db = next(get_db())
    role, _, permissions_dict = get_role_modules_permissions(role_id) 
    
    for module in modules:
        existing_permission = permissions_dict.get(module.id)
        
        if existing_permission: 
            existing_permission.show = form_data.get(f"{module.module_name.lower().replace(' ', '_')}show") == "on"
            existing_permission.create = form_data.get(f"{module.module_name.lower().replace(' ', '_')}_create") == "on"
            existing_permission.read = form_data.get(f"{module.module_name.lower().replace(' ', '_')}_read") == "on"
            existing_permission.update = form_data.get(f"{module.module_name.lower().replace(' ', '_')}_update") == "on"
            existing_permission.delete = form_data.get(f"{module.module_name.lower().replace(' ', '_')}_delete") == "on"




@router.post('/main/roles/permission_modules/{id}')
async def role_module_permission(id: str, request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())
    role, modules, _ = get_role_modules_permissions(id)

    form_data = await request.form()
    permissions_data = []  

    for module in modules:
        permission_entry = {
            "role_id": id,  
            "module_id": module.id,  
            "show": form_data.get(f"{module.module_name.lower().replace(' ', '_')}_show") == "on",
            "create": form_data.get(f"{module.module_name.lower().replace(' ', '_')}_create") == "on",
            "read": form_data.get(f"{module.module_name.lower().replace(' ', '_')}_read") == "on",
            "update": form_data.get(f"{module.module_name.lower().replace(' ', '_')}_update") == "on",
            "delete": form_data.get(f"{module.module_name.lower().replace(' ', '_')}_delete") == "on"
        }
        permissions_data.append(permission_entry)  

    
    try:
        update_or_create_permissions(permissions_data, db)
        db.commit()  
        message = "Successfully permission updated"
        await update_session_permissions(id, form_data, modules)
    except Exception as e:
        db.rollback()
        print("error", e)
        raise HTTPException(status_code=500, detail="Error saving permissions to the database")
    
    session_permission_alert_message.append(message)
    return RedirectResponse(url=f"/main/roles/permission/{id}", status_code=303)

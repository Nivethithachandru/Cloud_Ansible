from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
from apps.main.config import *
from apps.main.models.model import *
from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse



from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")



from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def authorize(request: Request):
    # Manually render the template as an HTML response
    error_page = templates.get_template("error_page.html")
    content = error_page.render({"request": request})
    
    # Return the content as HTML with 403 status
    return HTMLResponse(content=content, status_code=403)



password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str):
    return password_context.hash(password)

def verify_password(password: str, hashed_pass: str):
    return password_context.verify(password, hashed_pass)

async def authorize(request: Request):    
    raise HTTPException(status_code=403, detail="Not authorized")




async def has_permission_bool(db, role_id: int, modulee_id: int, required_permission: str) -> bool:

    permission = db.query(RolePermissions).filter(
        RolePermissions.role_id == role_id,
        RolePermissions.module_id == modulee_id
    ).first()

    if not permission:
        return False

    if required_permission == "show":
        return permission.show
    elif required_permission == "create":
        return permission.create
    elif required_permission == "read":
        return permission.read
    elif required_permission == "update":
        return permission.update
    elif required_permission == "delete":
        return permission.delete
    else:
        return False




def get_role_info(db, role_id):
    role_data = db.query(RoleGroup).filter(RoleGroup.id == role_id).first()
    if not role_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role_permissions = db.query(RolePermissions).filter(RolePermissions.role_id == role_id).all()

    modules_data = []
    for permission in role_permissions:
        module = db.query(ModulesGroup).filter(ModulesGroup.id == permission.module_id).first()
        modules_data.append({
            "module_id": module.id,
            "module_name": module.module_name,
            "module_bio": module.module_bio,
            "permissions": {
                "show": permission.show,
                "create": permission.create,
                "read": permission.read,
                "update": permission.update,
                "delete": permission.delete
            }
        })

    role_info = {
        "role_name": role_data.role_name,
        "role_bio": role_data.role_bio,
        "role_id": role_data.role_id,
        "modules": modules_data
    }

    return role_info



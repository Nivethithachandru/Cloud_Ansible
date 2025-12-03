from fastapi import  APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.session import * 
import os
from apps.main.config import *
from logg import *
from typing import Any


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")



@router.get("/main/logs/get_logs/{action}")
async def get_logs_for_action(action: str, from_date: str, to_date: str):
    if action not in ["kit", "camera", "report", "audit","roles"]:
        raise HTTPException(status_code=404, detail="Action not found")

    logs = read_logs(action, from_date, to_date)
    
    if logs is None or logs.strip() == "":
        return {"message": f"No logs found for {action} between {from_date} and {to_date}."}

    return {"logs": logs}


@router.post('/main/logs/clear_logs/{action}')
async def clear_logs(action: str):
    LOGS_ROOT = os.path.join(media_base_path, 'LOGS/')

    log_file_path = os.path.join(LOGS_ROOT, f"{action}.log")
   
    if os.path.exists(log_file_path):
        with open(log_file_path, 'w') as file:             
            file.write("")   
        return {"message": f"{action.capitalize()} logs cleared successfully."}
    else:
        raise HTTPException(status_code=404, detail=f"No log file found for {action}.")


    
@router.get('/main/logs/list/', response_class=HTMLResponse, name="main.logs_preview")
async def logs_management(request: Request):
    db = next(get_db())  
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    role_id = session_data.get('role_id')
    
    modulee_id = 17
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    if role_id == 0:
        return templates.TemplateResponse("loggs.html", {
                "request": request,
                "session": session_data,

            })
    else:
        if show_required_permission:
            return templates.TemplateResponse("loggs.html", {
                "request": request,
                "session": session_data,

            })
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)





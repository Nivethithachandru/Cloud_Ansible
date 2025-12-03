from fastapi import FastAPI,APIRouter, HTTPException,Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse,StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, Alignment
from apps.main.utils.local_vendor import *
from apps.main.database.db import get_db
import zipfile
from io import BytesIO
import io,os,logging
import requests
from apps.main.config import *
from openpyxl.styles import Font, Alignment, Border, Side
from sqlalchemy import text
from apps.main.routers.super_admin.super_admin import has_permission_bool
from apps.main.utils.session import handle_session
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder

app = FastAPI()
router=APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="apps/main/front_end/templates")






@router.get("/main/detection", response_class=HTMLResponse, name="main.detection")
async def detection_management(request: Request):

    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')

    db = next(get_db()) 

    modulee_id = 8
    show_required_permission = "show" 

    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    now = datetime.now()   # or datetime.now() depending on your timezone handling
    three_minutes_ago = now - timedelta(minutes=1)

    print("current dateime",now)
    print("3 mintes ago ",three_minutes_ago)
    current_drawn = (
            db.query(ROIMapping)
            .filter(
                ROIMapping.datetime >= three_minutes_ago,
                ROIMapping.datetime <= now,
                ROIMapping.updated_status == True
            )
            .all()
    )
    print("resese ",current_drawn)

    
    if role_id == 0:
        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True
        return templates.TemplateResponse("super_admin/project/detection.html", {
                                        "request": request,
                                        "current_drawn" : jsonable_encoder(current_drawn),
                                        'page_permission':required_permission_s,
                                        'edit_permission' :edit_required_permission_s,
                                        'delete_permission' :delete_required_permission_s,                                        
                                        "session": session_data
                                        } )
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


            return templates.TemplateResponse("super_admin/project/detection.html", {
                                            'request': request,
                                            "current_drawn" : jsonable_encoder(current_drawn),
                                            'page_permission':required_permission,
                                            'edit_permission' :edit_required_permission,
                                            'delete_permission' :delete_required_permission,
                                            "session": session_data
                                            })
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)


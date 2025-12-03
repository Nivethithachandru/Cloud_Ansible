import json
from fastapi import APIRouter ,Request,HTTPException,Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi_utilities import repeat_every
import asyncio
from apps.main.utils.local_vendor import *
from apps.main.database.db import get_db


router=APIRouter()

templates = Jinja2Templates(directory="apps/main/front_end/templates")

@router.get("/cloud_sync")
async def cloud_to_kit_sendingdata(request: Request,db: Session = Depends(get_db)):
    try:
        print("hii")
        data = db.query(Lpu_management).all()
        return data
    except Exception as e:
        print("===================================================")
        print("===================================================")
        print("===================================================")

        print("Error Data Syncing to kit",e)

        print("===================================================")
        print("===================================================")
        print("===================================================")
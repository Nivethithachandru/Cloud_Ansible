import uuid
from datetime import datetime, timedelta
from apps.main.config import SESSION_EXPIRE_MINUTES
from apps.main.models.model import *
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from fastapi import Request
from apps.main.database.db import get_db
from apps.main.utils.jwt import *

session_store = {}

def create_session1(user_email, role_name, role_id, role_info, user_name=None, db_superadmin=False):
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Set the expiration time for the session
    expires_at = datetime.now() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    
    print("Session is creating... ", session_id)
    
    # Create the session data dictionary
    session_data = {
        'user_email': user_email,
        'role_name': role_name,
        'role_id': role_id,
        'expires_at': expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        'user_name': 'cosai' if db_superadmin else user_name,
        'permission': 'ALL' if db_superadmin else None,
        'role_info': role_info if not db_superadmin else None
    }

    # Store the session data in the global session_store
    session_store[session_id] = session_data
    # print("New session created: ", session_data)
    # print("Current session store: ", session_store)

    # Return the session ID and data
    return session_id, session_data


def create_session(user_email, role_name, role_id, role_info, user_name=None, db_superadmin=False):
    session_id = str(uuid.uuid4())
    dt = datetime.now() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    # print("SEssion is createing . .. . .",session_id)
    session_data = {
        'user_email': user_email,
        'role_name': role_name,
        'role_id': role_id,
        'expires_at': dt.strftime("%Y-%m-%d %H:%M:%S")
    }
    if db_superadmin:
        session_data['user_name'] = 'cosai'
        session_data['permission'] = 'ALL'
    else:
        session_data['user_name'] = user_name
        session_data['role_info'] = role_info

    session_store[session_id] = session_data
   
    response = JSONResponse(content={"message": "Login successful", "session_id": session_id})
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=SESSION_EXPIRE_MINUTES * 60)

    return response


def get_role_name_id(db, role_id):
    role = db.query(RoleGroup).filter(RoleGroup.role_id == role_id).first()
    return role.role_name if role else None
    

def update_session_recent(session_id, user_email, role_name, role_id, role_info, user_name=None, db_superadmin=False):
    
    if session_id in session_store:
        session_data = session_store[session_id]

        session_data['user_email'] = user_email
        session_data['role_name'] = role_name
        session_data['role_id'] = role_id
           
        if db_superadmin:
            session_data['user_name'] = 'cosai'
            session_data['permission'] = 'ALL'
        else:
            session_data['user_name'] = user_name
            session_data['role_info'] = role_info 
        # print("-------------------------------------------------------------")
        # print("-------------------------------------------------------------")
        # print("Session updated:", session_data)
        # print("-------------------------------------------------------------")
        # print("-------------------------------------------------------------")
    else:
        print("Session ID not found:", session_id)



def handle_session(request: Request, lpu_id: int = None, lpu_ip: str = None,lpu_name:str = None):
    db = next(get_db())


    session_id = request.cookies.get("session_id")
    if not session_id:
        return None, JSONResponse(content={"error": "No session found"}, status_code=401)

    session_data = session_store.get(session_id)
    if not session_data:
        return None, JSONResponse(content={"error": "Invalid or expired session"}, status_code=401)    

    role_id = session_data.get('role_id')
    user_name = session_data.get('user_name')
    user_email = session_data.get('user_email')

    if role_id == 0:
        sa_user_email = "superadmin@gmail.com"
        update_session_recent(session_id, sa_user_email, 'Super Admin', 0, 'ALL', db_superadmin=True)
    else:
        role_name = get_role_name_id(db, role_id)
        role_info = get_role_info(db, role_id)
        update_session_recent(session_id, user_email, role_name, role_id, role_info, user_name=user_name)

  
    if lpu_id is not None:
        session_data['lpu_id'] = lpu_id
        session_store[session_id] = session_data  

    if lpu_ip is not None:
        session_data['lpu_ip']=lpu_ip
        session_store[session_id]=session_data

    if lpu_name is not None:
        session_data['lpu_name']=lpu_name
        session_store[session_id]=session_data

    return session_data, None

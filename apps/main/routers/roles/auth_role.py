from fastapi import FastAPI, APIRouter, Query, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from apps.main.database.db import get_db
from apps.main.models.model import *
from apps.main.utils.jwt import *
from apps.main.utils.session import *
from apps.main.config import SESSION_EXPIRE_MINUTES


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")
 


session_login_store = {}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    error = session_login_store.get("error")
    success = session_login_store.get("success")
    
    session_login_store.pop("error", None)
    session_login_store.pop("success", None)

    return templates.TemplateResponse("roles/login.html", {
        "request": request,
        "error": error,
        "success": success
    })

#######################################################
@router.get("/auth/register_device/",response_class=HTMLResponse)
async def register_device(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("super_admin/org/register_device.html", {
        "request":request,
        "session": session_data,
        })
#######################################################
 


@router.post("/roles/auth/login/")
async def role_auth_login(request: Request):
    form_data = await request.form()
    user_email = form_data.get('email')
    user_password = form_data.get('password')
   

    db = next(get_db())
    superadmin = db.query(SuperAdmin).filter(SuperAdmin.email == user_email).first()


    existing_lpu = db.query(Lpu_management).first()
    if existing_lpu:
        redirect_url = f"/auth/dashboard?lpu_id={existing_lpu.lpu_id}&lpu_ip={existing_lpu.lpu_ip}&lpu_name={existing_lpu.lpu_name}"
    else:
        redirect_url = "/auth/organization_list"

        
    superadminrowdata = db.query(SuperAdmin).all() 
    db_superadmin_email = None
    for superadmin_data in superadminrowdata:
        db_superadmin_email = superadmin_data.email

    if user_email == db_superadmin_email:
        if superadmin and verify_password(user_password, superadmin.password):
            session_id, session_data = create_session1(user_email, 'Super Admin', 0, 'ALL', db_superadmin=True)
            print("Super admin session data:", session_data)

            org_data_exist = db.query(Lpu_management).first()
            if not org_data_exist:               
                response = RedirectResponse(url="/auth/register_device/", status_code=status.HTTP_303_SEE_OTHER)
                response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=SESSION_EXPIRE_MINUTES * 60)
                return response
            else:
                response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

                # response = RedirectResponse(url="/auth/organization_list/", status_code=status.HTTP_303_SEE_OTHER)
                response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=SESSION_EXPIRE_MINUTES * 60)
                return response

    roles_auth = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()
    if roles_auth and verify_password(user_password, roles_auth.user_password):
        role_info = get_role_info(db, roles_auth.role_id)  

        admin_get_block_or_nonblock = db.query(RoleGroup).filter(RoleGroup.role_id == 5).first() 
        get_block_or_nonblock = db.query(RoleGroup).filter(RoleGroup.role_id == roles_auth.role_id).first() 
 
        
        
        if admin_get_block_or_nonblock and admin_get_block_or_nonblock.is_blocked:
            session_login_store["error"] = "Admin role is blocked. No users can log in."
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            
        if get_block_or_nonblock and get_block_or_nonblock.is_blocked:  
            session_login_store["error"] = "User role is blocked."
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        
        session_id, session_data = create_session1(user_email, role_info['role_name'], roles_auth.role_id, role_info, user_name=roles_auth.user_name)
        
        # ✅ Redirect to first LPU dashboard if exists
        existing_lpu = db.query(Lpu_management).first()
        if existing_lpu:
            redirect_url = f"/auth/dashboard?lpu_id={existing_lpu.lpu_id}&lpu_ip={existing_lpu.lpu_ip}&lpu_name={existing_lpu.lpu_name}"
        else:
            redirect_url = "/auth/organization_list"

        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        # response = RedirectResponse(url="/auth/organization_list", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=SESSION_EXPIRE_MINUTES * 60)
        return response

    session_login_store["error"] = "User not found"
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)




@router.get("/auth/reset_pass/", name="auth.reset_pass")
async def update_password(request: Request):
    session_data, error_response = handle_session(request)
    print("session_data", session_data)

    if error_response:
        return RedirectResponse(url="/")

    user_email = session_data['user_email']
    db = next(get_db())

    if session_data['role_id'] == 0:  # Super Admin
        profile_data = db.query(SuperAdmin).filter(SuperAdmin.email == user_email).first()
    else:  
        profile_data = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()

    return templates.TemplateResponse("roles/update_profile.html", 
                                      {
                                          "request": request, 
                                          "session": session_data,
                                          "data": profile_data,
                                          "user_name": session_data['user_name'],  
                                          "user_email": user_email  
                                      })




@router.get("/auth/logout", name="auth.logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in session_store:
        del session_store[session_id]
    
    response = RedirectResponse(url="/")
    response.delete_cookie(key="session_id")  
    return response

@router.get("/main/device/list/", name="main.device_list")
async def device_list(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    print("session_data", session_data)

    user_email = session_data['user_email']
    db = next(get_db())
    role_id = session_data.get('role_id')

    modulee_id = 12
    show_required_permission = "show" 

    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)

    
    
    if role_id == 0:          
        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True
        profile_data = db.query(SuperAdmin).filter(SuperAdmin.email == user_email).first()
        return templates.TemplateResponse("super_admin/org/device_list.html", 
                                        {
                                            "request": request, 
                                            "session": session_data,
                                            "data": profile_data,
                                            'page_permission':required_permission_s,
                                            'edit_permission' :edit_required_permission_s,
                                            'delete_permission' :delete_required_permission_s,
                                            "user_name": session_data['user_name'],  
                                            "user_email": user_email  
                                        })
    else:
        profile_data = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()

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

            return templates.TemplateResponse("super_admin/org/device_list.html", 
                                        {
                                            "request": request, 
                                            "session": session_data,
                                            "data": profile_data,
                                            "user_name": session_data['user_name'], 
                                            'page_permission':required_permission,
                                            'edit_permission' :edit_required_permission,
                                            'delete_permission' :delete_required_permission, 
                                            "user_email": user_email  
                                        })

        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)
        



@router.get("/auth/organization_list",name='organization')
async def select_lpu(request:Request):
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    print("session_data", session_data)

    user_email = session_data['user_email']
    db = next(get_db())
    role_id = session_data.get('role_id')

    modulee_id = 12
    show_required_permission = "show" 

    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)

    
    
    if role_id == 0:          
        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True
        profile_data = db.query(SuperAdmin).filter(SuperAdmin.email == user_email).first()
        return templates.TemplateResponse("super_admin/org/org.html", 
                                        {
                                            "request": request, 
                                            "session": session_data,
                                            "data": profile_data,
                                            'page_permission':required_permission_s,
                                            'edit_permission' :edit_required_permission_s,
                                            'delete_permission' :delete_required_permission_s,
                                            "user_name": session_data['user_name'],  
                                            "user_email": user_email  
                                        })
    else:
        profile_data = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()

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

            return templates.TemplateResponse("super_admin/org/org.html", 
                                        {
                                            "request": request, 
                                            "session": session_data,
                                            "data": profile_data,
                                            "user_name": session_data['user_name'], 
                                            'page_permission':required_permission,
                                            'edit_permission' :edit_required_permission,
                                            'delete_permission' :delete_required_permission, 
                                            "user_email": user_email  
                                        })

        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)


@router.get('/main/add/organization/', response_class=HTMLResponse, name="main.organization")
async def classes_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")  
      
    role_id = session_data.get('role_id')
    db = next(get_db())   
    
    modulee_id = 5
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    if role_id == 0:
        return templates.TemplateResponse("super_admin/org/add_org.html", 
                                        {"request": request, "session": session_data}
                                        )
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/org/add_org.html", 
                                        {"request": request, "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)
        


@router.post('/main/device/add/')
async def add_device(request: Request):
    try:
        
        db=next(get_db())
        session_data, error_response = handle_session(request)
        
        data = await request.json()
        org_name = data.get('org_name')
        lpu_ip = data.get('lpu_ip')
        lpu_name = data.get('lpu_name')
        device_id=data.get('device_id')
        lpu_id=data.get('lpu_id')


        print("details:",org_name,lpu_ip,lpu_name,device_id,lpu_id)

    
        if not org_name or not lpu_ip or not lpu_name or not device_id or not lpu_id:
            return JSONResponse(
                status_code=400,
                content={"message": "All fields are required: org_name, lpu_ip, lpu_name,device id"}
            )

        
        existing_lpu_ip = db.query(Lpu_management).filter(Lpu_management.lpu_ip == lpu_ip).first()
        if existing_lpu_ip:
            return JSONResponse(
                status_code=400,
                content={"message": f"The LPU IP '{lpu_ip}' already exists. Please use a different IP."}
            )
        
        existing_lpu_id = db.query(Lpu_management).filter(Lpu_management.lpu_id == lpu_id).first()
        if existing_lpu_id:
            return JSONResponse(
                status_code=400,
                content={"message": f"The LPU IP '{lpu_id}' already exists. Please use a different ID."}
            )

    
        new_org = Lpu_management(
            org_name=org_name,
            lpu_ip=lpu_ip,
            lpu_name=lpu_name,
            updated_status=True,
            lpu_serial_num=device_id,
            lpu_id=lpu_id
        )
        db.add(new_org)
        db.commit()
        db.refresh(new_org)


        redirect_url = f"/auth/dashboard?lpu_id={new_org.lpu_id}&lpu_ip={new_org.lpu_ip}&lpu_name={new_org.lpu_name}"
        return JSONResponse(content={
            "message": f"Device '{new_org.org_name}' added successfully!",
            "redirect_url": redirect_url
        })
         

    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post('/main/org/add/')
async def add_organization(request: Request):
    try:
        db=next(get_db())
    
        session_data, error_response = handle_session(request)
        # if error_response:
        #     return JSONResponse(status_code=401, content={"message": "Unauthorized access"})

        role_id = session_data.get('role_id')
        module_id = 5  
        required_permission = "create"
        
     
        has_permission = await has_permission_bool(db, role_id, module_id, required_permission)
        if role_id != 0 and not has_permission:
            return JSONResponse(
                status_code=403,
                content={"message": "Access Denied: You are not authorized to perform this operation."}
            )

     
        data = await request.json()
        org_name = data.get('org_name')
        lpu_ip = data.get('lpu_ip')
        lpu_name = data.get('lpu_name')
        device_id=data.get('device_id')
        lpu_id=data.get('lpu_id')


        print("details:",org_name,lpu_ip,lpu_name,device_id,lpu_id)

    
        if not org_name or not lpu_ip or not lpu_name or not device_id or not lpu_id:
            return JSONResponse(
                status_code=400,
                content={"message": "All fields are required: org_name, lpu_ip, lpu_name,device id"}
            )

        
        existing_lpu_ip = db.query(Lpu_management).filter(Lpu_management.lpu_ip == lpu_ip).first()
        if existing_lpu_ip:
            return JSONResponse(
                status_code=400,
                content={"message": f"The LPU IP '{lpu_ip}' already exists. Please use a different IP."}
            )
        
        existing_lpu_id = db.query(Lpu_management).filter(Lpu_management.lpu_id == lpu_id).first()
        if existing_lpu_id:
            return JSONResponse(
                status_code=400,
                content={"message": f"The LPU IP '{lpu_id}' already exists. Please use a different ID."}
            )

    
        new_org = Lpu_management(
            org_name=org_name,
            lpu_ip=lpu_ip,
            lpu_name=lpu_name,
            updated_status=True,
            lpu_serial_num=device_id,
            lpu_id=lpu_id
        )
        db.add(new_org)
        db.commit()
        db.refresh(new_org)

        return JSONResponse(content={
            "message": "Organization added successfully.",
            "org_name": new_org.org_name
        })

    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/list/organization")
async def get_organizations():
    db=next(get_db())
    org_list = db.query(Lpu_management).all()
    data = [{"id": org.id, "org_name": org.org_name, "lpu_ip": org.lpu_ip, "lpu_name": org.lpu_name,"lpu_status":org.lpu_status,"lpu_id":org.lpu_id} for org in org_list]
    print("data in org :",data) 
    return JSONResponse(content={"data": data})


@router.get('/main/org/edit/{id}')
async def edit_lpu(id: str, request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())
    
    lpu = db.query(Lpu_management).filter(Lpu_management.id == id).first()
    if not lpu:
        raise HTTPException(status_code=404, detail=f"org's Lpu ID {id} not found")

    return templates.TemplateResponse("super_admin/org/edit_org.html", {
        'request': request,
        "lpu": lpu,
        "session": session_data
    })


@router.post('/main/org/update/{id}')
async def update_module(id: str, request: Request):
    print("*************************lpu*******")
    print("update lpu organization data .       . . . . . ")
    db  = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    form_data = await request.form()
    lpu_ip = form_data.get('lpu_ip')
    lpu_name = form_data.get('lpu_name')
    org_name = form_data.get('org_name')
    device_id = form_data.get('device_id')
    print("forooooooooooram",form_data)


    print("lpu:",lpu_ip,lpu_name,org_name,device_id)


    module_to_update = db.query(Lpu_management).filter(Lpu_management.id == id).first()

    
    if not module_to_update:
        raise HTTPException(status_code=404, detail=f"LPU ID {id} not found")
   
    module_to_update.lpu_ip = lpu_ip
    module_to_update.lpu_name = lpu_name
    module_to_update.org_name = org_name
    module_to_update.lpu_serial_num=device_id
    module_to_update.updated_status = True


    db.commit()
    db.refresh(module_to_update)

    return templates.TemplateResponse("super_admin/org/edit_org.html", {
        "request": request,
        "session": session_data,
        "lpu": module_to_update,
        "message": "Organization updated successfully."
    })



# @router.get("/api/check_lpu_ip")
# def check_lpu_ip(lpu_ip: str = Query(...), id: int = Query(None)):

#     db=next(get_db())
#     existing_lpu = db.query(Lpu_management).filter(Lpu_management.lpu_ip == lpu_ip).first()
#     if existing_lpu:
#         if existing_lpu.id == id:
#             return JSONResponse(status_code=200, content={"exists": False})
#         return JSONResponse(status_code=200, content={"exists": True})
    
@router.get("/api/check_lpu_ip")
def check_lpu_ip(lpu_ip: str = Query(...), id: int = Query(None)):
    db = next(get_db())
    existing_lpu = db.query(Lpu_management).filter(Lpu_management.lpu_ip == lpu_ip).first()

    if existing_lpu:
        if existing_lpu.id ==id:
            return JSONResponse(status_code=200, content={"exists": False})
        return JSONResponse(status_code=200, content={"exists": True})

    return JSONResponse(status_code=200, content={"exists": False})




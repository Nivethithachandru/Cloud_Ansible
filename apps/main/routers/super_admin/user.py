from fastapi import  APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import RoleGroup,UserGroup 
from apps.main.utils.jwt import * 
from apps.main.utils.session import *
from logg import *

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")

 
@router.get('/main/user/', response_class=HTMLResponse, name="main.users_management")
async def users_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    

    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db())   

    if role_id == 0 or role_id == 5:
        roles = db.query(RoleGroup).all()  
    else:
        roles = db.query(RoleGroup).filter(
            RoleGroup.id != role_id,
            RoleGroup.id != 5
        ).all()
     
    modulee_id = 2
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    
    if role_id == 0:
        return templates.TemplateResponse(
                "super_admin/user/add_user.html", 
                {'request': request, 'roles': roles,"session": session_data}  
            )
    else:
        if show_required_permission:
            return templates.TemplateResponse(
                "super_admin/user/add_user.html", 
                {'request': request, 'roles': roles,"session": session_data}  
            )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)

 
@router.get('/main/user/list/', response_class=HTMLResponse, name="main.user_preview")
async def user_preview(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db())   
    modulee_id = 2
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    if role_id == 0:
         

        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True

        return templates.TemplateResponse("super_admin/user/list_user.html", 
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


            return templates.TemplateResponse("super_admin/user/list_user.html",
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

@router.post('/main/user/add/')
async def users_add(request: Request):
    try:
        db = next(get_db())

        data = await request.json()
        print("data",data)
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        role_id = session_data.get('role_id')
        s_user_name = session_data.get('user_name')

        modulee_id = 2
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission",required_permission)

        role_select = data.get('role_select')
        user_name = data.get('user_name')
        user_id = data.get('user_id')
        user_email = data.get('user_email')
        user_password = data.get('user_password')
        db = next(get_db())

        if role_id != 0:
            if not required_permission:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Access Denied: You are not authorized to perform this operation."}
                )
        

        existing_user_email = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()
        if existing_user_email:
            return JSONResponse(
                status_code=400,
                content={"message": f"The user email '{user_email}' already exists. Please choose a different email."}
            )
        
        existing_user_id = db.query(UserGroup).filter(UserGroup.user_id == user_id).first()
        if existing_user_id:
            return JSONResponse(
                status_code=400,
                content={"message": f"The user ID '{user_id}' already exists."}
            )
        
        existing_user_name = db.query(UserGroup).filter(UserGroup.user_name == user_name).first()
        if existing_user_name:
            return JSONResponse(
                status_code=400,
                content={"message": f"The user Name '{user_name}' already exists. Please choose a different name."}
            )
        
        add_new_user = UserGroup(
            role_id=role_select,
            user_id=user_id, 
            user_name=user_name, 
            user_email=user_email, 
            user_password=get_hashed_password(user_password)  
        )
        
        
        ROLES_LOGGER.info(
            f"[USER] - New user '{user_name}' (Email: '{user_email}', Role ID: '{role_select}') created successfully by '{s_user_name}'"
        )
        
        db.add(add_new_user)
        db.commit()
        db.refresh(add_new_user)

        return JSONResponse(content={"message": "User added successfully.", 
                                    "user": add_new_user.user_email})
    
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



   
    



@router.post('/main/user/update/{id}')
async def update_user(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    s_user_name = session_data.get('user_name')


    form_data = await request.form()
    user_name = form_data.get('user_name')
    user_id = form_data.get('user_id')
    user_email = form_data.get('user_email')
    role_id = form_data.get('role_id')  


    user = db.query(UserGroup).filter(UserGroup.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {id} not found")

    ROLES_LOGGER.info(
        f"[USER] - User '{user.user_name}' ( Email: '{user.user_email}', Role ID: '{user.role_id}') "
        f"Updated to Name: '{user_name}', Email: '{user_email}', Role ID: '{role_id}' by '{s_user_name}'"
    )

    user.user_name = user_name
    user.user_id = user_id

    user.user_email = user_email
    user.role_id = role_id

    

    db.commit()   
    db.refresh(user) 
    message= "User updated successfully."

    return templates.TemplateResponse("super_admin/user/edit_user.html", {
        "request": request,
        "user": user,
        "session": session_data,
        "message": message
    })







@router.get('/main/user/userlist/')
async def preview_all_userlist():
    try:
        db = next(get_db())

        users = db.query(UserGroup).order_by(UserGroup.id).all()
        user_list = []

        for user in users:
            role = db.query(RoleGroup).filter(RoleGroup.id == user.role_id).first()

            user_info = {
                "serial_no": user.id,
                "user_id": user.user_id,
                "user_name": user.user_name,
                "role_name": role.role_name if role else "Unknown",
                "user_email": user.user_email
            }
            user_list.append(user_info)

        return {"data": user_list}

    except Exception as e:
        print(f"Error retrieving users: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.get('/main/user/edit/{id}')
async def user_role(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    user = db.query(UserGroup).filter(UserGroup.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {id} not found")

    role = db.query(RoleGroup).filter(RoleGroup.id == user.role_id).first()  
    role_name = role.role_name if role else "Unknown Role" 

    roles = db.query(RoleGroup).all()  

    return templates.TemplateResponse("super_admin/user/edit_user.html", 
                                      {'request': request, "user": user,
                                        "roles": roles, "role_name": role_name,
                                        "session": session_data})





@router.delete('/main/user/delete/{user_id}/')
async def delete_user(user_id: int,request: Request):
    try:
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        s_user_name = session_data.get('user_name')

        db = next(get_db())
        user = db.query(UserGroup).filter(UserGroup.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user)
        db.commit()
        ROLES_LOGGER.info(
                f"[USER] - User '{user.user_name}' deleted successfully by   {s_user_name}"
            )
        
        return {"detail": "User deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

 

@router.post('/main/user/update_password/')
async def update_user_password(request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)

    if error_response:
        return RedirectResponse(url="/")
    s_user_name = session_data.get('user_name')
    form_data = await request.json()
    user_email = form_data.get('user_email')
    new_password = form_data.get('new_password')
    
    
    try:
        superadmin = db.query(SuperAdmin).filter(SuperAdmin.email == user_email).first()
        user = db.query(UserGroup).filter(UserGroup.user_email == user_email).first()

        if superadmin:
            superadmin.password = get_hashed_password(new_password)
            db.commit()
            message = "Superadmin password updated successfully."
        elif user:
            ROLES_LOGGER.info(
                f"[USER] - Successfully updated password '{user.user_password}' to '{new_password}' by  '{s_user_name}'"
            )
            user.user_password = get_hashed_password(new_password)
            db.commit()
            message = "User password updated successfully."
        else:
            return {"message": "User not found. Please check the email and try again."}

        return {"message": message}

    except Exception as e:
        return {"message": "An error occurred while updating the password."}
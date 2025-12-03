from fastapi import  APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import RoleGroup
from apps.main.utils.jwt import *
from apps.main.routers.roles.auth_role import *
from logg import *

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")

 

@router.get('/main/roles/', response_class=HTMLResponse, name="main.roles_management")
async def roles_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")   
    
    role_id = session_data.get('role_id')
    
    db = next(get_db())  

    modulee_id = 1
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    if role_id == 0:
        return templates.TemplateResponse("super_admin/roles/add_role.html", 
                                        {"request": request, "session": session_data}
                                      )
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/roles/add_role.html", 
                                            {"request": request, "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)



@router.get('/main/roles/list/', response_class=HTMLResponse, name="main.roles_preview")
async def roles_preview(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db())   
    modulee_id = 1
    show_required_permission = "show" 
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    permission_list_mapping = {
        pm.role_id: pm.is_permit 
        for pm in db.query(Permissionlistmapping).all() 
        if pm.is_permit
    }

    permitted_list_role_ids = [role_id for role_id, is_permit in permission_list_mapping.items() if is_permit]
    permitted_list_role_ids.append(0)   

  

    if role_id == 0:

        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True

        return templates.TemplateResponse("super_admin/roles/list_role.html", 
                                        {"request": request,
                                          "role_id":role_id,

                                         "permitted_list_role_ids":permitted_list_role_ids, 
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


            return templates.TemplateResponse("super_admin/roles/list_role.html", 
                                        {"request": request, 
                                         "role_id":role_id,
                                          "permitted_list_role_ids":permitted_list_role_ids, 

                                        'page_permission':required_permission,
                                            'edit_permission' :edit_required_permission,
                                            'delete_permission' :delete_required_permission,                                        
                                        "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)




        
@router.delete('/main/roles/delete/{id}')
async def delete_role(id: str,request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    s_user_name = session_data.get('user_name')

    db = next(get_db())
    role_to_delete = db.query(RoleGroup).filter(RoleGroup.id == id).first()    
    if not role_to_delete:
        raise HTTPException(status_code=404, detail=f"Role {id} not found")    
    db.delete(role_to_delete)
    db.commit()
    ROLES_LOGGER.info(
                f"[ROLES] - Role '{role_to_delete.role_name}' deleted successfully by   {s_user_name}"
            )
    
    return JSONResponse(content={"message": f"Role {id} deleted successfully."})



@router.get('/main/roles/edit/{id}')
async def edit_role(id: str,request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    role = db.query(RoleGroup).filter(RoleGroup.id == id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role {id} not found")

    return templates.TemplateResponse("super_admin/roles/edit_role.html",
                                       {'request': request,"role":role,"session": session_data})


@router.post('/main/roles/update/{id}')
async def update_role(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    s_user_name = session_data.get('user_name')
    form_data = await request.form()
    updated_role_name = form_data.get('role_name')
    updated_role_bio = form_data.get('role_bio')

    role_to_update = db.query(RoleGroup).filter(RoleGroup.id == id).first()

    if not role_to_update:
        raise HTTPException(status_code=404, detail=f"Role {id} not found")

    
    ROLES_LOGGER.info(
        f"[ROLES] - Successfully updated role '{role_to_update.role_name}' to '{updated_role_name}' by  '{s_user_name}'"
    )
    role_to_update.role_name = updated_role_name
    role_to_update.role_bio = updated_role_bio
    db.commit()
    db.refresh(role_to_update)

    


    return templates.TemplateResponse("super_admin/roles/edit_role.html", {
        "request": request,
        "role": role_to_update,
        "session": session_data,
        "message": "Role updated successfully."
    })
   




@router.post('/main/roles/add/')
async def roles_add(request: Request):
    try:
        data = await request.json()
        db = next(get_db())

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        s_user_name = session_data.get('user_name')
        role_id = session_data.get('role_id')

        modulee_id = 1
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission",required_permission)


        role_name = data.get('role_name')
        role_bio = data.get('role_bio')
        
        if role_id != 0:
            if not required_permission:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Access Denied: You are not authorized to perform this operation."}
                )
        

        # Check if the role_name already exists
        existing_role_name = db.query(RoleGroup).filter(RoleGroup.role_name == role_name).first()
        if existing_role_name:
            return JSONResponse(
                status_code=400,
                content={"message": f"The role name '{role_name}' already exists. Please choose a different name."}
            )
        
        # Determine the next role_id based on existing records
        existing_roles_count = db.query(RoleGroup).count()
        role_id = existing_roles_count + 1  

        # Insert new role into the database
        add_new_role = RoleGroup(role_name=role_name, role_bio=role_bio, role_id=role_id)
        db.add(add_new_role)
        db.commit()
        db.refresh(add_new_role)
        ROLES_LOGGER.info(
                f"[ROLES] - Role '{role_name}' Created successfully by   {s_user_name}"
            )
        return JSONResponse(content={"message": "Role added successfully.", 
                                     "role": add_new_role.role_name})
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


@router.get('/main/roles/rolelist/')
async def preview_all_roleslist():
    db = next(get_db())
    roles = db.query(RoleGroup).order_by(RoleGroup.id).all()

    role_list = [
        {
            "serial_no": idx + 1,   
            "role_name": role.role_name,
            "role_bio": role.role_bio,
            "id":role.id,
            "is_blocked": role.is_blocked 
        }
        for idx, role in enumerate(roles)
    ]
 
    return JSONResponse(content={"data": role_list})

 

@router.post('/main/roles/block/{id}')
async def block_role(id: str,request: Request): 
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    s_user_name = session_data.get('user_name')
    
    db = next(get_db())
    role_to_block = db.query(RoleGroup).filter(RoleGroup.id == id).first()    
    if not role_to_block:
        raise HTTPException(status_code=404, detail=f"Role {id} not found")        
    role_to_block.is_blocked = True
    db.commit()  
    ROLES_LOGGER.info(
                f"[ROLES] - Role '{ role_to_block.role_name }' Blocked successfully by   {s_user_name}"
            )    
    return JSONResponse(content={"message": f"Role {id} blocked successfully."})



@router.post('/main/roles/unblock/{id}')
async def unblock_role(id: str,request: Request):  
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    s_user_name = session_data.get('user_name')
    db = next(get_db())
    role_to_unblock = db.query(RoleGroup).filter(RoleGroup.id == id).first()    
    if not role_to_unblock:
        raise HTTPException(status_code=404, detail=f"Role {id} not found")        
    role_to_unblock.is_blocked = False
    db.commit()  
    ROLES_LOGGER.info(
                f"[ROLES] - Role '{ role_to_unblock.role_name }' Un-Blocked successfully by   {s_user_name}"
            )
    return JSONResponse(content={"message": f"Role {id} unblocked successfully."})

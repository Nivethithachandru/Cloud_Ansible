from fastapi import  APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import ModulesGroup 
from apps.main.utils.jwt import * 
from apps.main.utils.session import * 
from sqlalchemy.exc import IntegrityError

router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")


@router.get('/main/modules/', response_class=HTMLResponse, name="main.modules_management")
async def modules_management(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    role_id = session_data.get('role_id')
    db = next(get_db()) 
    modulee_id = 3
    show_required_permission = "show"      
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    if role_id == 0:
        return templates.TemplateResponse("super_admin/modules/add_modules.html", 
                                        {'request': request,"session": session_data})
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/modules/add_modules.html", 
                                            {'request': request,"session": session_data})
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)

@router.get('/main/modules/list/', response_class=HTMLResponse, name="main.modules_preview")
async def modules_preview(request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())  
    role_id = session_data.get('role_id')
    modulee_id = 3
    show_required_permission = "show" 
     
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)

    if role_id == 0:
         

        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True

        return templates.TemplateResponse("super_admin/modules/list_module.html", 
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

            return templates.TemplateResponse("super_admin/modules/list_module.html", 
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


@router.get('/main/modules/moduleslist/')
async def preview_all_moduleslist():
    db = next(get_db())
    module = db.query(ModulesGroup).order_by(ModulesGroup.id).all()  

    module_list = [
        {
            "serial_no": idx + 1,   
            "module_name": module.module_name,
            "module_bio": module.module_bio,
            "id":module.id
        }
        for idx, module in enumerate(module)
    ]
 
    return JSONResponse(content={"data": module_list})

@router.delete('/main/modules/delete/{id}')
async def delete_module(id: str):
    db = next(get_db())
    modules_to_delete = db.query(ModulesGroup).filter(ModulesGroup.id == id).first()    
    if not modules_to_delete:
        raise HTTPException(status_code=404, detail=f"Modules {id} not found")    
    db.delete(modules_to_delete)
    db.commit()
    return JSONResponse(content={"message": f"Modules {id} deleted successfully."})


@router.get('/main/modules/edit/{id}')
async def edit_module(id: str,request: Request):
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    db = next(get_db())
    module = db.query(ModulesGroup).filter(ModulesGroup.id == id).first()
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {id} not found")

    return templates.TemplateResponse("super_admin/modules/edit_module.html",
                                       {'request': request,"module":module,"session": session_data})



@router.post('/main/modules/update/{id}')
async def update_module(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    form_data = await request.form()
    updated_module_name = form_data.get('module_name')
    updated_module_bio = form_data.get('module_bio')

    modules_to_update = db.query(ModulesGroup).filter(ModulesGroup.id == id).first()

    if not modules_to_update:
        raise HTTPException(status_code=404, detail=f"Module {id} not found")

    modules_to_update.module_name = updated_module_name
    modules_to_update.module_bio = updated_module_bio
 

    try:
        db.commit()
        db.refresh(modules_to_update)
        message = "Modules updated successfully."
    except IntegrityError:
        db.rollback() 
        message = "Module name already exists. Please choose a different name."


    return templates.TemplateResponse("super_admin/modules/edit_module.html", {
        "request": request,
        "session": session_data,
        "module": modules_to_update,
        "message": message
    })




@router.post('/main/modules/add/')
async def modules_add(request: Request):
    try:
        data = await request.json()
        module_name = data.get('module_name')
        module_bio = data.get('module_bio')
        db = next(get_db())

        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        
        role_id = session_data.get('role_id')

        modulee_id = 3
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission",required_permission)


        if role_id != 0:
            if not required_permission:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Access Denied: You are not authorized to perform this operation."}
                )
        
        
        
        existing_module_name = db.query(ModulesGroup).filter(ModulesGroup.module_name == module_name).first()
        if existing_module_name:
            return JSONResponse(status_code=400,
                                content={"message":f'The Module Name {module_name} already exists'})
    
        add_new_module = ModulesGroup(module_name=module_name, module_bio=module_bio)
        db.add(add_new_module)
        db.commit()
        db.refresh(add_new_module)
        return JSONResponse(content={"message": "Module added successfully.", 
                                     "module": add_new_module.module_name})
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


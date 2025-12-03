from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from main import CLASSES_ROOT
from apps.main.utils.jwt import *
from fastapi.templating import Jinja2Templates
from apps.main.routers.roles.auth_role import *
from aiocron import crontab


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")

@crontab('*/1 * * * *')
async def default_class_mapping():
    try:
        print("==== Running Default Class Mapping Cron ====")
        db = next(get_db()) 

        org_result = db.query(Lpu_management).all()
        print("LPU organization list:", org_result)
        
        for data in org_result:
            lpu_id = data.lpu_id
            print("Processing LPU ID:", lpu_id)

            if lpu_id:
                CUSTOM_DEFAULT_NAME = "NETC_CLASSES"

                # Check if the default custom class exists
                default_class = (
                    db.query(CustomClasses)
                    .filter(
                        CustomClasses.custom_class == CUSTOM_DEFAULT_NAME,
                        CustomClasses.lpu_id == lpu_id
                    )
                    .first()
                )

                if not default_class:
                    # Create it (SQLAlchemy will auto-assign id if serial)
                    default_class = CustomClasses(
                        custom_class=CUSTOM_DEFAULT_NAME,
                        updated_status=True,
                        lpu_id=lpu_id
                    )
                    db.add(default_class)
                    db.commit()
                    db.refresh(default_class)

                else:
                    # Already exists → just update updated_status
                    default_class.updated_status = True
                    db.commit()

                # Ensure the mapping exists with model_class_id=[0..15]
                default_mapping = (
                    db.query(MappingCustomClasses)
                    .filter(
                        MappingCustomClasses.custom_class_id == default_class.id,
                        MappingCustomClasses.lpu_id == lpu_id
                    )
                    .first()
                )

                if not default_mapping:
                    default_mapping = MappingCustomClasses(
                        custom_class_id=default_class.id,
                        model_class_id=list(range(16)),  # 0..15
                        updated_status=True,
                        lpu_id=lpu_id
                    )
                    db.add(default_mapping)
                    db.commit()
                else:
                    # Update existing mapping to ensure full default list
                    default_mapping.model_class_id = list(range(16))
                    default_mapping.updated_status = True
                    db.commit()

        print("==== Default Class Mapping Cron Completed ====")

    except Exception as e:
        print("Default Roi Mapping classes error:", e)


# @crontab('*/1 * * * *')
# async def default_class_mapping():
#     try:
#         print("==== Running Default Class Mapping Cron ====")
#         db = next(get_db()) 

#         org_result = db.query(Lpu_management).all()
#         print("LPU organization list:", org_result)
        
#         for data in org_result:
#             lpu_id = data.lpu_id
#             print("Processing LPU ID:", lpu_id)

#             if lpu_id:
#                 CUSTOM_DEFAULT_NAME = "NETC_CLASSES"

#                 existing_defcust_classes = (
#                     db.query(CustomClasses)
#                     .filter(
#                         CustomClasses.custom_class == CUSTOM_DEFAULT_NAME,
#                         CustomClasses.lpu_id == lpu_id
#                     )
#                     .first()
#                 )

#                 if not existing_defcust_classes:
#                     # Create custom class
#                     add_new_defcust_classes = CustomClasses(
#                         id=1,  # reserve this ID only for COSAI_CLASS
#                         custom_class=CUSTOM_DEFAULT_NAME,
#                         updated_status=True,
#                         lpu_id=lpu_id
#                     )
#                     db.add(add_new_defcust_classes)
#                     db.commit()
#                     db.refresh(add_new_defcust_classes)

#                     # Create default mapping
#                     new_mapping = MappingCustomClasses(
#                         custom_class_id=add_new_defcust_classes.id,
#                         model_class_id=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
#                         updated_status=True,
#                         lpu_id=lpu_id
#                     )
#                     db.add(new_mapping)
#                     db.commit()
#                 else:
#                     # ✅ Already exists → just update both
#                     existing_defcust_classes.updated_status = True
#                     db.commit()

#                     existing_mapping = (
#                         db.query(MappingCustomClasses)
#                         .filter(
#                             MappingCustomClasses.custom_class_id == existing_defcust_classes.id,
#                             MappingCustomClasses.lpu_id == lpu_id
#                         )
#                         .first()
#                     )
#                     if existing_mapping:
#                         existing_mapping.updated_status = True
#                         db.commit()
#         print("==== Default Class Mapping Cron Completed ====")

#     except Exception as e:
#         print("Default Roi Mapping classes error:", e)


@router.on_event('startup')
async def startup_event():
    db = next(get_db())    
    modules = [
        "Role management",
        "User Management",
        "Module management",
        "Camera Management",
        "Project management",
        "Live View",
        "Draw & ROI Mapping",
        "Detection Management",
        "Report management",
        "Audit Report",
        "Audit Transaction",
        "Device Management",
    ] 

    for name in modules:
        existing_module = db.query(ModulesGroup).filter_by(module_name=name).first()

        if not existing_module:
            new_module = ModulesGroup(
                module_name=name,
                module_bio=name.strip()  # bio same as name
            )
            db.add(new_module)
            db.commit()
            db.refresh(new_module)

    with open(CLASSES_ROOT, "r") as file:
        for index, value in enumerate(file):
            existing_record = db.query(ModuleClassesGroup).filter_by(m_classes_id=index).first()
            
            if not existing_record:                 
                module_class_name = ModuleClassesGroup(
                    m_classes_id=index,
                    m_classes_name=value.strip()
                )
                db.add(module_class_name)
                db.commit()
                db.refresh(module_class_name)                          

    db.close()

@router.get('/main/classes/', response_class=HTMLResponse, name="main.class_management")
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
        return templates.TemplateResponse("super_admin/classes/add_class.html", 
                                        {"request": request, "session": session_data}
                                        )
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/classes/add_class.html", 
                                        {"request": request, "session": session_data}
                                        )
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)
        


 
@router.get('/main/classes/classeslist/')
async def preview_all_classeslist(request:Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")


    lpu_id=session_data['lpu_id']

    print("lpu_id:",lpu_id)
    
   
    # custom_classes = db.query(CustomClasses).filter(CustomClasses.lpu_id == lpu_id).all()
    custom_classes = (
        db.query(CustomClasses)
        .filter(CustomClasses.lpu_id == lpu_id)
        .order_by(CustomClasses.id.asc())
        .all()
    )


    class_list = []    

    class_mappings=db.query(MappingCustomClasses).filter(MappingCustomClasses.lpu_id == lpu_id).all()
   

    module_classes = db.query(ModuleClassesGroup).order_by(ModuleClassesGroup.id).all()

    
    module_class_names = {}
    for module_class in module_classes:
        module_class_names[module_class.m_classes_id] = module_class.m_classes_name

    class_to_module_mapping = {}
    for mapping in class_mappings:
        module_names = []
        for module_id in mapping.model_class_id:
            module_name = module_class_names.get(module_id)
            if module_name:  
                module_names.append(module_name)
        class_to_module_mapping[mapping.custom_class_id] = module_names

    for index, custom_class in enumerate(custom_classes):
        module_groups = class_to_module_mapping.get(custom_class.id, [])

        class_list.append({
            'serial_no': index + 1,  
            'id': custom_class.id,  
            'custom_class': custom_class.custom_class,  
            'module_groups': module_groups 
        })

    return JSONResponse(content={"data": class_list})




@router.delete('/main/classes/delete/{id}')
async def delete_classes(id: str,request:Request):
    db = next(get_db())
    classes_to_delete = db.query(CustomClasses).filter(CustomClasses.id == id).first() 
    
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")


    lpu_id=session_data['lpu_id']

    print("lpu_id:",lpu_id)   
    if classes_to_delete:
        del_class =Ondelete(
                             custom_class=id,
                             status=True,
                             lpu_id=lpu_id
                               
                            )
    print("delete class:", del_class.__dict__)
    db.add(del_class)

    if not classes_to_delete:
        raise HTTPException(status_code=404, detail=f"Classes {id} not found")    
    db.delete(classes_to_delete)
    db.commit()
    return JSONResponse(content={"message": f"Classes {id} deleted successfully."})



@router.get('/main/classes/edit/{id}')
async def edit_classes(id: str,request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")
    
    lpu_id=session_data['lpu_id']

   
    classes = db.query(CustomClasses).filter(CustomClasses.id==id).first()

    if not classes:
        raise HTTPException(status_code=404, detail=f"Classes {id} not found")

    return templates.TemplateResponse("super_admin/classes/edit_class.html",
                                       {'request': request,"class":classes,"session": session_data})



@router.get('/main/classes/list/', response_class=HTMLResponse, name="main.classes_preview")
async def classes_preview(request: Request):
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
       
        required_permission_s = True
        edit_required_permission_s = True
        delete_required_permission_s = True

        return templates.TemplateResponse("super_admin/classes/list_classes.html", 
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


            return templates.TemplateResponse("super_admin/classes/list_classes.html",
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




@router.post('/main/classes/update/{id}')
async def update_classes(id: str, request: Request):
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
        return RedirectResponse(url="/")

    form_data = await request.form()
    updated_custom_class = form_data.get('custom_class')

    custom_class_to_update = db.query(CustomClasses).filter(CustomClasses.id == id).first()

    if not custom_class_to_update:
        raise HTTPException(status_code=404, detail=f"Classes {id} not found")
    


    existing_custom_class_name = db.query(CustomClasses).filter(CustomClasses.custom_class == updated_custom_class).first()
    if existing_custom_class_name:
        
        return templates.TemplateResponse("super_admin/classes/edit_class.html", {
            "request": request,
            "class": custom_class_to_update,
            "session": session_data,
            "message": f"The Classes name '{updated_custom_class}' already exists. Please choose a different name."
        })
    

    custom_class_to_update.custom_class = updated_custom_class
    custom_class_to_update.updated_status =True
    db.commit()
    db.refresh(custom_class_to_update)

    return templates.TemplateResponse("super_admin/classes/edit_class.html", {
        "request": request,
        "class": custom_class_to_update,
        "session": session_data,
        "message": "Classes updated successfully.",
        "redirect_url": "/main/view_report/"   
    })



@router.post('/main/classes/add/')
async def classes_add(request: Request):
    try:
        db = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")
        

        role_id = session_data.get('role_id')

        modulee_id = 5
        required_permission = "create" 
        
        required_permission = await has_permission_bool(db, role_id, modulee_id, required_permission)
        print("show_required_permission",required_permission)


        data = await request.json()
        custom_class_name = data.get('custom_class_name')
        lpu_id=session_data['lpu_id']

        lpu_record = db.query(Lpu_management).filter(
                Lpu_management.lpu_id == lpu_id, 
                Lpu_management.lpu_status == False  
            ).all()

        print("lpu_records:",lpu_record)

        # if lpu_record:
        #     return JSONResponse(
        #         status_code=400,
        #         content={"message": f"KIT is Offline.Cannot Add classes!."}
        #     )
        
        if role_id != 0:
            if not required_permission:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Access Denied: You are not authorized to perform this operation."}
                )
        
        

        existing_custom_class_name = db.query(CustomClasses).filter(CustomClasses.custom_class == custom_class_name,CustomClasses.lpu_id == lpu_id).first()
        if existing_custom_class_name:
            return JSONResponse(
                status_code=400,
                content={"message": f"The Classes name '{custom_class_name}' already exists. Please choose a different name."}
            )
        
        add_new_custom_classes= CustomClasses(custom_class=custom_class_name,updated_status=True,lpu_id=lpu_id)
        db.add(add_new_custom_classes)
        db.commit()
        db.refresh(add_new_custom_classes)
        return JSONResponse(content={"message": "Custom Classes Added successfully.", 
                                     "classes": add_new_custom_classes.custom_class})
    except HTTPException as http_error:
        pass
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



# ------------------------------------------------------------------------
async def get_custom_module_name(db,lpu_id):
    cust_data = db.query(CustomClasses).filter(CustomClasses.lpu_id==lpu_id).all()
    return cust_data

async def get_orginal_module_name(db):
    orgi_data = db.query(ModuleClassesGroup).order_by(ModuleClassesGroup.id).all()  
    return orgi_data

@router.get('/main/group/cust_classes/', response_class=HTMLResponse, name="main.group_class_management")
async def group_classes_management(request: Request):
    db = next(get_db())   

    session_data, error_response = handle_session(request)  
    if error_response:
        return RedirectResponse(url="/")   
    
    lpu_id=session_data['lpu_id']

    role_id = session_data.get('role_id')
    modulee_id = 7
    show_required_permission = "show" 
    show_required_permission = await has_permission_bool(db, role_id, modulee_id, show_required_permission)
    print("show_required_permission",show_required_permission)
    
    get_custom_class_name = await get_custom_module_name(db,lpu_id)
    get_orignial_class_name = await get_orginal_module_name(db)

    if role_id == 0:
        return templates.TemplateResponse("super_admin/classes/group_class.html", 
                                    {"request": request,
                                     "custom_class": get_custom_class_name,
                                     "original_class": get_orignial_class_name,
                                     "session": session_data
                                     })
    else:
        if show_required_permission:
            return templates.TemplateResponse("super_admin/classes/group_class.html", 
                                    {"request": request,
                                     "custom_class": get_custom_class_name,
                                     "original_class": get_orignial_class_name,
                                     "session": session_data
                                     })
        else:
            print("Unautorize user")
            error_page = templates.get_template("error_page.html")
            content = error_page.render({"request": request})
            
            return HTMLResponse(content=content, status_code=403)






# ---------------------------- group classs mapping --------------------------------------------------
@router.post('/main/group_classes/add_update/')
async def map_classes_update(request: Request):
    try:
        db = next(get_db())
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        data = await request.json()
        custom_class_id = data.get('custom_class_id')
        original_class_ids = data.get('orginal_class_id') 

        # if not custom_class_id or not original_class_ids:
        #     raise HTTPException(status_code=400, detail="Custom class ID and original class IDs are required.")
        lpu_id=session_data['lpu_id']

        lpu_record = db.query(Lpu_management).filter(
                Lpu_management.lpu_id == lpu_id, 
                Lpu_management.lpu_status == False  
            ).all()

        print("lpu_records:",lpu_record)

        # if lpu_record:
        #     return JSONResponse(
        #         status_code=400,
        #         content={"message": f"KIT is Offline.Cannot Add classes!."}
        #     )
        
        existing_mapping = db.query(MappingCustomClasses).filter(
            MappingCustomClasses.custom_class_id == custom_class_id
        ).first()

        if existing_mapping:
            print("Existing mapping:", existing_mapping.model_class_id)
            print("New mapping:", original_class_ids)

            # Convert both lists to int for proper comparison
            existing_ids_check = list(map(int, existing_mapping.model_class_id))
            new_ids_check = list(map(int, original_class_ids))

            print("Existing IDs check:", existing_ids_check)
            print("New IDs check:", new_ids_check)

            if existing_ids_check == new_ids_check:
                print("************************************************! Mapping already exists")
                return JSONResponse(
                    status_code=200,
                    content={"message": "Mapping already exists for this custom class."}
                )
            else:
                print("Updating mapping...")
                # Make sure to store as integers (or your DB type) consistently
                existing_mapping.model_class_id = new_ids_check
                existing_mapping.updated_status = True
        else:
            new_mapping = MappingCustomClasses(
                custom_class_id=custom_class_id,
                model_class_id=list(map(int, original_class_ids)),  # convert to int
                updated_status=True,
                lpu_id=lpu_id
            )
            db.add(new_mapping)

        db.commit()

        # existing_mapping = db.query(MappingCustomClasses).filter(MappingCustomClasses.custom_class_id == custom_class_id).first()

        # if existing_mapping:
        #     print("innnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
        #     print("88888888888888888888888888888",existing_mapping.model_class_id)
        #     print("newwwwwww",original_class_ids)

        #     existing_ids_check = list(map(int, existing_mapping.model_class_id))
        #     new_ids_check = list(map(int, original_class_ids))

        #     print(",,,,,,",existing_ids_check)
        #     print("33222332232",new_ids_check)
        #     if existing_ids_check == new_ids_check:

        #     # if existing_mapping.model_class_id == original_class_ids:
        #         # Value already exists
                
        #         print("************************************************!1111111111111111111111111111111111111111showww")
        #         return JSONResponse(
        #             status_code=200,
        #             content={"message": "Mapping already exists for this custom class."}
        #         )
        #     else:
        #         print("nooooooooooooooooooooooooooooooooooooo")
        #         existing_mapping.model_class_id = original_class_ids 
        #         existing_mapping.updated_status = True 
        # else:
        #     new_mapping = MappingCustomClasses(
        #         custom_class_id=custom_class_id,
        #         model_class_id=original_class_ids, 
        #         updated_status= True,
        #         lpu_id=lpu_id
        #     )
        #     db.add(new_mapping)

        # db.commit()  
   
        return {"message": "Mapping successfully updated.","classes": custom_class_id}


    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@router.post('/main/group_classes/fetch_ori_class/')
async def fetch_model_classes(request: Request):  
    data = await request.json()  
    custom_class_id = data.get('custom_id') 
    
    db = next(get_db())
    session_data, error_response = handle_session(request)
    if error_response:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    lpu_id=session_data['lpu_id']

    get_mapping = db.query(MappingCustomClasses).filter(MappingCustomClasses.custom_class_id == custom_class_id,MappingCustomClasses.lpu_id ==lpu_id).all()
    
    
    # get_all_mapping = db.query(MappingCustomClasses).filter(MappingCustomClasses.lpu_id ==lpu_id).all()
    get_all_mapping = db.query(MappingCustomClasses).filter(
        MappingCustomClasses.lpu_id == lpu_id,
        MappingCustomClasses.custom_class_id != 1
    ).all()

    total_classes = db.query(ModuleClassesGroup).all()

    total_classes_data = []
    for data in total_classes:
        total_classes_data.append({"m_classes_id": data.m_classes_id, "m_classes_name": data.m_classes_name}) 

    available_model_classes_id = []
    for selected_data in get_mapping:
        selected_model_ids = selected_data.model_class_id  
        for model_id in selected_model_ids: 
            available_model_classes_id.append(model_id)  

    already_booked_classes = set()  
    for data in get_all_mapping:
        for model_id in data.model_class_id:  
            already_booked_classes.add(model_id)  

    showing_dropdown_models = []
    
    for class_data in total_classes_data:
        class_id = class_data["m_classes_id"]
        class_name = class_data["m_classes_name"]
        
        if class_id not in already_booked_classes or class_id in available_model_classes_id:
            showing_dropdown_models.append({"m_classes_id": class_id, "m_classes_name": class_name})

    print("********************************************")
    print("Selected available_model_classes_id:", available_model_classes_id)
    print("********************************************")
    print("Total available_model_classes_data:", total_classes_data)
    print("********************************************")
    print("Showing dropdown models:", showing_dropdown_models)

    return {"message": "Fetch successfully", "data": showing_dropdown_models,'already_exisit_list' :available_model_classes_id}

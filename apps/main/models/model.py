from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float,JSON,func
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from apps.main.database.db import Base
from sqlalchemy.dialects.postgresql import ARRAY
from typing import Optional

class SuperAdmin(Base):
    __tablename__ = 'super_admin'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, default=0)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)     
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class RoleGroup(Base):
    __tablename__ = 'role_group'

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, index=True)
    role_bio = Column(String)
    role_id = Column(Integer, default=1)
    is_blocked = Column(Boolean, default=False)      
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship to RolePermissions
    permissions = relationship('RolePermissions', back_populates='role', cascade="all, delete")

class UserGroup(Base):
    __tablename__ = 'user_group'

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True)
    user_id = Column(String, unique=True, index=True)
    user_email = Column(String, unique=True, index=True)
    user_password = Column(String)  # Should not be unique
    role_id = Column(Integer, ForeignKey('role_group.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, unique=True, index=True,autoincrement=True)
    project_name = Column(String,index=True)
    camera_ip=Column(String)  
    camera_status=Column(Boolean)
    analytics=Column(String, index=True)
    lpu_id = Column(Integer, index=True) 
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_status=Column(Boolean, default=False)  
    cloud_status=Column(Boolean,default=False)
    mapped_value=Column(String)

    

class LpuGroup(Base):
    __tablename__ = 'lpu_group'

    id = Column(Integer, primary_key=True, index=True)
    lpu_id = Column(Integer, index=True) 
    lpu_name = Column(String, index=True)  
    lpu_ip = Column(String, index=True)
    camera_ip = Column(String) 
    camera_name = Column(String)
    camera_port = Column(String)
    camera_username = Column(String)
    camera_password = Column(String)
    camera_status = Column(Boolean, default=True)
    kit_status = Column(Boolean, default=False)  
    # project_id=Column(Integer) 
    updated_status = Column(Boolean,default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_status=Column(Boolean, default=False)
    lpu_status=Column(Boolean,default=False)
    camera_id = Column(Integer,autoincrement=True)

    

   
class KitMonitoring(Base):
    __tablename__ = 'kit_monitor'

    id = Column(Integer, primary_key=True, index=True)   
    lpu_id = Column(Integer, nullable=False) 

    total_disk_gb = Column(Float) 
    used_disk_gb = Column(Float)
    free_disk_gb = Column(Float)

    cpu_core = Column(Integer)  
    kit_fan_speed = Column(Integer)
    cpu_temperature = Column(Float)
    gpu_temperature = Column(Float)
    gpu_usage = Column(Float)  
    cpu_percentage_usage = Column(Float)
    ram_percentage_usage = Column(Float)
    
    system_uptime = Column(String) 
    total_ram_gb = Column(Float)
    used_ram_gb = Column(Float)

    kit_time = Column(DateTime, default=datetime.utcnow)  
    camera_status = Column(Boolean)
    storage_status = Column(Boolean, default=False)    
    temp_status = Column(Boolean, default=False)  

    download_speed = Column(Float)
    upload_speed = Column(Float) 
    camera_fps = Column(Float) 


    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   


class ModulesGroup(Base):
    __tablename__ = 'modules_group'

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String, unique=True, index=True)
    module_bio = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
     


class Permissionlistmapping(Base):
    __tablename__ = 'permissionlist_mapping'
    
    id = Column(Integer, primary_key=True, index=True)  
    role_id = Column(Integer, ForeignKey('role_group.id', ondelete='CASCADE'), nullable=False)  
    is_permit = Column(Boolean, default=False)  

class RolePermissions(Base):
    __tablename__ = 'role_permissions'

    id = Column(Integer, primary_key=True, index=True)  
    role_id = Column(Integer, ForeignKey('role_group.id', ondelete='CASCADE'), nullable=False)  
    module_id = Column(Integer, ForeignKey('modules_group.id', ondelete='CASCADE'), nullable=False)

    show = Column(Boolean, default=False)  
    create = Column(Boolean, default=False)  
    read = Column(Boolean, default=False)    
    update = Column(Boolean, default=False)  
    delete = Column(Boolean, default=False)  
    created_at = Column(DateTime, default=datetime.now)  
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    role = relationship('RoleGroup', back_populates='permissions')


class settings(Base):
    __tablename__ = 'alert_settings'

    id = Column(Integer, primary_key=True, index=True)
    lpu_id=Column(Integer)
    to_address = Column(ARRAY(String))   
    kit_alert = Column(Boolean, default=False)  
    camera_alert = Column(Boolean, default=False)  
    storage_alert = Column(Boolean, default=False)  
    temperature_alert = Column(Boolean, default=False)  
    last_mail_status=Column(String)
    created_at = Column(DateTime, default=datetime.now)  
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ModuleClassesGroup(Base):
    __tablename__ = 'module_class_group'

    id = Column(Integer, primary_key = True, index=True)
    m_classes_id = Column(Integer)
    m_classes_name = Column(String)
    created_at = Column(DateTime, default=datetime.now)  
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
   


class CustomClasses(Base):
    __tablename__ = 'custom_classes'

    id = Column(Integer, primary_key = True, index=True)
    custom_class = Column(String)
    created_at = Column(DateTime, default=datetime.now)  
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    mappings = relationship("MappingCustomClasses", backref="custom_class", cascade="all, delete-orphan")
    updated_status = Column(Boolean,default=False)
    lpu_id=Column(Integer)

 
class MappingCustomClasses(Base):
    __tablename__ = 'mapping_custom_classes'

    id = Column(Integer, primary_key=True, index=True)
    custom_class_id = Column(Integer, ForeignKey('custom_classes.id', ondelete='CASCADE')) 
    model_class_id = Column(ARRAY(Integer))   
    created_at = Column(DateTime, default=datetime.now)
    updated_status = Column(Boolean,default=False)
    lpu_id=Column(Integer)
   


class Detection_details(Base):
    __tablename__ = 'detection_details'

    id = Column(Integer, primary_key=True, index=True)        
    project_id = Column(Integer)
   
    camera_status = Column(Boolean, default=True)
    camera_ip = Column(String)
    line_crossing=Column(JSON,default={})
    updated_status = Column(Boolean,default=False)
    lpu_id=Column(Integer)
    
class Polygon_details(Base):
    __tablename__ = 'polygon_details'

    id = Column(Integer, primary_key=True, index=True)        
    project_id = Column(Integer)
    camera_ip = Column(String)
    coordinates=Column(JSON,default={})
    updated_status = Column(Boolean,default=False)
    lpu_id=Column(Integer)
    
   


# Column(DateTime, default=func.now())
class Detection_log(Base):
    __tablename__ = 'detection_log'

    id = Column(Integer, primary_key=True, index=True)        
    project_id = Column(Integer)
    camera_ip = Column(String)
    start_time=Column(DateTime)
    end_time=Column(DateTime)
    line_crossing=Column(JSON)
    line_id=Column(String)
    detection_id=Column(Integer)
    vms_status = Column(Boolean, default=False)
    vms_ffmpeg_processid = Column(String)
    pid = Column(String)
    detection_status=Column(String)
    created_at=Column(DateTime, default=datetime.now) 
    lpu_id=Column(Integer)
    mapped_polygon=Column(String)
    cloud_delete = Column(Boolean, default=False)




class VideosTsList(Base):
    __tablename__ = 'video_ts_data'
    id = Column(Integer, primary_key=True, index=True)        
    project_id = Column(Integer)
    camera_ip = Column(String)
    detection_id = Column(Integer)
    start_time = Column(DateTime)  # Use Column for defining type in SQLAlchemy
    file_name = Column(String)     # Same for file_name
    created_at = Column(DateTime, default=datetime.now)


class ROIMapping(Base):
    __tablename__ = 'roi_mapping'

    id = Column(Integer, primary_key=True, index=True)
    camera_ip = Column(String)
    lineid = Column(String)
    polygon=Column(String)
    project_id=Column(Integer,nullable=False)
    datetime =Column(DateTime,default=datetime.now)
    updated_status = Column(Boolean,default=False)

class Audit_activity(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index =True)
    obj_pid = Column(Integer)
    # kit_id=Column(Integer)
    vehicle_id=Column(Integer)
    m_classes_id=Column(Integer)
    last_modified=Column(String)
    project_id=Column(Integer)
    camera_ip=Column(String)
    actual_datetime = Column(DateTime,default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now) 



class kit1_objectdetection(Base):
    __tablename__ = 'kit1_objectdetection'

    id = Column(Integer, primary_key=True, index=True)
    date_time =Column(DateTime,default=datetime.now)
    vehicle_id=Column(Integer)
    vehicle_class_id= Column(Integer)
    vehicle_name=Column(String)
    ai_class=Column(String)
    audited_class=Column(String)
    direction =Column(String)
    cross_line=Column(Integer)
    x1_coords=Column(Float)
    y1_coords=Column(Float)
    x2_coords=Column(Float)
    y2_coords=Column(Float)
    frame_number=Column(Integer)
    image_path=Column(String)
    camera_ip=Column(String)
    play_stream_id =Column(Integer)
    detection_id=Column(Integer)
    is_audit=Column(Boolean, default=False)  
    kit_id=Column(Integer)
    project_id=Column(Integer)
    line_id=Column(String)
    last_modified=Column(String)
    mapped_line=Column(String)
    
  
    
class Vms_notification(Base):
    __tablename__ = "vms_notification"

    id =Column(Integer, primary_key = True, index =True)
    is_visit = Column(Boolean, default=False) 
    project_id=Column(Integer)
    camera_ip=Column(String)
    detection_id=Column(Integer)
    vms_directory = Column(String)
    vms_download_filename = Column(String)


class Lpu_management(Base):
    __tablename__ = "org_list"

    id=Column(Integer, primary_key = True, index =True)
    org_name=Column(String)
    lpu_ip=Column(String,unique=True)
    lpu_id=Column(Integer)
    lpu_name=Column(String)
    updated_status=Column(Boolean,default=False)
    lpu_serial_num=Column(String) 
    lpu_status=Column(Boolean,default=False)
    updated_at=Column(DateTime)
    
class cloud_vms(Base):
    __tablename__ = "cloud_vms"

    id =Column(Integer, primary_key = True, index =True)
    lpu_id = Column(Integer, index=True) 
    project_id=Column(Integer)
    camera_ip=Column(String)
    detection_id=Column(Integer)
    event_time =Column(DateTime,default=datetime.now)
    request_start_time=Column(DateTime)
    request_end_time=Column(DateTime)
    file_status_code = Column(Integer) # 0-> init 1->process 2->completed 3->failed
    upload_count = Column(Integer, default=0)    
    file_count = Column(Integer, default=0)
    row_status = Column(String)

class Ondelete(Base):
    __tablename__ = 'ondelete'
    id =Column(Integer,primary_key =True,index=True)
    project_id =Column(Integer)
    camera_ip=Column(String)
    detection_id=Column(Integer)
    custom_class=Column(Integer) 
    status=Column(Boolean,default=False)
    lpu_id=Column(Integer)


class Roi_detection(Base):
    __tablename__ = 'roi_detection'
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id=Column(Integer)
    date_time =Column(DateTime,default=datetime.now)
    vehicle_id=Column(Integer)
    vehicle_class_id= Column(Integer)
    vehicle_name=Column(String)
    ai_class=Column(String)
    direction =Column(String)
    image_path=Column(String)
    project_id=Column(Integer)
    camera_ip=Column(String)
    mapped_polygon=Column(String)

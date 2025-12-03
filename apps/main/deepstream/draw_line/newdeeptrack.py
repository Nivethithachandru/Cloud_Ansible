import argparse
import sys
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
import os
os.environ['CUDA_MODULE_LOADING'] = '1'
from gi.repository import GLib, Gst, GstRtspServer
from ctypes import *
from sqlalchemy.sql import text  
import time
import psutil
import math
import json
import threading
from apps.main.utils.session import * 
from aiocron import crontab
from pydantic import BaseModel
from apps.main.models.model import *
sys.path.append('../')
import asyncio
import multiprocessing
import platform
from apps.main.database.db import get_db
from pathlib import Path
from apps.main.config import deep_file,folder
from apps.main.database.db import get_db
from apps.main.deepstream.draw_line.deepstream_files.common.is_aarch_64 import is_aarch64
from apps.main.deepstream.draw_line.deepstream_files.common.bus_call import bus_call
from apps.main.deepstream.draw_line.deepstream_files.common.bbox import rect_params_to_coords
from apps.main.deepstream.draw_line.deepstream_files.common.FPS import PERF_DATA
from apps.main.deepstream.draw_line.box import callbbox
import numpy as np
import pyds
import cv2
import os.path
from os import path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SHOW_DRAW = False
detect_project_id=None

perf_data = None
frame_count = {}
saved_count = {}

MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 400000
TILED_OUTPUT_WIDTH = 1920  
TILED_OUTPUT_HEIGHT = 1080
GST_CAPS_FEATURES_NVMM = "memory:NVMM"
PGIE_CLASS_ID_auto_rickshaw = 0
PGIE_CLASS_ID_bus = 1
PGIE_CLASS_ID_car = 2
PGIE_CLASS_ID_other = 3
PGIE_CLASS_ID_lcv = 4
PGIE_CLASS_ID_mini_bus = 5
PGIE_CLASS_ID_Two_Wheeler = 6
PGIE_CLASS_ID_multi_axle = 7
PGIE_CLASS_ID_Truck_3Axle = 8
PGIE_CLASS_ID_Truck_4Axle = 9
PGIE_CLASS_ID_Truck_6Axle = 10
PGIE_CLASS_ID_tracktor = 11
PGIE_CLASS_ID_tracktor_trailer = 12
PGIE_CLASS_ID_Truck_2Axle = 13
PGIE_CLASS_ID_van = 14
PGIE_CLASS_ID_etcher = 15
pgie_classes_str= ["auto_rickshaw ", "Bus", "car","others","lcv", "minibus", "Two Wheeler","multiaxle", "Truck_3Axle", "Truck_4Axle","Truck_6Axle","Tractor","tracktor_trailer","Truck_2Axle","van","Foreign Truck"]
class_color=['0.0, 0.0, 0.0, 1.0',"0.0, 0.8, 1.0, 0.0",'0.0, 0.0, 1.0, 1.0',"0.0, 1.0, 0.0, 0.0","0.0, 1.0, 0.0, 1.0","0.0, 1.0, 1.0, 0.0","0.0, 1.0, 1.0, 1.0","1.0, 0.0, 0.0, 0.0","1.0, 0.0, 0.0, 1.0","1.0, 0.0, 1.0, 0.0","1.0, 0.0, 1.0, 1.0","1.0, 1.0, 0.0, 0.0","1.0, 1.0, 0.0, 1.0","1.0, 1.0, 1.0, 0.0","1.0, 1.0, 1.0, 1.0","1.0, 1.0, 1.0, 1.0"]

MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.4
obj_counter = {
PGIE_CLASS_ID_auto_rickshaw:0,
PGIE_CLASS_ID_bus:0,
PGIE_CLASS_ID_car:0,
PGIE_CLASS_ID_other:0,
PGIE_CLASS_ID_lcv:0,
PGIE_CLASS_ID_mini_bus:0,
PGIE_CLASS_ID_Two_Wheeler:0,
PGIE_CLASS_ID_multi_axle:0,
PGIE_CLASS_ID_Truck_3Axle:0,
PGIE_CLASS_ID_Truck_4Axle:0,
PGIE_CLASS_ID_Truck_6Axle:0,
PGIE_CLASS_ID_tracktor:0,
PGIE_CLASS_ID_tracktor_trailer:0,
PGIE_CLASS_ID_Truck_2Axle:0,
PGIE_CLASS_ID_van:0,
PGIE_CLASS_ID_etcher:0,
}
import psycopg2

pipeline = None
out_codec = "H265"
out_bitrate = 4000000

def draw_bbox(image, top, left, width, height, class_id, class_name):

    c1, c2 = int((top + width)/2), int((left + height)/2)
    cv2.putText(image, class_name, (c1, c2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)


active_processes = {}
project_info_queue = multiprocessing.Queue()




def update_pid_using_psycopg2(detection_id: str, pid: int):
    try:
        
        connection = psycopg2.connect(
            host="localhost",
            database="cloud_test4",

            user="postgres",
            password="ccsai"
        )

     
        cursor = connection.cursor()

        
        update_query = """
            UPDATE detection_log
            SET pid = %s
            WHERE detection_id = %s
        """

        
        cursor.execute(update_query, (pid, detection_id))

        
        connection.commit()

     
        if cursor.rowcount > 0:
            print(f"PID {pid} updated for detection_id {detection_id}")
        else:
            print(f"No record found with detection_id {detection_id}")

        
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error while updating PID using psycopg2: {e}")



def start_process_in_background(uri_inputs, project_id, camera_ip, detection_id, line, vms_directory):
    """
    Function to start the process in a separate background process.
    """
    try:
        
        print(f"Starting process for project_id: {project_id}")

       
        if project_id in active_processes:
            print(f"Process already running for project_id: {project_id}. Not starting a new one.")
            return active_processes[project_id].pid 
        
        print(f"No active process found for project_id: {project_id}. Starting a new one.")

        p = multiprocessing.Process(
            target=main,  
            args=(uri_inputs, out_codec, out_bitrate, folder, project_id, camera_ip, detection_id, line, vms_directory)
        )
        p.start()

        
        active_processes[project_id] = p
        update_pid_using_psycopg2(detection_id, p.pid)
      
        project_info_queue.put((project_id, p.pid))

        print(f"Process with ID {p.pid} is running for project_id {project_id}")
        return p.pid

    except Exception as e:
        print(f"Error while starting the process for project_id {project_id}: {e}")


async def deep_start(uri_inputs, project_id, camera_ip, line, line_crossing):
    """
    FastAPI endpoint to start the process in the background.
    """
    print("URI Inputs:", uri_inputs)
    uri_inputs = [uri_inputs]
    
    print(f"Camera IP: {camera_ip}, Project ID: {project_id}, Line ID: {line}")
    print("Line Crossing in start():", line_crossing)

    project_info_queue.put((project_id))
    
    db_session = next(get_db())
    detection_status = "Processing"

    last_record = db_session.query(Detection_log).order_by(Detection_log.id.desc()).first()
    detection_id = last_record.detection_id + 1 if last_record else 1  

    if isinstance(line_crossing, list):
        line_crossing = ";".join(line_crossing) + ";"

    new_project = Detection_log(
        project_id=project_id,
        camera_ip=camera_ip,
        start_time=datetime.now(),
        line_id=line,
        line_crossing=line_crossing,
        detection_id=detection_id,
        detection_status=detection_status,
        vms_status=True,
        vms_ffmpeg_processid=None
    )
    db_session.add(new_project)
    db_session.commit()

    

    vms_directory = Path(media_base_path) / "VMS" / f"proj_id_{project_id}" / f"camera_{camera_ip}" / f"detect_id_{detection_id}"
    os.makedirs(vms_directory, exist_ok=True)

   
    p = multiprocessing.Process(
        target=start_process_in_background,
        args=(uri_inputs, project_id, camera_ip, detection_id, line, vms_directory)
    )
    p.start()
    
    print(f"Started new process for project_id {project_id} with PID {p.pid}")




def tiler_sink_pad_buffer_probe(pad, info, u_data,project_id,camera_ip,detection_id,line):
    global SHOW_DRAW

    num_rects = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer")
        return
    
    print(f"Accessing project ID globally {project_id}{camera_ip}{line}")

    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_time = datetime.now()
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            frame_width = frame_meta.source_frame_width
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",frame_width)
        except StopIteration:
            break
        
   
        frame_number = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
       
        is_first_obj = True
        save_image = False
        frame_copy1 = np.array(n_frame, copy=True, order='C')
        # convert the array into cv2 default color format
        frame_copy1 = cv2.cvtColor(frame_copy1, cv2.COLOR_RGBA2BGRA)
        
       
        
        while l_obj is not None:
            try: 
                # Note that l_obj.data needs a cast to pyds.NvDsObjectMeta
                # The casting is done by pyds.NvDsObjectMeta.cast()
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            osd_rect_params =  pyds.NvOSD_RectParams.cast(obj_meta.rect_params)
            #To set the bbox color for each classes
            color_bbox = callbbox(obj_meta) 
            obj_meta = color_bbox 
            l_user_meta = obj_meta.obj_user_meta_list
            ###############################
            rect_params = obj_meta.rect_params
            top = int(rect_params.top)
            left = int(rect_params.left)
            width = int(rect_params.width)
            height = int(rect_params.height)
            obj_name = pgie_classes_str[obj_meta.class_id]

            if SHOW_DRAW:
                draw_bbox(frame_copy1, top, left, width, height, obj_meta.class_id, obj_name)
                cv2.imshow("detect", frame_copy1)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            ###############################
            while l_user_meta:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data)
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):             
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data)

                        if user_meta_data.dirStatus: print("1 {0} moving in direction: {1}".format(obj_meta.object_id, user_meta_data.dirStatus))                    
                        if user_meta_data.lcStatus: print("object id {0} line crossing: {1} classid: {2}".format(obj_meta.object_id, user_meta_data.lcStatus,obj_meta.class_id))
                        if user_meta_data.ocStatus: print("3 {0} overcrowding status: {1}".format(obj_meta.object_id, user_meta_data.ocStatus))
                        if user_meta_data.roiStatus: print("4 {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
                
                        if user_meta_data.lcStatus:
                        
                            obj_counter[obj_meta.class_id] += 1
                            
                            n_frame, obj_name = crop_object(n_frame, obj_meta)
                            # convert python array into numpy array format in the copy mode.
                            frame_copy = np.array(n_frame, copy=True, order='C')
                            # convert the array into cv2 default color format
                            frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)
                        save_image = True   
                        track_id = obj_meta.object_id

                        
      
                        
                        if save_image:   
                            direction = int(user_meta_data.lcStatus[0])
                            print("direction:", direction)
                            print("line :", line)

                        
                            line_list = line.split(",")

                            if "line_id_2" in line_list and direction == 0:
                                line_id = "line_id_2"
                                line_value = "line_2"
                            elif "line_id_1" in line_list and direction == 1:
                                line_id = "line_id_1"
                                line_value = "line_1"
                            elif "line_id_3" in line_list:
                                if direction == 0:
                                    line_id = "line_id_3_down"
                                elif direction == 1:
                                    line_id = "line_id_3_up"
                                line_value = "line_3"
                            else: 
                                line_id = None


                           
                           

                            print("Line ID:", line_id,line) 

                           
                            

                            folder_path = "{}/{}/{}/{}/{}/{}".format(folder_name, project_id, camera_ip,detection_id,line_value,line_id)
                            
                        
                            if not os.path.exists(folder_path):
                                os.makedirs(folder_path)

                        
                            img_path = "{}/{}_{}_{}.jpg".format(
                                folder_path,obj_name, user_meta_data.lcStatus[0], track_id
                            )

                            frame_copy = cv2.resize(frame_copy, (100, 100))
                            cv2.imwrite(img_path, frame_copy)


                            if folder_path not in saved_count:
                                saved_count[folder_path] = 0

                            

                        saved_count[folder_path] += 1


                        print("Project started:", project_id, camera_ip)
                        
                     

                        

                        print("Line ID:", line_id,line)

                      
                        end_time=datetime.now()

                        update_query = """
                                        UPDATE detection_log 
                                        SET end_time = %s 
                                        WHERE project_id = %s AND camera_ip = %s AND detection_id = %s
                                        """

                        update_values = (end_time, project_id, camera_ip, detection_id)
                       

                        
                        insert_query = """
                        INSERT INTO kit1_objectdetection (date_time, vehicle_id, vehicle_class_id, vehicle_name, direction, cross_line, 
                        x1_coords, y1_coords, x2_coords, y2_coords, frame_number, image_path,project_id,line_id,camera_ip,ai_class,detection_id,mapped_line)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s)
                        """

                        values = (
                            datetime.now(),
                            track_id,
                            obj_meta.class_id,
                            obj_name,
                            int(user_meta_data.lcStatus[0]),
                            1,  
                            left,
                            top,
                            left + width,
                            top + height,
                            frame_number,
                            img_path,
                            project_id,
                            line_id,
                            camera_ip,
                            obj_name,
                            detection_id,
                            line
                          
                        )
                        print("Values to be inserted:", values)

                        try:
                            connection = psycopg2.connect(
                                host="localhost",
                                database="cloud_test4",

                                user="postgres",
                                password="ccsai"
                            )
                            cursor = connection.cursor()
                            cursor.execute(update_query,update_values)

                            cursor.execute(insert_query, values)

                            connection.commit()

                            print(f"Successfully inserted object with ID: {track_id}")
                        except Exception as e:
                            print(f"Error inserting data: {e}")
                        finally:
                            if connection:
                                cursor.close()
                                connection.close()


                except StopIteration:
                    break
                try:
                    l_user_meta = l_user_meta.next
                except StopIteration:
                    break
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break

        
        l_user = frame_meta.frame_user_meta_list
        while l_user:
            try:
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSFRAME.USER_META"):
                    user_meta_data = pyds.NvDsAnalyticsFrameMeta.cast(user_meta.user_meta_data)
                 
            except StopIteration:
                break
            try:
                l_user = l_user.next
            except StopIteration:
                break

       
        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
    
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]

        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.
        py_nvosd_text_params.display_text = "bus={} car={} Others={} Lcv={} Minibus={} Two={} M_Axle={} 2_Axle={} 3_Axle={} 4_Axle={} 6_Axle={} Etcher={}Total={}".format(obj_counter[PGIE_CLASS_ID_bus], obj_counter[PGIE_CLASS_ID_car], obj_counter[PGIE_CLASS_ID_other], obj_counter[PGIE_CLASS_ID_lcv],obj_counter[PGIE_CLASS_ID_mini_bus], obj_counter[PGIE_CLASS_ID_Two_Wheeler], obj_counter[PGIE_CLASS_ID_multi_axle], obj_counter[PGIE_CLASS_ID_Truck_2Axle],obj_counter[PGIE_CLASS_ID_Truck_3Axle],obj_counter[PGIE_CLASS_ID_Truck_4Axle],obj_counter[PGIE_CLASS_ID_Truck_6Axle],obj_counter[PGIE_CLASS_ID_etcher],user_meta_data.objLCCumCnt)
        
        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 35

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 12
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 2
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)


        # Update frame rate through this probe
        stream_index = "stream{0}".format(frame_meta.pad_index)
        global perf_data
        perf_data.update_fps(stream_index)

        try:
            l_frame=l_frame.next
        except StopIteration:
            break

    # store_file_object.create_excel_sheet()

    return Gst.PadProbeReturn.OK



def crop_object(image, obj_meta):
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)
    obj_name = pgie_classes_str[obj_meta.class_id]
    print("obj_name",obj_name)

    crop_img = image[top:top+height, left:left+width]
	
    return crop_img,obj_name



def cb_newpad(decodebin, decoder_src_pad, data):
    print("In cb_newpad\n")
    caps = decoder_src_pad.get_current_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if (gstname.find("video") != -1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")


def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)
    if is_aarch64() and name.find("nvv4l2decoder") != -1:
       print("Seting bufapi_version\n")
       Object.set_property("bufapi-version", True)


def create_source_bin(index, uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name = "source-bin-%02d" % index
    print(bin_name)
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")


    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri", uri)
   
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin



from apps.main.config import *
from pathlib import Path
import subprocess




async def start_ffmpeg_stream(uri_inputs,vms_directory,project_id,camera_ip,detection_id):
    try:
        connection = psycopg2.connect( host="localhost", database="cloud_test4", user="postgres", password="ccsai")

        cursor = connection.cursor()
        print("[VMS] Video storing started . . . . . ")
        print("[VMS] VMS VIDEO STORE DIRECTORY",vms_directory)
        print("[VMS] VMS VIDEO STORE RTSP URL",uri_inputs)
        HLS_TIME_DURATION = 10
        HLS_SEGMENT_FILENAME = "%Y-%m-%d-%H-%M-%S.ts"

        command = [
            "ffmpeg", "-hide_banner", "-i", uri_inputs[0],
            "-c:v", "copy",
            "-f", "hls", "-hls_time", str(HLS_TIME_DURATION), "-hls_list_size", "10",
            "-hls_segment_filename", f"{vms_directory}/{HLS_SEGMENT_FILENAME}",
            "-strftime", "1",
            "-loglevel", "error",
            f"{vms_directory}/index.m3u8"
        ]        
        proc = await asyncio.create_subprocess_exec(
            *command,  
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        time.sleep(2)
        p = subprocess.Popen(['pgrep', 'ffmpeg'], stdout=subprocess.PIPE)
        pids = p.communicate()[0].decode('utf-8').split('\n') 
        ffmpeg_processid = pids[-2].strip() if len(pids) >= 2 else None   
        print("[VMS] VMS FFMPEG PROCESS ID",ffmpeg_processid)
      
        if ffmpeg_processid:   
            query = """
                UPDATE detection_log
                SET vms_ffmpeg_processid = %s
                WHERE project_id = %s AND camera_ip = %s AND detection_id = %s
            """
            cursor.execute(query, (ffmpeg_processid, project_id, camera_ip,detection_id))
            connection.commit()
             
    except Exception as e:
        print("[VMS] Errror ffmpeg",e)



def main(uri_inputs,codec,bitrate,folder,project_id,camera_ip,detection_id,line,vms_directory):

    #####################################  VMS IMPLEMENTATION  ######################################
    #####################################  VMS IMPLEMENTATION  ######################################
   
   

    asyncio.run(start_ffmpeg_stream(uri_inputs,vms_directory,project_id,camera_ip,detection_id))
    # asyncio.run(check_process_status())

    #####################################  VMS IMPLEMENTATION  ######################################
    #####################################  VMS IMPLEMENTATION  ######################################


    # Check input arguments
    number_sources = len(uri_inputs)
    global perf_data
    perf_data = PERF_DATA(number_sources)
    print("project id in main:",project_id)
    
    global folder_name
    folder_name = folder
    

    Gst.init(None)

    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
    print("Creating streamux \n ")

  
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    pipeline.add(streammux)
    line = line.strip("{}") 
    print("line id:",line)
    folder_path = "{}/{}/{}/{}".format(folder_name, project_id, camera_ip,detection_id)
    print("folder path:", folder_path)

    for i in range(number_sources):
        if not os.path.exists(folder_path):  
            os.makedirs(folder_path) 
        frame_count[folder_path] = 0
        saved_count[folder_path] = 0
        print("Creating source_bin ", i, " \n ")
        uri_name = uri_inputs[i]

        if uri_name.find("rtsp://") == 0:
            is_live = True
        source_bin = create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname = "sink_%u" % i
        sinkpad = streammux.get_request_pad(padname)
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)
    print("Creating Pgie \n ")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")
    
    print("Creating nvvidconv1 \n ")
    nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
    if not nvvidconv1:
        sys.stderr.write(" Unable to create nvvidconv1 \n")
    print("Creating filter1 \n ")
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
    if not filter1:
        sys.stderr.write(" Unable to get the caps filter1 \n")
    filter1.set_property("caps", caps1)

    print("Creating nvtracker \n ")
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")


    print("Creating nvdsanalytics \n ")
    nvanalytics = Gst.ElementFactory.make("nvdsanalytics", "analytics")
    deep_config_file = Path(deep_file) 
    nvdconf = str( deep_config_file/ "deeptrackconfig.txt")
    if not nvanalytics:
        sys.stderr.write(" Unable to create nvanalytics \n")
    nvanalytics.set_property("config-file",nvdconf)
 

    print("Creating tiler \n ")
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")
    print("Creating nvvidconv \n ")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
    print("Creating nvosd \n ")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

   


    nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    if not nvvidconv_postosd:
        sys.stderr.write(" Unable to create nvvidconv_postosd \n")
    
    # Create a caps filter
    caps = Gst.ElementFactory.make("capsfilter", "filter")
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))
    

    
    # Make the encoder
    if codec == "H264":
        encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
        print("Creating H264 Encoder")
    elif codec == "H265":
        encoder = Gst.ElementFactory.make("nvv4l2h265enc", "encoder")
        print("Creating H265 Encoder")
    if not encoder:
        sys.stderr.write(" Unable to create encoder")
    encoder.set_property('bitrate', bitrate)
    if is_aarch64():
        encoder.set_property('preset-level', 1)
        encoder.set_property('insert-sps-pps', 1)
     


    
    # Make the payload-encode video into RTP packets
    if codec == "H264":
        rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
        print("Creating H264 rtppay")
    elif codec == "H265":
        rtppay = Gst.ElementFactory.make("rtph265pay", "rtppay")
        print("Creating H265 rtppay")
    if not rtppay:
        sys.stderr.write(" Unable to create rtppay")
    
    # Make the UDP sink
    updsink_port_num = 5400
    sink = Gst.ElementFactory.make("udpsink", "udpsink")
    if not sink:
        sys.stderr.write(" Unable to create udpsink")
    
    sink.set_property('host', '224.224.255.255')
    sink.set_property('port', updsink_port_num)
    sink.set_property('async', True)
    sink.set_property('sync', 1)


    muxer = Gst.ElementFactory.make("mp4mux", "muxer")
    if not muxer:
        sys.stderr.write(" Unable to create MP4 muxer\n")

    print("Creating Sink \n")
    filesink = Gst.ElementFactory.make("filesink", "filesink")
    if not filesink:
        sys.stderr.write(" Unable to create file sink \n")

    filesink.set_property("location", "./fp32_detect_output.mp4")
    filesink.set_property("sync", 0)
    filesink.set_property("async", 1)

    
    print("Playing file {} ".format(uri_inputs))
   

    tee = Gst.ElementFactory.make("tee", "tee")
    if not tee:
        sys.stderr.write(" Unable to create tee\n")

    queue1 = Gst.ElementFactory.make("queue", "queue1")
    queue2 = Gst.ElementFactory.make("queue", "queue2")
    if not queue1 or not queue2:
        sys.stderr.write(" Unable to create queues\n")

    # source_bin.set_property('location','out.mp4')
    streammux.set_property('width', MUXER_OUTPUT_WIDTH)
    streammux.set_property('height', MUXER_OUTPUT_HEIGHT)
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', 4000000)
    nvdinfer = str(deep_config_file / "config_infer_primary_yoloV11.txt")
    print(nvdinfer)
    pgie.set_property('config-file-path',nvdinfer)
    pgie_batch_size = pgie.get_property("batch-size")
    # pgie_batch_size = 2
    if (pgie_batch_size != number_sources):
        print("WARNING: Overriding infer-config batch-size", pgie_batch_size, " with number of sources ",
              number_sources, " \n")
        pgie.set_property("batch-size", number_sources)
    tiler_rows = int(math.sqrt(number_sources))
    tiler_columns = int(math.ceil((1.0 * number_sources) / tiler_rows))
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)

 #Set properties of tracker

    config = configparser.ConfigParser()
    nvdtravk = str(deep_config_file/ 'dsnvanalytics_tracker_config.txt')
   
    config.read(nvdtravk)
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
     
    if not is_aarch64():
       
        mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        streammux.set_property("nvbuf-memory-type", mem_type)
        nvvidconv.set_property("nvbuf-memory-type", mem_type)
        nvvidconv1.set_property("nvbuf-memory-type", mem_type)
        tiler.set_property("nvbuf-memory-type", mem_type)

    print("Adding elements to Pipeline \n")
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvanalytics)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(filter1)
    pipeline.add(nvvidconv1)
    pipeline.add(nvosd)
    pipeline.add(nvvidconv_postosd)
    pipeline.add(caps)
    pipeline.add(encoder)
    pipeline.add(rtppay)
    pipeline.add(tee)
    pipeline.add(queue1)
    pipeline.add(queue2)
    pipeline.add(sink)
    pipeline.add(muxer)
    pipeline.add(filesink)
    

    print("Linking elements in the Pipeline \n")
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvanalytics)
    nvanalytics.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tiler)
    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(nvvidconv_postosd)
    nvvidconv_postosd.link(caps)
    caps.link(encoder)

    encoder.link(tee)

    tee.link(queue1)
    tee.link(queue2)

    queue1.link(rtppay)
    rtppay.link(sink)
    queue2.link(filesink)
   
    

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)
    
    # Start streaming
    rtsp_port_num = 8555
    
    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    rtsp_url = f"rtsp://localhost:{rtsp_port_num}/deep"
    server.attach(None)
    
    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_launch( "( udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (updsink_port_num, codec))
    factory.set_shared(True)
    server.get_mount_points().add_factory("/deep", factory)
    
    print("\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n" % rtsp_port_num)
    
    tiler_sink_pad = tiler.get_static_pad("src")
    if not tiler_sink_pad:
        sys.stderr.write(" Unable to get sink pad \n")
    else:
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0,project_id,camera_ip,detection_id,line)
        # perf callback function to print fps every 5 sec
        GLib.timeout_add(5000, perf_data.perf_print_callback)

    # ffmpeg_thread_obj = threading.Thread(target=ffmpeg_thread, args=(rtsp_url,))
    # ffmpeg_thread_obj.start()
    print("Starting pipeline \n")
    # start play back and listed to events		
    pipeline.set_state(Gst.State.PLAYING)
    # data = videorender(folder_name)

    try:
        loop.run() 
    except:
        pass
    
    print("Exiting app\n")
  

    pipeline.set_state(Gst.State.NULL)

def parse_args():
    parser = argparse.ArgumentParser(description='RTSP Output Sample Application Help ')
				  
    parser.add_argument("-i","--uri_inputs", metavar='N', type=str, nargs='+',
                    help='Path to inputs URI e.g. rtsp:// ...  or file:// seperated by space')
					
    parser.add_argument("-c", "--codec", default="H264",
                  help="RTSP Streaming Codec H264/H265 , default=H264", choices=['H264','H265'])
    parser.add_argument("-b", "--bitrate", default=4000000,
                  help="Set the encoding bitrate ", type=int)
    parser.add_argument("-f", "--folder", type=str,
                        help="create the folder")
    # Check input arguments
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
        
    print("URI Inputs: " + str(args.uri_inputs ))
    
    return args.uri_inputs , args.codec, args.bitrate, args.folder,

if __name__ == '__main__':
    uri_inputs , out_codec, out_bitrate, folder = parse_args()
    
    sys.exit(main(uri_inputs, out_codec, out_bitrate, folder))






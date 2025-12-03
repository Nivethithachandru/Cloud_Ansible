# from fastapi import APIRouter
# import os
# from aiocron import crontab
# import subprocess
# import threading
# from pathlib import Path
# from apps.main.models.model import LpuGroup
# from apps.main.database.db import get_db 
# from apps.main.utils.local_vendor import *
# import requests
# from requests.exceptions import RequestException, Timeout
# from logg import *
# from apps.main.config import *

# router = APIRouter()

# @router.on_event("startup")
# async def startup_event():
#     try:
#         print("************************* live")
#         # Get first camera information
#         first_camera_info = await get_camera_by_index(0)
#         #first_camera_info = await get_first_camera()

#         print("first_camera_info",first_camera_info)
        
#         if first_camera_info:
#             rtsp_url = first_camera_info['rtsp_url']  
#             rtsp_url = rtsp_url + '/Streaming/Channels/102/'           
#             first_cam_directory = Path(media_base_path) / f"HLS/kit/{first_camera_info['camera_ip']}/live_view"

            
#             # Delete existing .ts and .m3u8 files in the first camera directory
#             for file in first_cam_directory.glob('*.ts'):
#                 file.unlink()
#             for file in first_cam_directory.glob('*.m3u8'):
#                 file.unlink()

#             os.makedirs(first_cam_directory, exist_ok=True)
#             SEGMENT_PATH = first_cam_directory / f'live-%d_{first_camera_info["id"]}.ts'
#             M3U8_PATH = first_cam_directory / f'live_{first_camera_info["id"]}.m3u8'
#             ffmpeg_thread = threading.Thread(target=run_ffmpeg, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
#             ffmpeg_thread.start()

#         # Get second camera information
        
#         second_camera_info = await get_camera_by_index(1)
#         print("second_camera_info",second_camera_info)     
#         if second_camera_info:            
#             rtsp_url = second_camera_info['rtsp_url']
#             rtsp_url = rtsp_url + '/Streaming/Channels/102/'           
#             second_cam_directory = Path(media_base_path) / f"HLS/kit/{second_camera_info['camera_ip']}/live_view"

#             for file in second_cam_directory.glob('*.ts'):
#                 file.unlink()
#             for file in second_cam_directory.glob('*.m3u8'):
#                 file.unlink()
#             os.makedirs(second_cam_directory, exist_ok=True)
#             SEGMENT_PATH = second_cam_directory / f'live-%d_{second_camera_info["id"]}.ts'
#             M3U8_PATH = second_cam_directory / f'live_{second_camera_info["id"]}.m3u8'
#             ffmpeg_thread2 = threading.Thread(target=run_ffmpeg2, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
#             ffmpeg_thread2.start()

#     except Exception as e:
#         print("Error:", e)



# def run_ffmpeg(rtsp_url: str, segment_path: Path, m3u8_path: Path):
#     print("Started live from ",rtsp_url)
#     # cmd = (
#     #     f'ffmpeg -loglevel quiet -i "{rtsp_url}" '
#     #     f'-c:v copy -c:a aac -f hls -hls_time 3 '
#     #     f'-hls_list_size 5 -hls_flags delete_segments '
#     #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     # )
#     # cmd = (
#     #     f'ffmpeg -loglevel error '
#     #     f'-i "{rtsp_url}" '
#     #     f'-vsync 0 -copyts '
#     #     f'-c:v copy -c:a aac -movflags frag_keyframe+empty_moov '
#     #     f'-f hls -hls_time 3 -hls_list_size 5 -hls_flags delete_segments ' 
#     #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     # )
#     # cmd = (
#     #     f'ffmpeg -i {rtsp_url} '
#     #     '-loglevel quiet '
#     #     '-f hls '
#     #     '-vsync 0 '
#     #     '-copyts '
#     #     '-vcodec copy '
#     #     '-acodec copy '
#     #     '-movflags frag_keyframe+empty_moov '
#     #     '-hls_flags delete_segments '
#     #     '-segment_wrap 1 '
#     #     '-hls_time 3 '
#     #     '-hls_list_size 5 '
#     #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     # )
#     cmd = (
#         f'ffmpeg -i {rtsp_url} '
#         '-loglevel quiet '
#         '-f hls '        
#         '-vsync 0 '
#         '-copyts '
#         '-vcodec copy '
#         '-acodec copy '
#         '-movflags frag_keyframe+empty_moov '
#         '-hls_flags delete_segments+program_date_time+append_list '
#         '-segment_wrap 5 '
#         '-hls_time 3 '
#         '-hls_list_size 5 '
#         f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     )

    
#     try:
#         subprocess.run(cmd, shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"An error occurred while running FFmpeg: {e.stderr}")

# def run_ffmpeg2(rtsp_url: str, segment_path: Path, m3u8_path: Path):
#     # cmd = (
#     #     f'ffmpeg -loglevel quiet -i "{rtsp_url}" '
#     #     f'-c:v copy -c:a aac -f hls -hls_time 3 '
#     #     f'-hls_list_size 5 -hls_flags delete_segments '
#     #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     # )
#     # cmd = (
#     #     f'ffmpeg -loglevel error '
#     #     f'-i "{rtsp_url}" '
#     #     f'-vsync 0 -copyts '
#     #     f'-c:v copy -c:a aac -movflags frag_keyframe+empty_moov '
#     #     f'-f hls -hls_time 3 -hls_list_size 5 -hls_flags delete_segments ' 
#     #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     # )

#     cmd = (
#         f'ffmpeg -i {rtsp_url} '
#         '-loglevel quiet '
#         '-f hls '        
#         '-vsync 0 '
#         '-copyts '
#         '-vcodec copy '
#         '-acodec copy '
#         '-movflags frag_keyframe+empty_moov '
#         '-hls_flags delete_segments+program_date_time+append_list '
#         '-segment_wrap 5 '
#         '-hls_time 3 '
#         '-hls_list_size 5 '
#         f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
#     )
        

    
#     try:
#         subprocess.run(cmd, shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"An error occurred while running FFmpeg: {e.stderr}")




# async def start_camera_stream(camera_info):
#     rtsp_url = camera_info['rtsp_url']
#     print("Call thai restart",rtsp_url)
#     print("camera_info",camera_info)
#     print("camera_info -----",camera_info["id"],type(camera_info["id"]))    


#     camera_directory = Path(media_base_path) / f"HLS/kit/{camera_info['camera_ip']}/live_view"

#     # camera_directory = Path(media_base_path) / f'{folder_live_name}/HLS/live_view'
#     print("restart camera_directory",camera_directory)
#     for file in camera_directory.glob('*.ts'):
#         file.unlink()
#     for file in camera_directory.glob('*.m3u8'):
#         file.unlink()

#     os.makedirs(camera_directory, exist_ok=True)
#     SEGMENT_PATH = camera_directory / f'live-%d_{camera_info["id"]}.ts'
#     M3U8_PATH = camera_directory / f'live_{camera_info["id"]}.m3u8'
#     ffmpeg_thread = threading.Thread(target=run_ffmpeg, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
#     ffmpeg_thread.start()




# async def check_camera_status():
#     try:
#         cameras_info = await get_all_camera()
#         camera_statuses = []
#         db = next(get_db())
#         print("************1")
        
#         print("cameras_info",cameras_info)
#         for camera in cameras_info:
#             is_live = await check_hikvision_camera_status(camera['camera_ip'], camera['username'], camera['password'])
#             camera_statuses.append({
#                 "id": camera['id'],
#                 "lpu_id": camera['lpu_id'],
#                 "lpu_name": camera['lpu_name'],
#                 "is_live": is_live
#             })  
#             print("sdf",camera_statuses)
#             db_camera = db.query(LpuGroup).filter(LpuGroup.id == camera['id']).first()
#             if db_camera:
#                 previous_status = db_camera.camera_status
#                 db_camera.camera_status = is_live
#                 db.commit()  
                
#                 if previous_status!=is_live:
#                     print(f"Camera status change detected for LPU ID '{camera['lpu_id']}': "
#                                 f"status changed from {'ONLINE' if previous_status else 'OFFLINE'} to {'ONLINE' if is_live else 'OFFLINE'}.")

#                     CAMERA_LOGGER.info(
#                         f"Camera status change detected for LPU ID '{camera['lpu_id']}': "
#                         f"status changed from {'ONLINE' if previous_status else 'OFFLINE'} to {'ONLINE' if is_live else 'OFFLINE'}."
#                     )

#                 if not previous_status and is_live:
#                     print("Auto Calll",previous_status,is_live)
#                     await start_camera_stream(camera)
#     except Exception as e:
#         print("Error from camera status checking",e)


# @crontab('*/1 * * * *')
# async def cron_job():
#     print("Checking Camera status  cron job every minutes . . . . .")
#     await check_camera_status()



from fastapi import APIRouter
import os
from aiocron import crontab
import subprocess
import threading
from pathlib import Path
from apps.main.models.model import LpuGroup
from apps.main.database.db import get_db 
from apps.main.utils.local_vendor import *
import requests
from requests.exceptions import RequestException, Timeout
from logg import *
from apps.main.config import *

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    try:
        print("************************* live")
        # Get first camera information
        first_camera_info = await get_camera_by_index(0)
        #first_camera_info = await get_first_camera()

        print("first_camera_info",first_camera_info)
        
        if first_camera_info:
            rtsp_url = first_camera_info['rtsp_url']  
            rtsp_url = rtsp_url + '/Streaming/Channels/102/'           
            first_cam_directory = Path(media_base_path) / f"HLS/kit/{first_camera_info['camera_ip']}/live_view"

            
            # Delete existing .ts and .m3u8 files in the first camera directory
            for file in first_cam_directory.glob('*.ts'):
                file.unlink()
            for file in first_cam_directory.glob('*.m3u8'):
                file.unlink()

            os.makedirs(first_cam_directory, exist_ok=True)
            SEGMENT_PATH = first_cam_directory / f'live-%d_{first_camera_info["id"]}.ts'
            M3U8_PATH = first_cam_directory / f'live_{first_camera_info["id"]}.m3u8'
            ffmpeg_thread = threading.Thread(target=run_ffmpeg, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
            ffmpeg_thread.start()

        # Get second camera information
        
        second_camera_info = await get_camera_by_index(1)
        print("second_camera_info",second_camera_info)     
        if second_camera_info:            
            rtsp_url = second_camera_info['rtsp_url']
            rtsp_url = rtsp_url + '/Streaming/Channels/102/'           
            second_cam_directory = Path(media_base_path) / f"HLS/kit/{second_camera_info['camera_ip']}/live_view"

            for file in second_cam_directory.glob('*.ts'):
                file.unlink()
            for file in second_cam_directory.glob('*.m3u8'):
                file.unlink()
            os.makedirs(second_cam_directory, exist_ok=True)
            SEGMENT_PATH = second_cam_directory / f'live-%d_{second_camera_info["id"]}.ts'
            M3U8_PATH = second_cam_directory / f'live_{second_camera_info["id"]}.m3u8'
            ffmpeg_thread2 = threading.Thread(target=run_ffmpeg2, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
            ffmpeg_thread2.start()

    except Exception as e:
        print("Error:", e)



def run_ffmpeg(rtsp_url: str, segment_path: Path, m3u8_path: Path):
    print("Started live from ",rtsp_url)
    # cmd = (
    #     f'ffmpeg -loglevel quiet -i "{rtsp_url}" '
    #     f'-c:v copy -c:a aac -f hls -hls_time 3 '
    #     f'-hls_list_size 5 -hls_flags delete_segments '
    #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    # )
    # cmd = (
    #     f'ffmpeg -loglevel error '
    #     f'-i "{rtsp_url}" '
    #     f'-vsync 0 -copyts '
    #     f'-c:v copy -c:a aac -movflags frag_keyframe+empty_moov '
    #     f'-f hls -hls_time 3 -hls_list_size 5 -hls_flags delete_segments ' 
    #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    # )
    # cmd = (
    #     f'ffmpeg -i {rtsp_url} '
    #     '-loglevel quiet '
    #     '-f hls '
    #     '-vsync 0 '
    #     '-copyts '
    #     '-vcodec copy '
    #     '-acodec copy '
    #     '-movflags frag_keyframe+empty_moov '
    #     '-hls_flags delete_segments '
    #     '-segment_wrap 1 '
    #     '-hls_time 3 '
    #     '-hls_list_size 5 '
    #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    # )
    cmd = (
        f'ffmpeg -i {rtsp_url} '
        '-loglevel quiet '
        '-f hls '        
        '-vsync 0 '
        '-copyts '
        '-vcodec copy '
        '-acodec copy '
        '-movflags frag_keyframe+empty_moov '
        '-hls_flags delete_segments+program_date_time+append_list '
        '-segment_wrap 5 '
        '-hls_time 3 '
        '-hls_list_size 5 '
        f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    )

    
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running FFmpeg: {e.stderr}")

def run_ffmpeg2(rtsp_url: str, segment_path: Path, m3u8_path: Path):
    # cmd = (
    #     f'ffmpeg -loglevel quiet -i "{rtsp_url}" '
    #     f'-c:v copy -c:a aac -f hls -hls_time 3 '
    #     f'-hls_list_size 5 -hls_flags delete_segments '
    #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    # )
    # cmd = (
    #     f'ffmpeg -loglevel error '
    #     f'-i "{rtsp_url}" '
    #     f'-vsync 0 -copyts '
    #     f'-c:v copy -c:a aac -movflags frag_keyframe+empty_moov '
    #     f'-f hls -hls_time 3 -hls_list_size 5 -hls_flags delete_segments ' 
    #     f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    # )

    cmd = (
        f'ffmpeg -i {rtsp_url} '
        '-loglevel quiet '
        '-f hls '        
        '-vsync 0 '
        '-copyts '
        '-vcodec copy '
        '-acodec copy '
        '-movflags frag_keyframe+empty_moov '
        '-hls_flags delete_segments+program_date_time+append_list '
        '-segment_wrap 5 '
        '-hls_time 3 '
        '-hls_list_size 5 '
        f'-hls_segment_filename "{segment_path}" "{m3u8_path}"'
    )
        

    
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running FFmpeg: {e.stderr}")




async def start_camera_stream(camera_info):
    rtsp_url = camera_info['rtsp_url']
    print("Call thai restart",rtsp_url)
    print("camera_info",camera_info)
    print("camera_info -----",camera_info["id"],type(camera_info["id"]))    


    camera_directory = Path(media_base_path) / f"HLS/kit/{camera_info['camera_ip']}/live_view"

    # camera_directory = Path(media_base_path) / f'{folder_live_name}/HLS/live_view'
    print("restart camera_directory",camera_directory)
    for file in camera_directory.glob('*.ts'):
        file.unlink()
    for file in camera_directory.glob('*.m3u8'):
        file.unlink()

    os.makedirs(camera_directory, exist_ok=True)
    SEGMENT_PATH = camera_directory / f'live-%d_{camera_info["id"]}.ts'
    M3U8_PATH = camera_directory / f'live_{camera_info["id"]}.m3u8'
    ffmpeg_thread = threading.Thread(target=run_ffmpeg, args=(rtsp_url, SEGMENT_PATH, M3U8_PATH))
    ffmpeg_thread.start()




async def check_camera_status():
    try:
        cameras_info = await get_all_camera()
        camera_statuses = []
        db = next(get_db())
        print("************1")
        
        print("cameras_info",cameras_info)
        for camera in cameras_info:
            is_live = await check_hikvision_camera_status(camera['camera_ip'], camera['username'], camera['password'])
            camera_statuses.append({
                "id": camera['id'],
                "lpu_id": camera['lpu_id'],
                "lpu_name": camera['lpu_name'],
                "is_live": is_live
            })  
            print("sdf",camera_statuses)
            db_camera = db.query(LpuGroup).filter(LpuGroup.id == camera['id']).first()
            if db_camera:
                previous_status = db_camera.camera_status
                db_camera.camera_status = is_live
                db.commit()  
                
                if previous_status!=is_live:
                    print(f"Camera status change detected for LPU ID '{camera['lpu_id']}': "
                                f"status changed from {'ONLINE' if previous_status else 'OFFLINE'} to {'ONLINE' if is_live else 'OFFLINE'}.")

                    CAMERA_LOGGER.info(
                        f"Camera status change detected for LPU ID '{camera['lpu_id']}': "
                        f"status changed from {'ONLINE' if previous_status else 'OFFLINE'} to {'ONLINE' if is_live else 'OFFLINE'}."
                    )

                if not previous_status and is_live:
                    print("Auto Calll",previous_status,is_live)
                    await start_camera_stream(camera)
    except Exception as e:
        print("Error from camera status checking",e)


# @crontab('*/5 * * * *')
# async def cron_job():
#     print("Checking Camera status  cron job every minutes . . . . .")
#     await check_camera_status()

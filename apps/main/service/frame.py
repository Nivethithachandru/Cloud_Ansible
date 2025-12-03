from fastapi import FastAPI ,HTTPException ,BackgroundTasks ,APIRouter,Form,Query
from fastapi_utilities import repeat_every
import asyncio
import websockets
import cv2
import base64
import threading
import json
import numpy as np
from apps.main.models.get_details import Get_cameras




uri_camera1 = "ws://157.173.221.23:8000/ws/livestream/1/"
uri_camera2 = "ws://157.173.221.23:8000/ws/livestream/2/"
uri_camera3 = "ws://157.173.221.23:8000/ws/livestream/3/"
uri_camera4 = "ws://157.173.221.23:8000/ws/livestream/4/"

router=APIRouter()
camera = Get_cameras()



# @router.on_event('startup')
# @repeat_every(seconds=1800)
# async def cron_job():
#     threading.Thread(target=run_web_frame_in_thread).start()

# @router.on_event('startup')
# @repeat_every(seconds=1800)
# async def cron_job():
#     threading.Thread(target=run_web_frame_in_thread1).start()

# @router.on_event('startup')
# @repeat_every(seconds=1800)
# async def cron_job():
#     threading.Thread(target=run_web_frame_in_thread2).start()

# @router.on_event('startup')
# @repeat_every(seconds=1800)
# async def cron_job():
#     threading.Thread(target=run_web_frame_in_thread3).start()


def run_web_frame_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_frame())
    loop.close()


async def send_frame():
    camera_details = camera.camera_find('1')
    print("success",camera_details)
    if camera_details:
        rtsp_link = camera.create_rtsp_link(camera_details)
        print(rtsp_link)
        async def connect_and_send():
            nonlocal rtsp_link
            while True:
                cap = cv2.VideoCapture(rtsp_link)
                if not cap.isOpened():
                    print(f"Failed to open RTSP stream for camera {camera_details.get('camera_id')}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(uri_camera1) as websocket:
                    print(f"Connected to the WebSocket server for camera {camera_details.get('camera_id')}")
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            print(f"Failed to grab frame for camera {camera_details.get('camera_id')}. Reconnecting...")
                            break

                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 35]
                        image = cv2.resize(frame, (400, 300), interpolation=cv2.INTER_NEAREST)
                        result, imgencode = cv2.imencode('.jpg', image, encode_param)
                        if not result:
                            print(f"Failed to encode frame for camera {camera_details.get('camera_id')}")
                            continue

                        data = np.array(imgencode)
                        c_img = data.tobytes()
                        c_img = base64.b64encode(c_img).decode()
                        data = json.dumps({
                            "type": "stream",
                            "frame": c_img
                        })
                        try:
                            await websocket.send(data)
                        except websockets.ConnectionClosed:
                            print(f"Connection closed for camera {camera_details.get('camera_id')}. Reconnecting...")
                            break

                cap.release()
                await asyncio.sleep(5)  # Wait before trying to reconnect

        while True:
            try:
                await connect_and_send()
            except (websockets.ConnectionClosed, websockets.InvalidURI, websockets.InvalidHandshake) as e:
                print(f"Connection error for camera {camera.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Awn unexpected error occurred for camera {camera_details.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)


    else:
        print(f"Camera with ID {camera_details.get('camera_id')} not found in the database")


def run_web_frame_in_thread1():
    loop1 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop1)
    loop1.run_until_complete(send_frame1())
    loop1.close()


async def send_frame1():
    camera_details1 = camera.camera_find('2')
    print("success")
    if camera_details1:
        rtsp_link = camera.create_rtsp_link(camera_details1)
        print(rtsp_link)
        async def connect_and_send():
            nonlocal rtsp_link
            while True:
                cap = cv2.VideoCapture(rtsp_link)
                if not cap.isOpened():
                    print(f"Failed to open RTSP stream for camera {camera_details1.get('camera_id')}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(uri_camera2) as websocket:
                    print(f"Connected to the WebSocket server for camera {camera_details1.get('camera_id')}")
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            print(f"Failed to grab frame for camera {camera_details1.get('camera_id')}. Reconnecting...")
                            break

                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 35]
                        image = cv2.resize(frame, (400, 300), interpolation=cv2.INTER_NEAREST)
                        result, imgencode = cv2.imencode('.jpg', image, encode_param)
                        if not result:
                            print(f"Failed to encode frame for camera {camera_details1.get('camera_id')}")
                            continue

                        data = np.array(imgencode)
                        c_img = data.tobytes()
                        c_img = base64.b64encode(c_img).decode()
                        data = json.dumps({
                            "type": "stream",
                            "frame": c_img
                        })
                        try:
                            await websocket.send(data)
                        except websockets.ConnectionClosed:
                            print(f"Connection closed for camera {camera_details1.get('camera_id')}. Reconnecting...")
                            break

                cap.release()
                await asyncio.sleep(5)  # Wait before trying to reconnect

        while True:
            try:
                await connect_and_send()
            except (websockets.ConnectionClosed, websockets.InvalidURI, websockets.InvalidHandshake) as e:
                print(f"Connection error for camera {camera_details1.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Andf unexpected error occurred for camera {camera_details1.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)


    else:
        print(f"Camera with ID {camera_details1.get('camera_id')} not found in the database")

 
def run_web_frame_in_thread2():
    loop2 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop2)
    loop2.run_until_complete(send_frame2())
    loop2.close()


async def send_frame2():
    camera_details2 = camera.camera_find('3')
    print("success")
    if camera_details2:
        rtsp_link = camera.create_rtsp_link(camera_details2)
        print(rtsp_link)
        async def connect_and_send():
            nonlocal rtsp_link
            while True:
                cap = cv2.VideoCapture(rtsp_link)
                if not cap.isOpened():
                    print(f"Failed to open RTSP stream for camera {camera_details2.get('camera_id')}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(uri_camera3) as websocket:
                    print(f"Connected to the WebSocket server for camera {camera_details2.get('camera_id')}")
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            print(f"Failed to grab frame for camera {camera_details2.get('camera_id')}. Reconnecting...")
                            break

                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 35]
                        image = cv2.resize(frame, (400, 300), interpolation=cv2.INTER_NEAREST)
                        result, imgencode = cv2.imencode('.jpg', image, encode_param)
                        if not result:
                            print(f"Failed to encode frame for camera {camera_details2.get('camera_id')}")
                            continue

                        data = np.array(imgencode)
                        c_img = data.tobytes()
                        c_img = base64.b64encode(c_img).decode()
                        data = json.dumps({
                            "type": "stream",
                            "frame": c_img
                        })
                        try:
                            await websocket.send(data)
                        except websockets.ConnectionClosed:
                            print(f"Connection closed for camera {camera_details2.get('camera_id')}. Reconnecting...")
                            break

                cap.release()
                await asyncio.sleep(5)  # Wait before trying to reconnect

        while True:
            try:
                await connect_and_send()
            except (websockets.ConnectionClosed, websockets.InvalidURI, websockets.InvalidHandshake) as e:
                print(f"Connection error for camera {camera_details2.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Ansdfd unexpected error occurred for camera {camera_details2.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)


    else:
        print(f"Camera with ID {camera_details2.get('camera_id')} not found in the database")

def run_web_frame_in_thread3():
    loop2 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop2)
    loop2.run_until_complete(send_frame3())
    loop2.close()


async def send_frame3():
    camera_details3 = camera.camera_find('4')
    print("success")
    if camera_details3:
        rtsp_link = camera.create_rtsp_link(camera_details3)
        print(rtsp_link)
        async def connect_and_send():
            nonlocal rtsp_link
            while True:
                cap = cv2.VideoCapture(rtsp_link)
                if not cap.isOpened():
                    print(f"Failed to open RTSP stream for camera {camera_details3.get('camera_id')}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(uri_camera4) as websocket:
                    print(f"Connected to the WebSocket server for camera {camera_details3.get('camera_id')}")
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            print(f"Failed to grab frame for camera {camera_details3.get('camera_id')}. Reconnecting...")
                            break

                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 35]
                        image = cv2.resize(frame, (400, 300), interpolation=cv2.INTER_NEAREST)
                        result, imgencode = cv2.imencode('.jpg', image, encode_param)
                        if not result:
                            print(f"Failed to encode frame for camera {camera_details3.get('camera_id')}")
                            continue

                        data = np.array(imgencode)
                        c_img = data.tobytes()
                        c_img = base64.b64encode(c_img).decode()
                        data = json.dumps({
                            "type": "stream",
                            "frame": c_img
                        })
                        try:
                            await websocket.send(data)
                        except websockets.ConnectionClosed:
                            print(f"Connection closed for camera {camera_details3.get('camera_id')}. Reconnecting...")
                            break

                cap.release()
                await asyncio.sleep(5)  # Wait before trying to reconnect

        while True:
            try:
                await connect_and_send()
            except (websockets.ConnectionClosed, websockets.InvalidURI, websockets.InvalidHandshake) as e:
                print(f"Connection error for camera {camera_details3.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Ansdfd unexpected error occurred for camera {camera_details3.get('camera_id')}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)


    else:
        print(f"Camera with ID {camera_details3.get('camera_id')} not found in the database")
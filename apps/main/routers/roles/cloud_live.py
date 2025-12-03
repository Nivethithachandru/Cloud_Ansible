from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

router = APIRouter()

# Store active connections as dictionary {websocket: camera_id}
connected_clients = {}

@router.websocket("/ws/livestream/{camera_id}/")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    print(f"[SERVER] WebSocket connected for Camera {camera_id}")


    # Store client with associated camera ID
    connected_clients[websocket] = camera_id

    # Create a background task to handle messages
    task = asyncio.create_task(handle_websocket(websocket, camera_id))

    try:
        await task  # Keep the WebSocket connection alive
    finally:
        # Clean up disconnected clients
        connected_clients.pop(websocket, None)

async def handle_websocket(websocket: WebSocket, camera_id: str):
    """Handles incoming messages from the WebSocket connection."""
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "stream":
                frame_base64 = message["frame"]
                print(f"[SERVER] Received Frame from Camera {camera_id} - {len(frame_base64)} bytes")

                # Send frame to all connected clients watching this camera
                await send_to_clients(camera_id, frame_base64)

            await asyncio.sleep(0.1)  # Reduce frame sending rate

    except WebSocketDisconnect:
        print(f"[SERVER] WebSocket disconnected for Camera {camera_id}")

    except Exception as e:
        print(f"[SERVER] Error: {e}")

    finally:
        connected_clients.pop(websocket, None)



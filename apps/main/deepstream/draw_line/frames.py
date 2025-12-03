import cv2
import os
import time

rtsp_url = "rtsp://admin:cosmdumayil1965@10.0.0.38:554 "
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Error: Unable to open RTSP stream.")
    exit()

width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Stream resolution: {width}x{height}, FPS: {fps}")


fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_video = cv2.VideoWriter('/home/cosai/deepstream_python_apps-1.1.1/apps/deepstream-rtsp-in-rtsp-out/draw_line/output/video/output_video.mp4', fourcc, 20.0, (640, 480))

frame_folder = "/home/cosai/deepstream_python_apps-1.1.1/apps/deepstream-rtsp-in-rtsp-out/draw_line/output/frames"
os.makedirs(frame_folder, exist_ok=True)

start_time = time.time()
frame_count = 0

while True:
    ret, frame = cap.read() 
    if not ret:
        print("Failed to grab frame.")
        break

    frame_filename = os.path.join(frame_folder, f"frame_{frame_count:04d}.jpg")
    cv2.imwrite(frame_filename, frame)


    out_video.write(frame)
    
    cv2.imshow("Frame", frame)

    frame_count += 1
    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    if elapsed_time > 300:  
        print("Time limit reached, stopping capture.")
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
out_video.release()
cv2.destroyAllWindows()

print("Finished capturing frames and video.")

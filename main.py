import os
current_file_path = os.path.abspath(__file__)
previous_file_path = os.path.dirname(current_file_path)
previous_file_path1 = os.path.dirname(previous_file_path)
STORE_ROOT = os.path.join(previous_file_path1, 'RVTL_ASSETS/')
# os.makedirs(STORE_ROOT, exist_ok=True) 
CLASSES_ROOT = os.path.join(previous_file_path, 'class.txt')

if __name__ == "__main__":
    import uvicorn

    # uvicorn.run("apps.main.app:app", host="0.0.0.0", port=8016,reload=True, lifespan="on", proxy_headers=True)  
    uvicorn.run("apps.main.app:app", host="0.0.0.0", port=8016, lifespan="on", proxy_headers=True)  
   

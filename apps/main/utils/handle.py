from fastapi import HTTPException


def ResponseModel(data, message):
    return {
        "status":"success",
        "data": data,
        "message": message,
    }
def OndemandResponce(default_code,file_Status,count, response_data):
    return {
        "status" : "success",
        "status_code" : "201",
        "default_code" :default_code,
        "file_status" : file_Status,
        "total_file_count" : count,
        "data" :response_data
    }
def ErrorResponseModel(status_code, message):
    return {
        "status":"failed",
        "status_code": status_code,
        "message": message,
    }

def EntrypointNotFound(default_code,message):
    return{
        "status":"failed",
        "default_code":default_code,
        "message":message
    }

def NotFoundError(default_code, message):
    error_data = {
        "status": "failed",
        "status_code": 404,
        "default_code": default_code,
        "message": message
    }
    print(error_data)
    raise HTTPException(status_code=404, detail=error_data)

def CameraConfigurefailed(default_code, message):
    error_data ={
        "status" : "failed",
        "status_code": 404,
        "default_code" : default_code,
        "message" : message
    }
    print(error_data)
    raise HTTPException(status_code=404, detail=error_data)

def AlreadyExist(default_code, message):
    error_data = {
        "status": "failed",
        "status_code": 409,
        "default_code": default_code,
        "message": message
    }
    print(error_data)
    raise HTTPException(status_code=404, detail=error_data)



def FailedCreate_rtsp(default_code,message):
    error_data ={
        "status":"failed",
        "default_code":default_code,
        "message":message
    }
    print(error_data)
    raise HTTPException(status_code=404, detail=error_data)

def Failed_hlsnotworking(default_code,message):
    error_data = {
        "status":"failed",
        "default_code":default_code,
        "message":message
    }
    print(error_data)
    raise HTTPException(status_code=404, detail=error_data)

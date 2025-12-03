import requests 
import json
import xmltodict
from apps.main.utils.handle import *

class CameraController:

    def __init__(self, ipaddress, username, password):
        self.ipaddress = ipaddress
        self.username = username
        self.password = password
        self.auth = requests.auth.HTTPDigestAuth(username, password)
        self.base_url = f'http://{ipaddress}:80/ISAPI/'

    def _get_request(self,endpoint):
        url = self.base_url + endpoint
        response = requests.get(url, auth =self.auth)
        response.raise_for_status() 
        return response.content
        
    
    def _put_request(self, json_data, endpoint):
        url = self.base_url + endpoint
        json_to_xml = xmltodict.unparse(json_data)        
        # print("________")
        # print(endpoint)
        try:
            response = requests.put(url, json_to_xml, auth=self.auth)
            response.raise_for_status()           
            return response.status_code 
        except requests.exceptions.HTTPError as e:          
            return ErrorResponseModel(e.response.status_code, f"HTTP Error: {str(e.response.content)}")
        except requests.exceptions.RequestException as e:
            return ErrorResponseModel("500", f"Request Exception: {str(e.response.content)}")
        

    def _get_cvrtdic(self,xml_data):
        json_data = xmltodict.parse(xml_data)
        return json_data
    
    def set_localtimezone(self,timezone):        
        endpoint = 'System/time'
        xml_data = self._get_request(endpoint)
        json_data = self._get_cvrtdic(xml_data)
        json_data['Time']['localTime'] = timezone
        request_status = self._put_request(json_data,endpoint)        
        return request_status
        
    def set_videovalue(self,v_width,v_height,fps):
        endpoint = 'Streaming/channels'
        xml_data = self._get_request(endpoint)
        json_data = self._get_cvrtdic(xml_data)
        for channel in json_data['StreamingChannelList']['StreamingChannel']:
            if channel['id'] == '101': 
                     
                if fps == 100:
                    fps =channel['Video']['maxFrameRate']
                else:      
                    channel['Video']['maxFrameRate'] =fps  

                if v_width is None and v_height is None:
                    v_width = channel['Video']['videoResolutionWidth'] 
                    v_height = channel['Video']['videoResolutionHeight'] 
                else:
                    channel['Video']['videoResolutionWidth'] = v_width
                    channel['Video']['videoResolutionHeight']  = v_height
                
                request_status = self._put_request(json_data,endpoint)
                break  
        return request_status
    
    def set_bitrate(self,bitRate):
        endpoint = 'Streaming/channels'
        xml_data = self._get_request(endpoint)
        json_data = self._get_cvrtdic(xml_data)
        for channel in json_data['StreamingChannelList']['StreamingChannel']:
            if channel['id'] == '101':                                
                channel['Video']['constantBitRate'] =bitRate                         
                request_status = self._put_request(json_data,endpoint)
                break  
        return request_status
    

    def _cameranameupdate(self,camera_name,json_data,endpoint):
        json_data['VideoInputChannel']['name'] = camera_name
        request_status = self._put_request(json_data,endpoint)
        return request_status
    
    def __textnameupdate(self,text_overlay,text_overlay_endpoint):        
        xml_data = self._get_request(text_overlay_endpoint)
        json_data = self._get_cvrtdic(xml_data)          
        json_data['TextOverlayList']['TextOverlay']['displayText'] = text_overlay        
        request_status = self._put_request(json_data,text_overlay_endpoint)
        return request_status
    

    def set_nameoverlay(self,text_overlay,camera_name): 
        endpoint = 'System/Video/inputs/channels/1/'  
        text_overlay_endpoint = endpoint +  'overlays/text'    
        xml_data = self._get_request(endpoint)
        json_data = self._get_cvrtdic(xml_data)        

        # if text_overlay is not None:
        #     text_overlay_status = self.__textnameupdate(text_overlay,text_overlay_endpoint)            
        #     if text_overlay_status != 200:
        #         return text_overlay_status
        if camera_name is not None:
            camera_request_status = self._cameranameupdate(camera_name,json_data,endpoint)
            if camera_request_status != 200:
                return camera_request_status
        

        
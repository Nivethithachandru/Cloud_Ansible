import psutil
import subprocess
import os
import time

class SystemMonitor:
    # def __init__(self):
        # self.jetson = jtop()

    def cpu_usage(self):
        cpu_percent = psutil.cpu_percent()        
        cpu_count = psutil.cpu_count()
        
        return {
            "cpu_cores" : cpu_count,
            "cpu_percentage_usage": round(cpu_percent)
        }

    def ram_usage(self):
        ram_info = psutil.virtual_memory()
        return {
            "total_ram_gb": f"{ram_info.total / 1024 / 1024 / 1024:.2f}",
            "used_ram_gb": f"{ram_info.used / 1024 / 1024 / 1024:.2f}",
            "ram_percentage_usage": f"{ram_info.percent:.2f}"
        }
    

    def disk_usage(self):
        disk_info = psutil.disk_usage("/")
        return {
            #"total_disk_gb": f"{disk_info.total / 1024 / 1024 / 1024:.2f}",
            "total_disk_gb": round(disk_info.total / (1024 ** 3)),
            "used_disk_gb": round(disk_info.used / (1024 ** 3)),
            "free_disk_gb": round(disk_info.free / (1024 ** 3))
        }






    def jtop_details(self):
        data = {}

        try:
            
            temps = psutil.sensors_temperatures()
            print("temps:",temps)
            data['cpu_temperature'] = temps.get('coretemp', [{'current': "0"}])[0]['current']

           
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            data['system_uptime'] = f"{days}d {hours}h {minutes}m {seconds}s"

            
            data['load_average'] = os.getloadavg() if hasattr(os, "getloadavg") else "0"

         
            fan_speed = psutil.sensors_fans()
            data['kit_fan_speed'] = fan_speed if fan_speed else "0"

        except Exception as e:
            print(f"Error retrieving system details: {e}")

        return data




                 

    
    def get_gpu_usage(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'gpu' in proc.info['name'].lower():
                    pid = proc.info['pid']
                    gpu_usage = psutil.Process(pid).cpu_percent(interval=1)
                    return {"gpu_usage": gpu_usage}
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return {"gpu_usage": None}




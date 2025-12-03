import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from apps.main.config import media_base_path
from datetime import datetime, timedelta


LOGS_ROOT = os.path.join(media_base_path, 'LOGS/')
os.makedirs(LOGS_ROOT, exist_ok=True)


def setup_logger(module_name):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    date_folder_path  = os.path.join(LOGS_ROOT,current_date)
    os.makedirs(date_folder_path, exist_ok=True)
    log_file_path = os.path.join(date_folder_path, f"{module_name}.log")

    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=50000000,
        backupCount=5
    )

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger


def read_logs(action: str, from_date: str, to_date: str):
    log_entries = []
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        current_date = from_dt

        while current_date <= to_dt:
            date_str = current_date.strftime("%Y-%m-%d")
            date_folder_path = os.path.join(LOGS_ROOT, date_str)
            log_file_path = os.path.join(date_folder_path, f"{action}.log")

            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    log_entries.extend(log_file.readlines())

            current_date += timedelta(days=1)

        if not log_entries:
            return None  # No logs found in range
        return "".join(log_entries)

    except Exception as e:
        print(f"Error reading logs: {e}")
        return None







KIT_MONITOR_LOGGER = setup_logger("kit")
CAMERA_LOGGER = setup_logger("camera")
REPORT_LOGGER = setup_logger("report")
AUDIT_LOGGER = setup_logger("audit")
ROLES_LOGGER = setup_logger("roles")

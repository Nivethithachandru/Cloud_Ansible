from fastapi import  APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse,RedirectResponse
from apps.main.database.db import get_db 
from apps.main.models.model import * 
from apps.main.utils.jwt import *
from fastapi.templating import Jinja2Templates
from apps.main.routers.roles.auth_role import *
from sqlalchemy import text


router = APIRouter()
templates = Jinja2Templates(directory="apps/main/front_end/templates")


# @router.get('/main/project/{project_id}/detect/{detect_id}/report/', response_class=HTMLResponse, name="auth.report_monitor")
# async def report_monitor(request: Request, project_id: int, detect_id: int):
#     try:
#         db = next(get_db())

#         # SQL: class-wise counts
#         sql = text("""
#             SELECT mc.m_classes_id AS class_id,
#                    mc.m_classes_name AS class_name,
#                    COUNT(ko.id) AS count
#             FROM module_class_group mc
#             LEFT JOIN kit1_objectdetection ko
#               ON ko.vehicle_class_id = mc.m_classes_id
#              AND ko.project_id = :project_id
#              AND ko.detection_id = :detect_id
#             GROUP BY mc.m_classes_id, mc.m_classes_name
#             ORDER BY mc.m_classes_id DESC
#         """)
#         class_results = db.execute(sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()

#         # Total vehicle count
#         total_sql = text("""
#             SELECT COUNT(*) FROM kit1_objectdetection
#              WHERE project_id = :project_id AND detection_id = :detect_id
#         """)
#         total_vehicle_count = db.execute(total_sql, {"project_id": project_id, "detect_id": detect_id}).scalar()

#         # Add percentage to each result
#         class_data = []
#         for row in class_results:
#             percentage = (row.count / total_vehicle_count * 100) if total_vehicle_count else 0
#             class_data.append({
#                 "class_id": row.class_id,
#                 "class_name": row.class_name,
#                 "count": row.count,
#                 "percentage": round(percentage, 2)
#             })
 
#         session_data, error_response = handle_session(request)
#         if error_response:
#             return RedirectResponse(url="/")

#         return templates.TemplateResponse("report_monitor.html", {
#             "request": request,
#             "session": session_data,
#             "project_id": project_id,
#             "detect_id": detect_id,
#             "class_results": class_data,
#             "total_vehicle_count": total_vehicle_count
#         })
#     except Exception as e:
#         print("Error from Report Monitoring", e)
 


@router.get('/main/project/{project_id}/detect/{detect_id}/report/', response_class=HTMLResponse, name="auth.report_monitor")
async def report_monitor(request: Request, project_id: int, detect_id: int):
    try:
        # -------------------------------
        # Session check
        # -------------------------------
        session_data, error_response = handle_session(request)
        if error_response:
            return RedirectResponse(url="/")

        db = next(get_db())

        # -------------------------------
        # Detection log info
        # -------------------------------
        detection_sql = text("""
            SELECT d.start_time, d.end_time, d.line_id, p.project_name
            FROM detection_log d
            LEFT JOIN project p ON d.project_id = p.project_id
            WHERE d.project_id = :project_id AND d.detection_id = :detect_id
            LIMIT 1
        """)
        detection_info = db.execute(detection_sql, {
            "project_id": project_id,
            "detect_id": detect_id
        }).fetchone()

        project_name = detection_info.project_name if detection_info and detection_info.project_name else "Unknown"
        start_time = detection_info.start_time.strftime("%Y-%m-%d %H:%M:%S") if detection_info and detection_info.start_time else "N/A"
        end_time = detection_info.end_time.strftime("%Y-%m-%d %H:%M:%S") if detection_info and detection_info.end_time else "N/A"
        line_id = detection_info.line_id if detection_info and detection_info.line_id else "N/A"
        line_id_map = {
            "line_id_1": "Up",
            "line_id_2": "Down",
            "line_id_3": "Both"
        }
        line_id_label = line_id_map.get(str(line_id), line_id)

        # -------------------------------
        # Vehicle counts grouped by class
        # -------------------------------
        grouped_sql = text("""
            SELECT vehicle_class_id, ai_class, COUNT(*) AS total
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY vehicle_class_id, ai_class
            ORDER BY ai_class DESC
        """)
        grouped_results = db.execute(grouped_sql, {
            "project_id": project_id,
            "detect_id": detect_id
        }).fetchall()

        total_vehicle_count = sum(row.total for row in grouped_results)

        class_results = []
        for row in grouped_results:
            percent = round((row.total / total_vehicle_count) * 100, 2) if total_vehicle_count else 0
            class_results.append({
                "class_name": row.ai_class or "Unknown",
                "vehicle_class_id": row.vehicle_class_id or 0,
                "count": int(row.total or 0),
                "percentage": percent
            })

        # -------------------------------
        # Hourly counts
        # -------------------------------
        hourly_sql = text("""
            SELECT DATE(date_time) AS day,
                   EXTRACT(HOUR FROM date_time) AS hour,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY day, hour
            ORDER BY day, hour
        """)
        hourly_rows = db.execute(hourly_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        hourly_counts = []
        for row in hourly_rows:
            day_str = row.day.strftime("%Y-%m-%d") if row.day else "Unknown"
            hour_val = int(row.hour) if row.hour is not None else 0
            label = f"{day_str} {hour_val:02d}:00"
            hourly_counts.append({"hour_label": label, "count": int(row.count or 0)})

        # -------------------------------
        # Weekly counts
        # -------------------------------
        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        weekly_sql = text("""
            SELECT EXTRACT(DOW FROM date_time) AS weekday,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY weekday ORDER BY weekday
        """)
        weekly_rows = db.execute(weekly_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        weekly_counts = []
        for row in weekly_rows:
            day_label = weekdays[int(row.weekday)] if row.weekday is not None else "Unknown"
            weekly_counts.append({"weekday_label": day_label, "count": int(row.count or 0)})

        # -------------------------------
        # Daily counts 
        # -------------------------------
        daily_sql = text("""
            SELECT DATE(date_time) AS day, COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY day ORDER BY day
        """)
        daily_rows = db.execute(daily_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        daily_counts = []
        for row in daily_rows:
            day_str = row.day.strftime("%Y-%m-%d") if row.day else "Unknown"
            daily_counts.append({"day_label": day_str, "count": int(row.count or 0)})

        # -------------------------------
        # Weekly class counts
        # -------------------------------
        weekly_class_sql = text("""
            SELECT EXTRACT(DOW FROM date_time) AS weekday,
                   ai_class,
                   COUNT(*) AS total
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY weekday, ai_class
            ORDER BY weekday, ai_class
        """)
        weekly_class_results = db.execute(weekly_class_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        weekly_data = {}
        class_names = list(set([row.ai_class for row in weekly_class_results if row.ai_class]))

        # Init with 0
        for cls in class_names:
            weekly_data[cls] = [0] * 7

        for row in weekly_class_results:
            day = int(row.weekday) if row.weekday is not None else 0
            cls = row.ai_class or "Unknown"
            weekly_data.setdefault(cls, [0]*7)
            weekly_data[cls][day] = int(row.total or 0)

        # -------------------------------
        # Peak Traffic Analysis
        # -------------------------------

        # 1️⃣ Peak hour per day
        peak_hour_sql = text("""
            SELECT DATE(date_time) AS day,
                   EXTRACT(HOUR FROM date_time) AS hour,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY day, hour
        """)
        peak_hour_data = db.execute(peak_hour_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()

        peak_hours_per_day = {}
        for row in peak_hour_data:
            day_str = row.day.strftime("%Y-%m-%d")
            hour = int(row.hour)
            count = int(row.count)
            if day_str not in peak_hours_per_day or count > peak_hours_per_day[day_str]["count"]:
                peak_hours_per_day[day_str] = {"hour": f"{hour:02d}:00", "count": count}

        # 2️⃣ Peak day per week
        peak_day_week_sql = text("""
            SELECT EXTRACT(DOW FROM date_time) AS weekday,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY weekday
        """)
        week_rows = db.execute(peak_day_week_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        weekdays_map = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        peak_day_of_week = {"weekday": "N/A", "count": 0}
        for row in week_rows:
            day_label = weekdays_map[int(row.weekday)]
            count = int(row.count)
            if count > peak_day_of_week["count"]:
                peak_day_of_week = {"weekday": day_label, "count": count}

        # Peak day per month
        peak_day_month_sql = text("""
            SELECT DATE(date_time) AS day,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY day
            ORDER BY count DESC
            LIMIT 1
        """)
        peak_day_month_row = db.execute(peak_day_month_sql, {"project_id": project_id, "detect_id": detect_id}).fetchone()
        peak_day_of_month = {
            "day": peak_day_month_row.day.strftime("%Y-%m-%d") if peak_day_month_row else "N/A",
            "count": int(peak_day_month_row.count) if peak_day_month_row else 0
        }

        # -------------------------------
        # Prepare Peak Traffic Data for Charts
        # -------------------------------
        hourly_peak_data = {
            "hours": [item["hour_label"] for item in hourly_counts],
            "counts": [item["count"] for item in hourly_counts],
        }

        daily_peak_data = {
            "days": [item["day_label"] for item in daily_counts],
            "counts": [item["count"] for item in daily_counts],
        }

        weekly_peak_data = {
            "weeks": [item["weekday_label"] for item in weekly_counts],
            "counts": [item["count"] for item in weekly_counts],
        }

        monthly_peak_data = {
            "days": [item["day_label"].split("-")[-1] for item in daily_counts],
            "counts": [item["count"] for item in daily_counts],
        }

        yearly_sql = text("""
            SELECT TO_CHAR(date_time, 'Mon') AS month,
                   COUNT(*) AS count
            FROM kit1_objectdetection
            WHERE project_id = :project_id AND detection_id = :detect_id
            GROUP BY month
            ORDER BY MIN(date_time)
        """)
        yearly_rows = db.execute(yearly_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
        yearly_peak_data = {
            "months": [row.month for row in yearly_rows],
            "counts": [int(row.count or 0) for row in yearly_rows],
        }

        # -------------------------------
        # Return to template
        # -------------------------------
        return templates.TemplateResponse("report_monitor.html", {
            "request": request,
            "session": session_data,
            "project_name": project_name,
            "start_time": start_time,
            "end_time": end_time,
            "line_id": line_id_label,
            "detection_id": detect_id,
            "total_vehicle_count": total_vehicle_count,
            "class_results": class_results,
            "hourly_counts": hourly_counts,
            "weekly_counts": weekly_counts,
            "daily_counts": daily_counts,
            "weekly_data": weekly_data,
            "class_names": class_names,
            "peak_hours_per_day": peak_hours_per_day,
            "peak_day_of_week": peak_day_of_week,
            "peak_day_of_month": peak_day_of_month,
            "hourly_peak_data": hourly_peak_data,
            "daily_peak_data": daily_peak_data,
            "weekly_peak_data": weekly_peak_data,
            "monthly_peak_data": monthly_peak_data,
            "yearly_peak_data": yearly_peak_data,
            "peak_hours_per_day": peak_hours_per_day,
            "peak_day_of_week": peak_day_of_week,
            "peak_day_of_month": peak_day_of_month
        })

    except Exception as e:
        print("Error from Report Monitoring:", e)
        return templates.TemplateResponse("report_monitor.html", {
            "request": request,
            "session": {},
            "project_name": "Unknown",
            "start_time": "N/A",
            "end_time": "N/A",
            "line_id": "N/A",
            "detection_id": detect_id,
            "total_vehicle_count": 0,
            "class_results": [],
            "hourly_counts": [],
            "weekly_counts": [],
            "daily_counts": [],
            "weekly_data": {},
            "class_names": [],
            "peak_hours_per_day": [],
            "peak_day_of_week": [],
            "peak_day_of_month": [],
            "hourly_peak_data": {},
            "daily_peak_data": {},
            "weekly_peak_data": {},
            "monthly_peak_data": {},
            "yearly_peak_data": {},
            "peak_hours_per_day": peak_hours_per_day,
            "peak_day_of_week": peak_day_of_week,
            "peak_day_of_month": peak_day_of_month
        })




# @router.get('/main/project/{project_id}/detect/{detect_id}/report/', response_class=HTMLResponse, name="auth.report_monitor")
# async def report_monitor(request: Request, project_id: int, detect_id: int):
#     # Initialize variables to avoid undefined errors
#     project_name = "Unknown"
#     start_time = "N/A"
#     end_time = "N/A"
#     line_id_label = "N/A"
#     total_vehicle_count = 0
#     class_results = []
#     hourly_counts = []
#     daily_counts = []
#     weekly_counts = []
#     weekly_data = {}
#     class_names = []
#     peak_hours_per_day = {}
#     peak_day_of_week = {"weekday": "N/A", "count": 0}
#     peak_day_of_month = {"day": "N/A", "count": 0}

#     try:
#         # Session check
#         session_data, error_response = handle_session(request)
#         if error_response:
#             return RedirectResponse(url="/")

#         db = next(get_db())

#         # Detection info
#         detection_sql = text("""
#             SELECT d.start_time, d.end_time, d.line_id, p.project_name
#             FROM detection_log d
#             LEFT JOIN project p ON d.project_id = p.project_id
#             WHERE d.project_id = :project_id AND d.detection_id = :detect_id
#             LIMIT 1
#         """)
#         detection_info = db.execute(detection_sql, {"project_id": project_id, "detect_id": detect_id}).fetchone()
#         if detection_info:
#             project_name = detection_info.project_name or "Unknown"
#             start_time = detection_info.start_time.strftime("%Y-%m-%d %H:%M:%S") if detection_info.start_time else "N/A"
#             end_time = detection_info.end_time.strftime("%Y-%m-%d %H:%M:%S") if detection_info.end_time else "N/A"
#             line_id_map = {"line_id_1": "Up", "line_id_2": "Down", "line_id_3": "Both"}
#             line_id_label = line_id_map.get(str(detection_info.line_id), str(detection_info.line_id))

#         # Vehicle class counts
#         grouped_sql = text("""
#             SELECT vehicle_class_id, ai_class, COUNT(*) AS total
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY vehicle_class_id, ai_class
#             ORDER BY ai_class DESC
#         """)
#         grouped_results = db.execute(grouped_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         total_vehicle_count = sum(row.total for row in grouped_results)
#         for row in grouped_results:
#             percent = round((row.total / total_vehicle_count) * 100, 2) if total_vehicle_count else 0
#             class_results.append({"class_name": row.ai_class or "Unknown",
#                                   "vehicle_class_id": row.vehicle_class_id or 0,
#                                   "count": int(row.total or 0),
#                                   "percentage": percent})
#         class_names = list(set([row.ai_class for row in grouped_results if row.ai_class]))

#         # Hourly counts
#         hourly_sql = text("""
#             SELECT DATE(date_time) AS day,
#                    EXTRACT(HOUR FROM date_time) AS hour,
#                    COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY day, hour
#             ORDER BY day, hour
#         """)
#         hourly_rows = db.execute(hourly_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         for row in hourly_rows:
#             day_str = row.day.strftime("%Y-%m-%d") if row.day else "Unknown"
#             hour_val = int(row.hour) if row.hour is not None else 0
#             hourly_counts.append({"hour_label": f"{day_str} {hour_val:02d}:00", "count": int(row.count or 0)})

#         # Daily counts
#         daily_sql = text("""
#             SELECT DATE(date_time) AS day, COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY day
#             ORDER BY day
#         """)
#         daily_rows = db.execute(daily_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         for row in daily_rows:
#             day_str = row.day.strftime("%Y-%m-%d") if row.day else "Unknown"
#             daily_counts.append({"day_label": day_str, "count": int(row.count or 0)})

#         # Weekly counts
#         weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
#         weekly_sql = text("""
#             SELECT EXTRACT(DOW FROM date_time) AS weekday,
#                    COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY weekday ORDER BY weekday
#         """)
#         weekly_rows = db.execute(weekly_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         for row in weekly_rows:
#             weekly_counts.append({"weekday_label": weekdays[int(row.weekday)], "count": int(row.count or 0)})

#         # Weekly class data
#         weekly_class_sql = text("""
#             SELECT EXTRACT(DOW FROM date_time) AS weekday, ai_class, COUNT(*) AS total
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY weekday, ai_class
#             ORDER BY weekday, ai_class
#         """)
#         weekly_class_results = db.execute(weekly_class_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         weekly_data = {cls: [0]*7 for cls in class_names}
#         for row in weekly_class_results:
#             cls = row.ai_class or "Unknown"
#             day = int(row.weekday)
#             weekly_data[cls][day] = int(row.total or 0)

#         # Peak hour per day
#         peak_hour_sql = text("""
#             SELECT DATE(date_time) AS day,
#                    EXTRACT(HOUR FROM date_time) AS hour,
#                    COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY day, hour
#         """)
#         peak_hour_data = db.execute(peak_hour_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         peak_hours_per_day = {}
#         for row in peak_hour_data:
#             day_str = row.day.strftime("%Y-%m-%d")
#             hour = int(row.hour)
#             count = int(row.count)
#             if day_str not in peak_hours_per_day or count > peak_hours_per_day[day_str]["count"]:
#                 peak_hours_per_day[day_str] = {"hour": f"{hour:02d}:00", "count": count}

#         # Peak day of week
#         peak_day_week_sql = text("""
#             SELECT EXTRACT(DOW FROM date_time) AS weekday,
#                    COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY weekday
#         """)
#         week_rows = db.execute(peak_day_week_sql, {"project_id": project_id, "detect_id": detect_id}).fetchall()
#         for row in week_rows:
#             day_label = weekdays[int(row.weekday)]
#             count = int(row.count)
#             if count > peak_day_of_week["count"]:
#                 peak_day_of_week = {"weekday": day_label, "count": count}

#         # Peak day of month
#         peak_day_month_sql = text("""
#             SELECT DATE(date_time) AS day, COUNT(*) AS count
#             FROM kit1_objectdetection
#             WHERE project_id = :project_id AND detection_id = :detect_id
#             GROUP BY day
#             ORDER BY count DESC
#             LIMIT 1
#         """)
#         peak_day_month_row = db.execute(peak_day_month_sql, {"project_id": project_id, "detect_id": detect_id}).fetchone()
#         if peak_day_month_row:
#             peak_day_of_month = {"day": peak_day_month_row.day.strftime("%Y-%m-%d"), "count": int(peak_day_month_row.count)}

#         # Return template
#         return templates.TemplateResponse("report_monitor.html", {
#             "request": request,
#             "session": session_data,
#             "project_name": project_name,
#             "start_time": start_time,
#             "end_time": end_time,
#             "line_id": line_id_label,
#             "detection_id": detect_id,
#             "total_vehicle_count": total_vehicle_count,
#             "class_results": class_results,
#             "hourly_counts": hourly_counts,
#             "daily_counts": daily_counts,
#             "weekly_counts": weekly_counts,
#             "weekly_data": weekly_data,
#             "class_names": class_names,
#             "peak_hours_per_day": peak_hours_per_day,
#             "peak_day_of_week": peak_day_of_week,
#             "peak_day_of_month": peak_day_of_month
#         })

#     except Exception as e:
#         print("Error in report_monitor:", e)
#         return templates.TemplateResponse("report_monitor.html", {
#             "request": request,
#             "session": {},
#             "project_name": project_name,
#             "start_time": start_time,
#             "end_time": end_time,
#             "line_id": line_id_label,
#             "detection_id": detect_id,
#             "total_vehicle_count": total_vehicle_count,
#             "class_results": class_results,
#             "hourly_counts": hourly_counts,
#             "daily_counts": daily_counts,
#             "weekly_counts": weekly_counts,
#             "weekly_data": weekly_data,
#             "class_names": class_names,
#             "peak_hours_per_day": peak_hours_per_day,
#             "peak_day_of_week": peak_day_of_week,
#             "peak_day_of_month": peak_day_of_month
#         })

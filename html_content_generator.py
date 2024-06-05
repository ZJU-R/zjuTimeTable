import json
from jinja2 import Template

from typing import List, Any, Tuple, Dict
import sys

from easyEta import etaOperator
import os

template_file_path = os.path.join(os.path.dirname(__file__), "templates/course_arrangement.html")
with open(template_file_path, "r", encoding="utf-8") as f:
    template_str = f.read()
template = Template(template_str)


def get_course_arrangement_data(school_number: str, password: str, semester: str, also_fetch_zdbk: bool = False) -> Tuple[Dict[str, Any], str, List[str]]:
    
    ess = etaOperator(school_number, password, also_fetch_zdbk)
    try:
        user_name = ess.get_name()
        if user_name in ["", None]:
            raise ValueError("学号或密码错误")
    except:
        raise ValueError("学号或密码错误")
    data = ess.get_course_arrangement(school_number, semester).get("data", {})
    if also_fetch_zdbk:
        courses_from_graduation_requirements = ess.get_courses_from_graduation_requirements(school_number)
        ongoing_course_names = [x.get("KCMC", "") for x in courses_from_graduation_requirements if x.get("status", "") == "在修"]
    else:
        ongoing_course_names = []
    title = f"{user_name} 的课程表" if user_name else "课程表"
    return data, title, ongoing_course_names

def get_html_content(data: Dict[str, Any], title: str, ongoing_courses: List[str]) -> str:
    
    next_semester_courses = []
    # 预处理数据，按照 course 组织
    courses = []
    dxq_courses = [x.get("SJKCMC", "") for x in data.get("sjkc", [])]
    for day, courses_list in data["kbList"].items():
        for course in courses_list:
            course_info = {
                "day": int(day),
                "semester": course["xxq"],
                "start_time": course["ksj"],
                "duration": course["ks"],
                "end_time": course["ksj"] + course["ks"] - 1,
                "selected": course["sfqd"],
                "single_double_week": course["dsz"],
                "kes": []
            }
            for index, ke in enumerate(course["ke"]):
                ke_info = ke
                if "|" in ke["sksj"]:
                    ke_info["sksj"] = ke["sksj"].split("|")[0] + "}"
                ke_info["index"] = index
                ke_info["selected"] = course["sfqd"]
                ke_info["single_double_week"] = course["dsz"]
                ke_info["start_time"] = course_info["start_time"]
                ke_info["end_time"] = course_info["start_time"] + course_info["duration"] - 1
                ke_info["period_description"] = f"{ke_info['start_time']}-{ke_info['end_time']}节"
                course_info["kes"].append(ke_info)
                if ke["kcmc"] in ongoing_courses:
                    next_semester_courses.append(ke["kcmc"])
            courses.append(course_info)

    # 冲突检测和合并单周/双周到 all，以及时间包含关系
    merged_courses = []
    course_dict = {}

    for course in courses:
        key = (course["day"], course["start_time"], course["end_time"], course["single_double_week"])
        if key in course_dict:
            if course["single_double_week"] == "all":
                course_dict[key]["kes"].extend(course["kes"])
            else:
                if course_dict[key]["single_double_week"] == "all":
                    course_dict[key]["kes"].extend(course["kes"])
                else:
                    course_dict[key] = course
        else:
            to_merge = False
            for existing_key, existing_course in list(course_dict.items()):
                existing_day, existing_start, existing_end, existing_single_double_week = existing_key
                if existing_day == course["day"]:
                    if existing_start <= course["start_time"] and existing_end >= course["end_time"]:
                        course_dict[existing_key]["kes"].extend(course["kes"])
                        to_merge = True
                        break
                    elif course["start_time"] <= existing_start and course["end_time"] >= existing_end:
                        course["kes"].extend(existing_course["kes"])
                        del course_dict[existing_key]
            if not to_merge:
                course_dict[key] = course

    merged_courses = list(course_dict.values())



    for course in merged_courses:
        unique_name_dict = {}
        for ke in course["kes"]:
            if ke["kcmc"] in unique_name_dict:
                already_ke = unique_name_dict[ke["kcmc"]]
                already_ke["sksj"] += "、" + ke["sksj"]
                already_ke["period_description"] += "、" + ke["period_description"]
                already_ke["rkjs"] += "、" + ke["rkjs"]
                already_ke["jsmc"] += "、" + ke["jsmc"]
            else:
                unique_name_dict[ke["kcmc"]] = ke
        course["kes"] = list(unique_name_dict.values())
        course["has_multiple_kes"] = len(course["kes"]) > 1


    # 构建字典记录哪些时间段和天数没有课程
    no_course_slots = {(day, period): True for day in range(1, 8) for period in range(1, 14)}

    for course in merged_courses:
        for i in range(course["duration"]):
            no_course_slots[(course["day"], course["start_time"] + i)] = False

    next_semester_courses = list(set(next_semester_courses))
    if len(next_semester_courses) == 0:
        next_semester_courses = None
    # Jinja2 模板
    global template
    # 渲染模板
    html_content = template.render(courses=merged_courses, no_course_slots=no_course_slots, title=title, table_title=title, dxq_courses = dxq_courses, ongoing_courses = next_semester_courses)
    return html_content

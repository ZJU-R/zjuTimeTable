
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
import os
import webbrowser
import uvicorn
from itsdangerous import URLSafeTimedSerializer, BadSignature
from html_content_generator import get_course_arrangement_data, get_html_content
import logging

logging.basicConfig(level=logging.INFO)


login_template_str = ""
login_html_path = os.path.join(os.path.dirname(__file__), "templates/login.html")
with open(login_html_path, "r", encoding="utf-8") as f:
    login_template_str = f.read()
login_template = login_template_str

# Secret key for session management
SECRET_KEY = "your_secret_key"
serializer = URLSafeTimedSerializer(SECRET_KEY)

app = FastAPI()

def get_html_content_from_session(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return "", "No session data"

    try:
        user_data = serializer.loads(session_token)
    except BadSignature:
        return "", "Invalid session data"

    school_number = user_data["school_number"]
    password = user_data["password"]
    semester_full = user_data["semester_full"]
    also_fetch_zdbk = user_data["also_fetch_zdbk"]
    try:
        data, title, ongoing_courses = get_course_arrangement_data(school_number, password, semester_full, also_fetch_zdbk)
        html_content = get_html_content(data, title, ongoing_courses)
    except Exception as e:
        logging.error(f"Error: {e}")
        return "发生错误：请检查账号与密码、是否在校园内网", "Error"
    return html_content, title

@app.get("/", response_class=HTMLResponse)
async def show_login():
    return login_template

@app.post("/login", response_class=HTMLResponse)
async def login(school_number: str = Form(...), password: str = Form(...), year: str = Form(...), semester: str = Form(...), also_fetch_zdbk: bool = Form(False)):
    semester_full = f"{year}-{semester}"
    user_data = {
        "school_number": school_number,
        "password": password,
        "semester_full": semester_full,
        "also_fetch_zdbk": also_fetch_zdbk
    }
    session_token = serializer.dumps(user_data)
    response = RedirectResponse(url="/courses", status_code=302)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@app.get("/courses", response_class=HTMLResponse)
async def show_courses(request: Request):
    html_content, title = get_html_content_from_session(request)
    if not html_content:
        return RedirectResponse(url="/")

    return HTMLResponse(content=html_content)

# import json
# test_data = None
# with open("tmp\course_arrangement.json", "r", encoding="utf-8") as f:
#     test_data = json.load(f)
# title = "test data"
# test_html_content = get_html_content(test_data, title)

# @app.get("/test_m", response_class=HTMLResponse)
# async def show_test_m():
#     return test_html_content

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7866)
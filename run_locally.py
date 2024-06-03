import uvicorn

port = 7866
url = f"http://127.0.0.1:{port}"

import webbrowser
webbrowser.open(url)

if __name__ == "__main__":
    uvicorn.run("course_arrangement_fastapi:app", host="127.0.0.1", port=port)
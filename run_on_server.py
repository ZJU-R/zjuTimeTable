import uvicorn

max_workers = 10
port = 80 # or 443 if you have a SSL certificate

if __name__ == "__main__":
    uvicorn.run("course_arrangement_fastapi:app", host="0.0.0.0", port=port, workers=max_workers)
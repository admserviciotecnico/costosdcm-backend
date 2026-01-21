from .main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend_costeo.main:app", host="0.0.0.0", port=8001, reload=True)

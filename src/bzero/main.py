import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
def check_health():
    return {"status": "ok"}


def dev():
    """개발 서버 실행"""
    uvicorn.run(
        "bzero.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

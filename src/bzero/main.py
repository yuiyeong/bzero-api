import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bzero.core.config import settings

app = FastAPI()

# ======================
# CORS 설정
# ======================
# Cross-Origin Resource Sharing (CORS) 미들웨어 설정
# 프론트엔드에서 백엔드 API에 접근할 수 있도록 허용합니다.
#
# 개발 환경: http://localhost:5173 (Vite 개발 서버)
# 배포 환경: https://app.basementzero.cloud (Cloudflare Pages)
#
# 환경별 설정 방법:
# - 개발: CORS_ORIGINS="http://localhost:5173"
# - 배포: CORS_ORIGINS="https://app.basementzero.cloud"
# - 다중 출처: CORS_ORIGINS="http://localhost:5173,https://app.basementzero.cloud"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # 허용할 출처(origin) 리스트
    allow_credentials=settings.cors_allow_credentials,  # 쿠키 등 자격증명 허용
    allow_methods=settings.get_cors_allow_methods(),  # 허용할 HTTP 메서드
    allow_headers=settings.get_cors_allow_headers(),  # 허용할 HTTP 헤더
)


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

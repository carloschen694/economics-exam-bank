from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .api.router import api_router
from .config import settings
from .database import create_db_and_tables
# Import models to ensure SQLModel registers table schemas before creating tables
from . import models  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 啟動時自動初始化資料表
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="專門提供台灣與海外經濟學研究所考古題庫檢索、題組測驗與練習之後端 API 服務。",
    lifespan=lifespan,
    docs_url=None,  # 自訂 /docs 使用穩定的 cdnjs CDN
    redoc_url="/redoc",
)


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    from fastapi.openapi.docs import get_swagger_ui_html

    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.min.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.11.0/swagger-ui.min.css",
    )

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 掛載靜態網頁驗收介面
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/web", include_in_schema=False)
@app.get("/app", include_in_schema=False)
def web_ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/", tags=["Root"])
def root():
    return FileResponse(STATIC_DIR / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run("economics_exam_bank.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()

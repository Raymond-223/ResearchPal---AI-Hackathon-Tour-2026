"""
学术写作风格迁移模块 - 主入口
可作为独立服务运行，也可被主后端集成
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="学术写作风格迁移服务",
        description="提供文本分析、风格评分、语法检查、风格迁移、版本对比等功能",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS（允许Gradio前端调用）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router)
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "writing_style_transfer"}
    
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

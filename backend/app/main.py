"""WorkShop 应用入口：装配 API、工具路由与前端静态资源。"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core import config
from app.core.registry import discover


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{config.APP_NAME} API",
        version=config.APP_VERSION,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    tools, routers = discover()
    app.state.tools = tools
    for router in routers:
        app.include_router(router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "app": config.APP_NAME,
            "version": config.APP_VERSION,
            "packaged": config.is_frozen(),
            "backendTools": [t.id for t in tools],
        }

    @app.get("/api/tools")
    def list_tools():
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "version": t.version,
            }
            for t in tools
        ]

    @app.post("/api/shutdown")
    def shutdown(request: Request):
        # 仅打包版允许从页面退出服务，开发模式下忽略
        server = getattr(request.app.state, "server", None)
        if not config.is_frozen() or server is None:
            raise HTTPException(403, detail="仅打包模式下允许远程退出")
        import threading

        threading.Timer(0.2, setattr, args=(server, "should_exit", True)).start()
        return {"status": "stopping"}

    static = config.static_dir()
    if (static / "index.html").exists():
        assets = static / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa(full_path: str):
            candidate = (static / full_path).resolve()
            # 防目录穿越：只允许 static 目录内的真实文件，其余回退到 SPA 入口
            if full_path and candidate.is_file() and static.resolve() in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(static / "index.html")

    return app

"""WorkShop 启动器：启动本地服务并自动打开浏览器。

开发模式:  python run.py
打包模式:  WorkShop.exe（PyInstaller 入口指向本文件）
"""
import os
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from app.core import config
from app.main import create_app


def guard_noconsole() -> bool:
    """--noconsole 打包后双击运行时没有控制台，sys.stdout / sys.stderr 为 None，
    uvicorn 的日志格式化器会调用 sys.stdout.isatty() 而崩溃。
    这里把它们替换为空设备，并告知调用方跳过日志配置。"""
    if sys.stdout is not None and sys.stderr is not None:
        return False
    devnull = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = devnull
    if sys.stderr is None:
        sys.stderr = devnull
    return True


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def open_browser(url: str) -> None:
    if not os.environ.get("WORKSHOP_NO_BROWSER"):
        threading.Timer(0.3, webbrowser.open, args=(url,)).start()


def close_splash() -> None:
    """关闭 PyInstaller --splash 占位窗（服务已就绪，浏览器页面即将接管）。"""
    if not config.is_frozen():
        return
    try:
        import pyi_splash  # 仅打包产物中存在

        pyi_splash.close()
    except Exception:
        pass


def main() -> None:
    no_console = guard_noconsole()
    port = config.default_port()
    url = f"http://127.0.0.1:{port}"

    if port_in_use(port):
        print(f"端口 {port} 已被占用，可能已有 WorkShop 在运行，直接打开页面。")
        close_splash()
        open_browser(url)
        return

    app = create_app()
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
            # 无控制台时跳过 uvicorn 自带的 dictConfig，彻底避开日志格式化器
            log_config=None if no_console else uvicorn.config.LOGGING_CONFIG,
        )
    )
    app.state.server = server

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 15
    while not server.started and time.time() < deadline:
        time.sleep(0.05)

    if server.started:
        mode = "打包版" if config.is_frozen() else "开发模式"
        print(f"{config.APP_NAME} 已启动（{mode}）: {url}")
        print("关闭本窗口或按 Ctrl+C 即可退出服务。")
        close_splash()
        open_browser(url)
    else:
        print("服务启动失败，请检查端口是否被占用。")
        close_splash()
        return

    try:
        thread.join()
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(timeout=5)
    print("WorkShop 已退出。")


if __name__ == "__main__":
    main()

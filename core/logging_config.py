"""
日志配置：统一根日志器，避免重复添加 handler。

仅在根日志器没有任何 handler 时添加 StreamHandler，并设置根级别为 INFO，
避免被多个模块反复调用时产生重复日志输出。
"""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """配置根日志器。

    仅当根日志器没有任何 handler 时才添加 StreamHandler，避免重复添加；
    同时将根日志级别设为 ``level``（默认 INFO）。
    """
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)

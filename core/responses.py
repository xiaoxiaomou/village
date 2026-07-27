"""
统一响应与全局错误处理。

错误 JSON 信封与现有代码保持一致：``{"msg": "<message>"}``。
全局错误处理器只影响「未匹配路由 / 未捕获异常」，不会改变路由内部显式返回。
"""

import logging

from flask import jsonify, request

logger = logging.getLogger(__name__)


def api_error(message: str, code: int = 400):
    """返回统一错误 JSON 信封 ``{"msg": message}`` 与对应状态码。"""
    return jsonify({"msg": message}), code


def register_error_handlers(app) -> None:
    """注册全局错误处理器（仅影响未匹配/未捕获错误）。"""

    @app.errorhandler(500)
    def handle_500(error):
        logger.exception("服务器内部错误: %s", error)
        if request.path.startswith("/api"):
            return api_error("服务器内部错误", 500)
        return (
            "<html><head><title>500 服务器错误</title></head><body>"
            "<h1>500 服务器内部错误</h1>"
            "<p>服务器遇到问题，请稍后再试。</p>"
            '<p><a href="/">返回首页</a></p></body></html>',
            500,
        )

    @app.errorhandler(404)
    def handle_404(error):
        if request.path.startswith("/api"):
            return api_error("资源不存在", 404)
        return (
            "<html><head><title>404 页面不存在</title></head><body>"
            "<h1>404 页面不存在</h1>"
            "<p>您访问的页面不存在或已被移动。</p>"
            '<p><a href="/">返回首页</a></p></body></html>',
            404,
        )

    @app.errorhandler(413)
    def handle_413(error):
        if request.path.startswith("/api"):
            return api_error("上传文件过大", 413)
        return (
            "<html><head><title>413 上传文件过大</title></head><body>"
            "<h1>413 上传文件过大</h1>"
            '<p><a href="/">返回首页</a></p></body></html>',
            413,
        )

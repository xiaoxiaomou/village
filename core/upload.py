"""
文件上传工具：统一落盘与访问 URL 生成，供多个蓝图复用。

成功返回字典::

    {"ok": True, "filename": <唯一文件名>, "url": <访问URL>, "size": <字节数|None>}

校验失败返回字典::

    {"ok": False, "error": "<中文错误>", "code": <400|413>}
"""

import os
import uuid
from typing import Optional

from werkzeug.utils import secure_filename


def save_uploaded_file(
    file,
    *,
    upload_folder: str,
    url_prefix: str,
    subfolder: str = "",
    allowed_exts: set,
    max_size: int = None,
) -> dict:
    """保存上传文件到磁盘并返回访问信息。

    Args:
        file: Werkzeug ``FileStorage`` 对象。
        upload_folder: 上传根目录（绝对或相对路径）。
        url_prefix: URL 前缀，例如 ``/download`` 或 ``/uploads``。
        subfolder: 子目录（例如 ``images`` / ``videos``），可为空字符串。
        allowed_exts: 允许的扩展名集合（小写，不含点）。
        max_size: 最大字节数；为 ``None`` 表示不限制大小。

    Returns:
        成功: ``{"ok": True, "filename": ..., "url": ..., "size": ...}``
        失败: ``{"ok": False, "error": ..., "code": ...}``
    """
    # 校验文件对象
    if file is None or not hasattr(file, "filename"):
        return {"ok": False, "error": "没有文件", "code": 400}
    original_name = file.filename or ""
    if original_name == "":
        return {"ok": False, "error": "没有选择文件", "code": 400}

    filename = secure_filename(original_name)
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if ext == "" or ext not in allowed_exts:
        return {"ok": False, "error": "不支持的文件类型", "code": 400}

    # 校验大小（仅当给定 max_size 时）
    size: Optional[int] = None
    if max_size is not None:
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > max_size:
            return {"ok": False, "error": "上传文件过大", "code": 413}

    unique = f"{uuid.uuid4().hex}.{ext}"

    # 组装保存目录并落盘
    if subfolder:
        dest_dir = os.path.join(upload_folder, subfolder)
        os.makedirs(dest_dir, exist_ok=True)
    else:
        dest_dir = upload_folder
    file.save(os.path.join(dest_dir, unique))

    # 组装访问 URL
    url = f"{url_prefix}/{subfolder}/{unique}" if subfolder else f"{url_prefix}/{unique}"

    return {"ok": True, "filename": unique, "url": url, "size": size}

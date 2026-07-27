"""
序列化工具：日期格式转换与分页字典构造。
"""

from typing import Any, List, Optional


def to_iso(dt: Any) -> Optional[str]:
    """将 datetime 转为 ISO 8601 字符串；为空（None/空字符串）时返回 None。"""
    return dt.isoformat() if dt else None


def paginate_to_dict(
    items: List[Any], pagination: Any, items_key: str = "data"
) -> dict:
    """将分页结果与条目列表构造为统一的 JSON 字典。

    Args:
        items: 已构造好的条目列表（每个元素是 dict）。
        pagination: SQLAlchemy ``Pagination`` 对象。
        items_key: 列表字段名，默认 ``data``。

    Returns:
        ``{items_key: items, "pagination": {page, per_page, total, pages}}``
    """
    return {
        items_key: items,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }

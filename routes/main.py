"""
主蓝图：公共页面路由
首页、新闻、村情、政务、服务、留言、联系我们
全部使用 SQLAlchemy ORM 访问数据库
"""

from flask import (
    Blueprint,
    request,
    session,
    render_template,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
)
from models import (
    db,
    News,
    Category,
    VillageInfo,
    Government,
    Service,
    Message,
    SiteContact,
    HomeFeature,
    VillageCarousel,
)
from datetime import datetime
import logging

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/")
def index():
    try:
        features = (
            HomeFeature.query.filter_by(is_active=True)
            .order_by(HomeFeature.sort_order, HomeFeature.id)
            .all()
        )
        carousel = (
            VillageCarousel.query.filter_by(is_active=True)
            .order_by(VillageCarousel.sort_order, VillageCarousel.id)
            .all()
        )
        return render_template("index.html", features=features, carousels=carousel)
    except Exception:
        return render_template("base.html")


# ─── 新闻动态 ───


@main_bp.route("/news")
def news_page():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)
    category_id = request.args.get("category_id", type=int)

    query = News.query.order_by(News.create_time.desc())
    if search:
        query = query.filter(
            db.or_(News.title.contains(search), News.content.contains(search))
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    # 构建 category_id -> name 映射
    cat_map = {c.id: c.name for c in Category.query.all()}
    news_data = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "date": str(n.create_time) if n.create_time else "",
            "author": n.author,
            "category_id": n.category_id,
            "category_name": cat_map.get(n.category_id, ""),
        }
        for n in pagination.items
    ]

    categories = Category.query.all()
    return render_template(
        "news.html",
        news_list=news_data,
        page=page,
        total_pages=pagination.pages,
        search=search,
        category_id=category_id,
        categories=categories,
    )


# ─── 新闻详情 ───


@main_bp.route("/news/<int:news_id>")
def news_detail(news_id):
    news = News.query.get(news_id)
    if not news:
        return render_template("base.html"), 404

    # 增加访问量
    try:
        db.session.execute(
            db.text(
                "UPDATE news SET view_count = COALESCE(view_count, 0) + 1 WHERE id=:id"
            ),
            {"id": news_id},
        )
        db.session.commit()
    except Exception:
        pass

    news_data = {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "author": news.author,
        "category_id": news.category_id,
        "image_url": news.image_url,
        "view_count": news.view_count or 0,
        "create_time": news.create_time.strftime("%Y-%m-%d %H:%M")
        if news.create_time
        else None,
        "category": news.category.name if news.category else None,
    }

    return render_template("news_detail.html", news=news_data)


# ─── 乡村概况 ───


@main_bp.route("/village")
def village_page():
    info = VillageInfo.query.order_by(VillageInfo.id.desc()).first()
    village_info = (
        {
            "id": info.id,
            "title": info.title,
            "content": info.content,
            "image_url": info.image_url,
        }
        if info
        else None
    )
    return render_template("village.html", village_info=village_info)


# ─── 政务公开 ───


@main_bp.route("/government")
def government_page():
    govs = Government.query.order_by(Government.id.desc()).all()
    government_list = [
        {
            "id": g.id,
            "title": g.title,
            "content": g.content,
            "file_url": g.file_url,
        }
        for g in govs
    ]
    return render_template("government.html", government_list=government_list)


@main_bp.route("/government/<int:gov_id>")
def government_detail(gov_id):
    """政务详情页面"""
    gov = Government.query.get(gov_id)
    if not gov:
        abort(404)
    return render_template("government_detail.html", government=gov)


# ─── 便民服务 ───


@main_bp.route("/services")
def services_page():
    return render_template("services.html")


@main_bp.route("/services/<int:service_id>")
def service_detail(service_id):
    """服务详情页面"""
    svc = Service.query.get(service_id)
    if not svc:
        abort(404)
    return render_template("service_detail.html", service=svc)


# ─── 互动交流（留言板） ───


@main_bp.route("/message", methods=["GET", "POST"])
def message_page():
    try:
        if request.method == "POST":
            if "user" not in session:
                flash("请先登录后再提交留言")
                return redirect(url_for("auth.login"))
            name = request.form.get("name", "").strip()
            contact = request.form.get("contact", "").strip()
            content = request.form.get("content", "").strip()
            if not name or not content:
                flash("姓名和留言内容不能为空")
                return redirect(url_for("main.message_page"))
            if len(content) > 1000:
                flash("留言内容不能超过1000个字符")
                return redirect(url_for("main.message_page"))
            try:
                msg = Message(name=name, contact=contact, content=content)
                db.session.add(msg)
                db.session.commit()
                flash("留言提交成功，我们会尽快回复您！")
            except Exception as e:
                db.session.rollback()
                flash("留言提交失败，请稍后再试")
                logger.error(f"留言提交失败: {e}")
            return redirect(url_for("main.message_page"))

        messages = []
        try:
            msgs = Message.query.order_by(Message.create_time.desc()).limit(50).all()
            messages = [
                {
                    "id": m.id,
                    "name": m.name,
                    "contact": m.contact,
                    "content": m.content,
                    "reply": m.reply,
                    "create_time": str(m.create_time) if m.create_time else "",
                }
                for m in msgs
            ]
        except Exception as e:
            logger.error(f"获取留言失败: {e}")
            messages = []

        try:
            return render_template("message_simple.html", messages=messages)
        except Exception as template_error:
            logger.error(f"模板渲染失败: {template_error}")
            return f"""<html><head><title>互动交流</title></head><body>
                <h1>互动交流</h1><p>页面正在维护中...</p>
                <p>留言数量: {len(messages)}</p>
                <p><a href="/">返回首页</a></p></body></html>"""

    except Exception as e:
        logger.error(f"message_page 错误: {e}")
        return (
            f"""<html><head><title>页面错误</title></head><body>
            <h1>页面暂时无法访问</h1><p>错误信息: {str(e)}</p>
            <p><a href="/">返回首页</a></p></body></html>""",
            500,
        )


# ─── 联系我们 ───


@main_bp.route("/contact")
def contact_page():
    contact = SiteContact.query.first()
    return render_template("contact.html", contact=contact)


# ─── 测试 ───


@main_bp.route("/test")
def test_page():
    """健康检查端点"""
    return "<h2>乡村记忆系统运行正常</h2><p><a href='/'>返回首页</a></p>"


@main_bp.route("/message-test")
def message_test_page():
    try:
        try:
            msgs = Message.query.order_by(Message.create_time.desc()).limit(10).all()
            messages = [
                {
                    "name": m.name,
                    "content": m.content,
                    "create_time": str(m.create_time) if m.create_time else "",
                    "reply": m.reply,
                }
                for m in msgs
            ]
        except Exception as e:
            messages = [
                {
                    "name": "测试用户",
                    "content": f"数据库连接测试失败: {str(e)}",
                    "create_time": "2024-01-01",
                    "reply": None,
                }
            ]
        return render_template("message_simple.html", messages=messages)
    except Exception as e:
        return f"页面错误: {str(e)}", 500


# ─── 文件服务 ───


@main_bp.route("/download/<filename>")
def download_file(filename):
    from flask import current_app

    try:
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True
        )
    except FileNotFoundError:
        abort(404)


@main_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import current_app

    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# 安全说明：出于安全考虑，不再提供「项目根目录」万能文件下载路由。
# 该路由会把 village.db、源码、cookies.txt 等任意文件暴露给未登录用户。
# 如需提供静态测试页，请显式新增一条指向固定白名单目录的路由。

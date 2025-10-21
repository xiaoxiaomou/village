import flask
from flask import Flask, jsonify, send_from_directory, request, session, render_template, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from models import db, User, Category, News, Service, Government, VillageInfo, Message, Reply, VillageLogo, VillageCarousel
import os
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'

# 使用MySQL数据库配置
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT
password = quote_plus(str(MYSQL_PASSWORD))
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,  # 连接在池中的最大生存时间（秒）
    'pool_timeout': 20,   # 获取连接的超时时间
    'pool_size': 10,      # 连接池大小
    'max_overflow': 5,    # 最大溢出连接数
    'connect_args': {
        'connect_timeout': 10,  # 连接超时时间
    }
}
#sk-532ca88475a14ae1b3fd767936517165
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
db.init_app(app)
CORS(app)

# 添加数据库连接健康检查
@app.before_request
def db_connection_check():
    # 如果不是静态资源请求，检查数据库连接
    if not request.path.startswith('/static/'):
        try:
            # 执行一个简单查询来保持连接活跃
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            app.logger.error(f"数据库连接检查失败: {e}")
            db.session.rollback()

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"msg": "未登录"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 管理员验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"msg": "未登录"}), 401
        if session.get('role') != 'admin':
            return jsonify({"msg": "无权限"}), 403
        return f(*args, **kwargs)
    return decorated_function

# 在应用程序关闭时关闭数据库连接
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def index():
    # 优先渲染 index.html，如无则渲染 base.html
    try:
        return render_template('index.html')
    except Exception:
        return render_template('base.html')

@app.route('/news')
def news_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, create_time as date FROM news ORDER BY create_time DESC LIMIT 20")
    news_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('news.html', news_list=news_list)

@app.route('/village')
def village_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, image_url FROM village_info ORDER BY id DESC LIMIT 1")
    village_info = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('village.html', village_info=village_info)

@app.route('/government')
def government_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, file_url FROM government ORDER BY id DESC")
    government_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('government.html', government_list=government_list)

@app.route('/services')
def services_page():
    return render_template('services.html')

@app.route('/message', methods=['GET', 'POST'])
def message_page():
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            contact = request.form.get('contact', '').strip()
            content = request.form.get('content', '').strip()
            
            if not name or not content:
                flash('姓名和留言内容不能为空')
                return redirect(url_for('message_page'))
            
            if len(content) > 1000:
                flash('留言内容不能超过1000个字符')
                return redirect(url_for('message_page'))
            
            try:
                # 使用原生SQL插入留言（支持匿名留言）
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (name, contact, content, create_time) VALUES (%s, %s, %s, NOW())",
                    (name, contact, content)
                )
                conn.commit()
                cursor.close()
                conn.close()
                flash('留言提交成功，我们会尽快回复您！')
            except Exception as e:
                flash('留言提交失败，请稍后再试')
                app.logger.error(f"留言提交失败: {e}")
            
            return redirect(url_for('message_page'))
        
        # 获取所有留言及回复
        messages = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, contact, content, reply, create_time 
                FROM messages 
                ORDER BY create_time DESC 
                LIMIT 50
            """)
            messages = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            app.logger.error(f"获取留言失败: {e}")
            # 如果数据库查询失败，使用空列表
            messages = []
        
        # 先尝试使用简化模板
        try:
            return render_template('message_simple.html', messages=messages)
        except Exception as template_error:
            app.logger.error(f"模板渲染失败: {template_error}")
            # 如果模板也失败，返回纯HTML
            return f"""
            <html>
            <head><title>互动交流</title></head>
            <body>
                <h1>互动交流</h1>
                <p>页面正在维护中...</p>
                <p>留言数量: {len(messages)}</p>
                <p><a href="/">返回首页</a></p>
            </body>
            </html>
            """
        
    except Exception as e:
        app.logger.error(f"message_page 错误: {e}")
        # 返回一个简单的错误页面
        return f"""
        <html>
        <head><title>页面错误</title></head>
        <body>
            <h1>页面暂时无法访问</h1>
            <p>错误信息: {str(e)}</p>
            <p><a href="/">返回首页</a></p>
        </body>
        </html>
        """, 500

@app.route('/contact')
def contact_page():
    """联系我们页面"""
    return render_template('contact.html')

@app.route('/test')
def test_page():
    """测试页面"""
    return send_from_directory('.', 'test_pages.html')

@app.route('/message-test', methods=['GET', 'POST'])
def message_test_page():
    """简化版留言页面用于测试"""
    try:
        messages = []
        if request.method == 'POST':
            return "表单提交测试成功！"
        
        # 尝试获取留言数据
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, contact, content, reply, create_time FROM messages ORDER BY create_time DESC LIMIT 10")
            messages = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            messages = [{'name': '测试用户', 'content': f'数据库连接测试失败: {str(e)}', 'create_time': '2024-01-01', 'reply': None}]
        
        return render_template('message_simple.html', messages=messages)
    except Exception as e:
        return f"页面错误: {str(e)}", 500

# 添加静态文件路由
@app.route('/static/<path:filename>')
def serve_static_file(filename):
    return send_from_directory('static', filename)

def get_db_connection():
    import pymysql
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/api/news')
def get_news():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category_id', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建查询条件
    where_conditions = []
    params = []
    
    if search:
        where_conditions.append("(title LIKE %s OR content LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    if category_id:
        where_conditions.append("category_id = %s")
        params.append(category_id)
    
    where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # 获取总数
    count_sql = f"SELECT COUNT(*) FROM news{where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['COUNT(*)']
    
    # 获取分页数据
    offset = (page - 1) * per_page
    data_sql = f"SELECT id, title, content, create_time, author, category_id FROM news{where_clause} ORDER BY create_time DESC LIMIT %s OFFSET %s"
    cursor.execute(data_sql, params + [per_page, offset])
    news = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "data": news,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })

@app.route('/api/news/<int:news_id>')
def get_news_detail(news_id):
    """获取新闻详情并增加访问量"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取新闻详情
    cursor.execute("SELECT * FROM news WHERE id=%s", (news_id,))
    news = cursor.fetchone()
    
    if not news:
        cursor.close()
        conn.close()
        return jsonify({"msg": "新闻不存在"}), 404
    
    # 增加访问量（如果表中有view_count字段）
    try:
        cursor.execute("UPDATE news SET view_count = COALESCE(view_count, 0) + 1 WHERE id=%s", (news_id,))
        conn.commit()
    except:
        # 如果没有view_count字段，忽略错误
        pass
    
    cursor.close()
    conn.close()
    
    return jsonify(news)

@app.route('/api/services')
def get_services():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM services ORDER BY id DESC")
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    return flask.jsonify(services)

@app.route('/api/village')
def get_village_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, image_url FROM village_info ORDER BY id DESC LIMIT 1")
    info = cursor.fetchone()
    cursor.close()
    conn.close()
    return flask.jsonify(info)

@app.route('/api/government')
def get_government_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, file_url FROM government ORDER BY id DESC")
    government = cursor.fetchall()
    cursor.close()
    conn.close()
    return flask.jsonify(government)

@app.route('/api/messages', methods=['GET', 'POST'])
def messages():
    if flask.request.method == 'POST':
        data = flask.request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (name, content, create_time) VALUES (%s, %s, NOW())", (data.get('name'), data.get('content')))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({"msg": "留言提交成功", "data": data}), 201
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, content, reply, create_time FROM messages ORDER BY create_time DESC")
        msgs = cursor.fetchall()
        cursor.close()
        conn.close()
        return flask.jsonify(msgs)

# ------------------- 后台管理接口 -------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理后台主页"""
    return render_template('admin_dashboard.html')

@app.route('/admin/logo')
@admin_required
def admin_logo_page():
    """Logo管理页面"""
    return render_template('admin_logo.html')

@app.route('/admin/carousel')
@admin_required
def admin_carousel_page():
    """轮播图管理页面"""
    return render_template('admin_carousel.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return send_from_directory('.', 'admin_login.html')
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = username
            session['role'] = user['role']
            return jsonify({"msg": "登录成功", "role": user['role']})
        return jsonify({"msg": "用户名或密码错误"}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('user', None)
    session.pop('role', None)
    return jsonify({"msg": "已退出登录"})

@app.route('/api/categories')
def get_categories():
    """获取所有分类"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY id")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(categories)

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    """分类管理"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        
        if not name:
            return jsonify({"msg": "分类名称不能为空"}), 400
        
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
        
        category_id = cursor.lastrowid
        cursor.execute("SELECT * FROM categories WHERE id=%s", (category_id,))
        category = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({"msg": "分类添加成功", "category": category}), 201
    else:
        cursor.execute("SELECT * FROM categories ORDER BY id")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(categories)

@app.route('/admin/categories/<int:category_id>', methods=['PUT', 'DELETE'])
@admin_required
def edit_category(category_id):
    """编辑或删除分类"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查分类是否存在
    cursor.execute("SELECT * FROM categories WHERE id=%s", (category_id,))
    category = cursor.fetchone()
    if not category:
        cursor.close()
        conn.close()
        return jsonify({"msg": "分类不存在"}), 404
    
    if request.method == 'PUT':
        data = request.json
        name = data.get('name', category['name'])
        
        cursor.execute("UPDATE categories SET name=%s WHERE id=%s", (name, category_id))
        conn.commit()
        
        cursor.execute("SELECT * FROM categories WHERE id=%s", (category_id,))
        updated_category = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({"msg": "分类更新成功", "category": updated_category})
    
    elif request.method == 'DELETE':
        # 检查是否有新闻使用此分类
        cursor.execute("SELECT COUNT(*) as count FROM news WHERE category_id=%s", (category_id,))
        count = cursor.fetchone()['count']
        
        if count > 0:
            cursor.close()
            conn.close()
            return jsonify({"msg": f"该分类下还有{count}条新闻，无法删除"}), 400
        
        cursor.execute("DELETE FROM categories WHERE id=%s", (category_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"msg": "分类删除成功"})

@app.route('/admin/news', methods=['GET', 'POST'])
@admin_required
def admin_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        new_news = News(title=title, content=content)
        db.session.add(new_news)
        db.session.commit()
        flash('新闻添加成功')
        return redirect(url_for('admin_news'))
    news_list = News.query.order_by(News.create_time.desc()).all()
    return render_template('admin_news.html', news_list=news_list)
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO news (title, content, create_time, author) VALUES (%s, %s, NOW(), %s)",
            (data['title'], data['content'], session['user'])
        )
        conn.commit()
        news_id = cursor.lastrowid
        cursor.execute("SELECT * FROM news WHERE id=%s", (news_id,))
        news = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "新闻添加成功", "news": news}), 201
    else:
        cursor.execute("SELECT * FROM news ORDER BY create_time DESC")
        news_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(news_list)

@app.route('/admin/news/<int:news_id>', methods=['PUT', 'DELETE'])
def edit_news(news_id):
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE id=%s", (news_id,))
    news = cursor.fetchone()
    if not news:
        cursor.close()
        conn.close()
        return jsonify({"msg": "新闻不存在"}), 404
    if request.method == 'PUT':
        data = request.json
        cursor.execute(
            "UPDATE news SET title=%s, content=%s WHERE id=%s",
            (data.get('title', news['title']), data.get('content', news['content']), news_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM news WHERE id=%s", (news_id,))
        updated_news = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "新闻更新成功", "news": updated_news})
    else:
        cursor.execute("DELETE FROM news WHERE id=%s", (news_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"msg": "新闻已删除"})

@app.route('/api/stats')
@admin_required
def get_stats():
    """获取网站统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # 新闻统计
    cursor.execute("SELECT COUNT(*) as count FROM news")
    stats['news_count'] = cursor.fetchone()['count']
    
    # 留言统计
    cursor.execute("SELECT COUNT(*) as count FROM messages")
    stats['message_count'] = cursor.fetchone()['count']
    
    # 未回复留言统计
    cursor.execute("SELECT COUNT(*) as count FROM messages WHERE reply IS NULL OR reply = ''")
    stats['unread_message_count'] = cursor.fetchone()['count']
    
    # 服务统计
    cursor.execute("SELECT COUNT(*) as count FROM services")
    stats['service_count'] = cursor.fetchone()['count']
    
    # 政务信息统计
    cursor.execute("SELECT COUNT(*) as count FROM government")
    stats['government_count'] = cursor.fetchone()['count']
    
    # 用户统计
    cursor.execute("SELECT COUNT(*) as count FROM users")
    stats['user_count'] = cursor.fetchone()['count']
    
    # 最近7天新闻统计
    cursor.execute("SELECT COUNT(*) as count FROM news WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    stats['recent_news_count'] = cursor.fetchone()['count']
    
    # 最近7天留言统计
    cursor.execute("SELECT COUNT(*) as count FROM messages WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    stats['recent_message_count'] = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify(stats)

@app.route('/admin/users', methods=['GET'])
def admin_users():
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, create_time FROM users ORDER BY create_time DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

@app.route('/admin/messages')
@admin_required
def admin_messages_page():
    """管理员留言管理页面"""
    return render_template('admin_messages.html')

@app.route('/admin/messages', methods=['GET', 'POST'])
def admin_messages():
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO messages (name, contact, content, create_time) VALUES (%s, %s, %s, NOW())",
            (data['name'], data.get('contact', ''), data['content'])
        )
        conn.commit()
        msg_id = cursor.lastrowid
        cursor.execute("SELECT * FROM messages WHERE id=%s", (msg_id,))
        msg = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "留言添加成功", "message": msg}), 201
    else:
        cursor.execute("SELECT * FROM messages ORDER BY create_time DESC")
        msgs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(msgs)

@app.route('/admin/messages/<int:msg_id>/reply', methods=['POST'])
@admin_required
def reply_message(msg_id):
    """管理员回复留言"""
    data = request.json
    reply_content = data.get('reply')
    
    if not reply_content:
        return jsonify({"msg": "回复内容不能为空"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查留言是否存在
    cursor.execute("SELECT * FROM messages WHERE id=%s", (msg_id,))
    message = cursor.fetchone()
    if not message:
        cursor.close()
        conn.close()
        return jsonify({"msg": "留言不存在"}), 404
    
    # 更新留言回复
    cursor.execute(
        "UPDATE messages SET reply=%s WHERE id=%s",
        (reply_content, msg_id)
    )
    conn.commit()
    
    # 获取更新后的留言
    cursor.execute("SELECT * FROM messages WHERE id=%s", (msg_id,))
    updated_message = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({"msg": "回复成功", "message": updated_message})

@app.route('/admin/government', methods=['GET', 'POST'])
def admin_government():
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO government (title, file_url) VALUES (%s, %s)",
            (data['title'], data.get('file_url', ''))
        )
        conn.commit()
        gov_id = cursor.lastrowid
        cursor.execute("SELECT * FROM government WHERE id=%s", (gov_id,))
        gov = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "政务信息添加成功", "government": gov}), 201
    else:
        cursor.execute("SELECT * FROM government ORDER BY id DESC")
        govs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(govs)

@app.route('/admin/government/<int:gov_id>', methods=['PUT', 'DELETE'])
def edit_government(gov_id):
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM government WHERE id=%s", (gov_id,))
    gov = cursor.fetchone()
    if not gov:
        cursor.close()
        conn.close()
        return jsonify({"msg": "政务信息不存在"}), 404
    if request.method == 'PUT':
        data = request.json
        cursor.execute(
            "UPDATE government SET title=%s, file_url=%s WHERE id=%s",
            (data.get('title', gov['title']), data.get('file_url', gov['file_url']), gov_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM government WHERE id=%s", (gov_id,))
        updated_gov = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "政务信息更新成功", "government": updated_gov})
    else:
        cursor.execute("DELETE FROM government WHERE id=%s", (gov_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"msg": "政务信息已删除"})

@app.route('/admin/services', methods=['GET', 'POST'])
def admin_services():
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO services (name, description, file_url) VALUES (%s, %s, %s)",
            (data['name'], data.get('description', ''), data.get('file_url', ''))
        )
        conn.commit()
        service_id = cursor.lastrowid
        cursor.execute("SELECT * FROM services WHERE id=%s", (service_id,))
        service = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "服务添加成功", "service": service}), 201
    else:
        cursor.execute("SELECT * FROM services ORDER BY id DESC")
        services = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(services)

@app.route('/admin/services/<int:service_id>', methods=['PUT', 'DELETE'])
def edit_services(service_id):
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE id=%s", (service_id,))
    service = cursor.fetchone()
    if not service:
        cursor.close()
        conn.close()
        return jsonify({"msg": "服务不存在"}), 404
    if request.method == 'PUT':
        data = request.json
        cursor.execute(
            "UPDATE services SET name=%s, description=%s, file_url=%s WHERE id=%s",
            (data.get('name', service['name']), data.get('description', service['description']), data.get('file_url', service['file_url']), service_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM services WHERE id=%s", (service_id,))
        updated_service = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "服务更新成功", "service": updated_service})
    else:
        cursor.execute("DELETE FROM services WHERE id=%s", (service_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"msg": "服务已删除"})

@app.route('/admin/village', methods=['GET', 'POST'])
def admin_village():
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO village_info (title, content, image_url) VALUES (%s, %s, %s)",
            (data['title'], data['content'], data.get('image_url', ''))
        )
        conn.commit()
        vid = cursor.lastrowid
        cursor.execute("SELECT * FROM village_info WHERE id=%s", (vid,))
        info = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "乡村概况添加成功", "village": info}), 201
    else:
        cursor.execute("SELECT * FROM village_info ORDER BY id DESC")
        infos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(infos)

@app.route('/admin/village/<int:vid>', methods=['PUT', 'DELETE'])
def edit_village(vid):
    if 'user' not in session:
        return jsonify({"msg": "未登录"}), 401
    if session.get('role') != 'admin':
        return jsonify({"msg": "无权限"}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM village_info WHERE id=%s", (vid,))
    info = cursor.fetchone()
    if not info:
        cursor.close()
        conn.close()
        return jsonify({"msg": "乡村概况不存在"}), 404
    if request.method == 'PUT':
        data = request.json
        cursor.execute(
            "UPDATE village_info SET title=%s, content=%s, image_url=%s WHERE id=%s",
            (data.get('title', info['title']), data.get('content', info['content']), data.get('image_url', info['image_url']), vid)
        )
        conn.commit()
        cursor.execute("SELECT * FROM village_info WHERE id=%s", (vid,))
        updated_info = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"msg": "乡村概况更新成功", "village": updated_info})
    else:
        cursor.execute("DELETE FROM village_info WHERE id=%s", (vid,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"msg": "乡村概况已删除"})



@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory('.', filename)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory('uploads', filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/api/upload', methods=['POST'])
@admin_required
def upload_file():
    """文件上传接口"""
    if 'file' not in request.files:
        return jsonify({"msg": "没有文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "没有选择文件"}), 400
    
    if file:
        # 安全的文件名处理
        import uuid
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        # 生成唯一文件名
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else str(uuid.uuid4().hex)
        
        # 检查文件类型
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
        if file_ext not in allowed_extensions:
            return jsonify({"msg": "不支持的文件类型"}), 400
        
        # 保存文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        return jsonify({
            "msg": "文件上传成功",
            "filename": unique_filename,
            "original_name": filename,
            "url": f"/download/{unique_filename}"
        })

@app.route('/api/upload/image', methods=['POST'])
@admin_required
def upload_image():
    """图片上传接口"""
    if 'image' not in request.files:
        return jsonify({"msg": "没有图片"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"msg": "没有选择图片"}), 400
    
    if file:
        import uuid
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # 检查图片类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if file_ext not in allowed_extensions:
            return jsonify({"msg": "不支持的图片格式，仅支持 PNG, JPG, JPEG, GIF, WebP"}), 400
        
        # 检查文件大小 (5MB限制)
        max_size = 5 * 1024 * 1024  # 5MB
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置文件指针
        if file_size > max_size:
            return jsonify({"msg": "图片大小不能超过5MB"}), 400
        
        # 生成唯一文件名
        unique_filename = f"carousel_{uuid.uuid4().hex}.{file_ext}"
        
        # 保存图片
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # 检查图片尺寸 (可选，记录但不强制限制)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                app.logger.info(f"上传图片尺寸: {width}x{height}")
        except Exception as e:
            app.logger.warning(f"无法获取图片尺寸: {e}")
        
        return jsonify({
            "msg": "图片上传成功",
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "size": file_size
        })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        flash('请填写用户名和密码')
        return redirect(url_for('login'))
    
    # 使用ORM方式查询用户
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user'] = username
        session['role'] = user.role
        # 根据用户角色重定向到不同页面
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))
    else:
        flash('用户名或密码错误')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """用户注销功能"""
    session.pop('user', None)
    session.pop('role', None)
    flash('已成功退出登录')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not username or not password or not confirm_password:
        flash('请填写所有字段')
        return redirect(url_for('register'))
    if password != confirm_password:
        flash('两次密码输入不一致')
        return redirect(url_for('register'))
    
    # 使用ORM方式检查用户是否存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在')
        return redirect(url_for('register'))
    
    # 创建新用户
    new_user = User(username=username, role='user')
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash('注册成功，请登录')
    return redirect(url_for('login'))

# ------------------- Logo和轮播图管理接口 -------------------
@app.route('/api/logo')
def get_village_logo():
    """获取乡村Logo"""
    logo = VillageLogo.query.filter_by(is_active=True).first()
    if logo:
        return jsonify({
            'id': logo.id,
            'name': logo.name,
            'logo_url': logo.logo_url,
            'description': logo.description
        })
    return jsonify({'msg': '暂无Logo'}), 404

@app.route('/admin/logo', methods=['GET', 'POST'])
@admin_required
def admin_logo():
    """管理乡村Logo"""
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        logo_url = data.get('logo_url')
        description = data.get('description', '')
        
        if not name or not logo_url:
            return jsonify({'msg': '乡村名称和Logo不能为空'}), 400
        
        # 检查是否已存在Logo
        existing_logo = VillageLogo.query.filter_by(is_active=True).first()
        if existing_logo:
            # 更新现有Logo
            existing_logo.name = name
            existing_logo.logo_url = logo_url
            existing_logo.description = description
            existing_logo.update_time = datetime.utcnow()
            db.session.commit()
            return jsonify({'msg': 'Logo更新成功', 'logo': {
                'id': existing_logo.id,
                'name': existing_logo.name,
                'logo_url': existing_logo.logo_url,
                'description': existing_logo.description
            }})
        else:
            # 创建新Logo
            new_logo = VillageLogo(
                name=name,
                logo_url=logo_url,
                description=description
            )
            db.session.add(new_logo)
            db.session.commit()
            return jsonify({'msg': 'Logo创建成功', 'logo': {
                'id': new_logo.id,
                'name': new_logo.name,
                'logo_url': new_logo.logo_url,
                'description': new_logo.description
            }}), 201
    
    # GET请求获取当前Logo
    logo = VillageLogo.query.filter_by(is_active=True).first()
    if logo:
        return jsonify({
            'id': logo.id,
            'name': logo.name,
            'logo_url': logo.logo_url,
            'description': logo.description,
            'create_time': logo.create_time.isoformat(),
            'update_time': logo.update_time.isoformat()
        })
    return jsonify({'msg': '暂无Logo'}), 404

@app.route('/api/carousel')
def get_village_carousel():
    """获取乡村风光轮播图"""
    carousels = VillageCarousel.query.filter_by(is_active=True).order_by(VillageCarousel.sort_order).all()
    return jsonify([{
        'id': carousel.id,
        'title': carousel.title,
        'image_url': carousel.image_url,
        'description': carousel.description,
        'link_url': carousel.link_url,
        'sort_order': carousel.sort_order
    } for carousel in carousels])

@app.route('/admin/carousel', methods=['GET', 'POST'])
@admin_required
def admin_carousel():
    """管理乡村风光轮播图"""
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        image_url = data.get('image_url')
        description = data.get('description', '')
        link_url = data.get('link_url', '')
        sort_order = data.get('sort_order', 0)
        
        if not title or not image_url:
            return jsonify({'msg': '标题和图片不能为空'}), 400
        
        # 创建新轮播图
        new_carousel = VillageCarousel(
            title=title,
            image_url=image_url,
            description=description,
            link_url=link_url,
            sort_order=sort_order
        )
        db.session.add(new_carousel)
        db.session.commit()
        
        return jsonify({'msg': '轮播图添加成功', 'carousel': {
            'id': new_carousel.id,
            'title': new_carousel.title,
            'image_url': new_carousel.image_url,
            'description': new_carousel.description,
            'link_url': new_carousel.link_url,
            'sort_order': new_carousel.sort_order
        }}), 201
    
    # GET请求获取所有轮播图
    carousels = VillageCarousel.query.order_by(VillageCarousel.sort_order).all()
    return jsonify([{
        'id': carousel.id,
        'title': carousel.title,
        'image_url': carousel.image_url,
        'description': carousel.description,
        'link_url': carousel.link_url,
        'sort_order': carousel.sort_order,
        'is_active': carousel.is_active,
        'create_time': carousel.create_time.isoformat(),
        'update_time': carousel.update_time.isoformat()
    } for carousel in carousels])

@app.route('/admin/carousel/<int:carousel_id>', methods=['PUT', 'DELETE'])
@admin_required
def edit_carousel(carousel_id):
    """编辑或删除轮播图"""
    carousel = VillageCarousel.query.get_or_404(carousel_id)
    
    if request.method == 'PUT':
        data = request.json
        carousel.title = data.get('title', carousel.title)
        carousel.image_url = data.get('image_url', carousel.image_url)
        carousel.description = data.get('description', carousel.description)
        carousel.link_url = data.get('link_url', carousel.link_url)
        carousel.sort_order = data.get('sort_order', carousel.sort_order)
        carousel.is_active = data.get('is_active', carousel.is_active)
        carousel.update_time = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'msg': '轮播图更新成功', 'carousel': {
            'id': carousel.id,
            'title': carousel.title,
            'image_url': carousel.image_url,
            'description': carousel.description,
            'link_url': carousel.link_url,
            'sort_order': carousel.sort_order,
            'is_active': carousel.is_active
        }})
    
    elif request.method == 'DELETE':
        db.session.delete(carousel)
        db.session.commit()
        return jsonify({'msg': '轮播图删除成功'})

@app.route('/admin/carousel/reorder', methods=['POST'])
@admin_required
def reorder_carousel():
    """重新排序轮播图"""
    data = request.json
    carousel_orders = data.get('carousel_orders', [])
    
    for item in carousel_orders:
        carousel = VillageCarousel.query.get(item['id'])
        if carousel:
            carousel.sort_order = item['sort_order']
    
    db.session.commit()
    return jsonify({'msg': '轮播图排序更新成功'})

if __name__ == '__main__':
    # 数据库表初始化和管理员用户创建逻辑
    with app.app_context():
        db.create_all()
        # 检查是否存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            db.session.commit()
    app.run(host='0.0.0.0', port=8080, debug=False)
"""前端可维护性改造冒烟测试：验证新页面可渲染、API 契约不变。"""
import sys
from routes import create_app
from models import db, SiteConfig, FriendLink, VillageHighlight, VillageStat, People, News

app = create_app()
client = app.test_client()

with app.app_context():
    db.create_all()
    # 确保有默认站点配置（否则 get() 返回内存默认，页面也应不崩）
    if not SiteConfig.query.first():
        db.session.add(SiteConfig(id=1, **SiteConfig.default_values()))
        db.session.commit()
    # 造一条人物与新闻，便于 /people/<id> 与首页最新动态渲染
    if not People.query.first():
        db.session.add(People(name="测试人物", relation="村民", bio="测试简介", birth_year=1950))
        db.session.commit()
    if not News.query.first():
        db.session.add(News(title="测试新闻", content="这是一条用于冒烟测试的新闻内容。"))
        db.session.commit()
    pid = People.query.first().id

results = []
def check(name, resp, expect_status=200):
    if isinstance(expect_status, (list, tuple)):
        ok = resp.status_code in expect_status
    else:
        ok = resp.status_code == expect_status
    results.append((name, resp.status_code, ok))
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {resp.status_code}")

# 公开页面
check("GET /", client.get("/"))
check("GET /about", client.get("/about"))
check("GET /media", client.get("/media"))
check("GET /contact", client.get("/contact"))
check("GET /village", client.get("/village"))
check(f"GET /people/{pid}", client.get(f"/people/{pid}"))
# 不存在的人物应 404 而非 500
check("GET /people/99999 (expect 404)", client.get("/people/99999"), 404)
# 后台页（未登录会被 admin_required 返回 401，但不应 500）
check("GET /admin/site-settings (expect 401)", client.get("/admin/site-settings"), 401)
check("GET /admin/home-features (expect 401)", client.get("/admin/home-features"), 401)
check("GET /admin/friend-links (expect 401)", client.get("/admin/friend-links"), 401)
check("GET /admin/village-highlights (expect 401)", client.get("/admin/village-highlights"), 401)
check("GET /admin/village-stats (expect 401)", client.get("/admin/village-stats"), 401)

# API 契约检查
r = client.get("/api/home/stats")
check("GET /api/home/stats", r, 200)
if r.status_code == 200:
    data = r.get_json()
    keys_ok = set(["population", "area", "output", "satisfaction", "users", "memories", "news", "services"]).issubset(data.keys())
    print("  /api/home/stats keys:", list(data.keys()), "OK" if keys_ok else "MISSING")
    results.append(("home/stats keys", 200 if keys_ok else 0, keys_ok))

# 以 admin 登录后校验后台页可渲染（不应 500）
with client.session_transaction() as sess:
    sess["user"] = "admin"
    sess["role"] = "admin"
for path in ["/admin/site-settings", "/admin/home-features", "/admin/friend-links",
             "/admin/village-highlights", "/admin/village-stats"]:
    check(f"admin GET {path}", client.get(path), 200)

# 验证首页是否含有来自 SiteConfig 的导航/页脚文案
html = client.get("/").data.decode("utf-8", "ignore")
has_nav = "乡村记忆" in html
results.append(("首页含站点名", 200 if has_nav else 0, has_nav))

failed = [r for r in results if not r[2]]
print("\n==== 冒烟结果 ====")
print("总计:", len(results), "失败:", len(failed))
sys.exit(1 if failed else 0)

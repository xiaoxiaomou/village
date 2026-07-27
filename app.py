"""
乡村记忆系统 - 应用入口
"""

import _compat  # noqa: F401 — Windows + asyncio 兼容桩

from routes import create_app

app = create_app()

if __name__ == "__main__":
    from werkzeug.security import generate_password_hash
    from models import db, User

    def _ensure_site_config_columns():
        """自愈式加列：比对 site_config 表列集合，缺失则 ALTER 补齐并回填默认值。

        仅在旧库未执行 db_migrate_site_config.py 时兜底；幂等，可重复运行。
        须已在应用上下文（app_context）内调用。
        """
        from sqlalchemy import inspect as sa_inspect, text
        from models import SiteConfig

        # 模型新增的 7 个列（与 models.py / default_values 双写一致）
        new_cols = [
            "hero_subtitle",
            "stat_labels",
            "intro_title",
            "intro_subtitle",
            "features_title",
            "features_subtitle",
            "village_info_title",
        ]
        try:
            existing_cols = {c["name"] for c in sa_inspect(db.engine).get_columns("site_config")}
        except Exception:
            # 表不存在时 db.create_all 已建好带新列的表，无需处理
            return
        missing_cols = [c for c in new_cols if c not in existing_cols]
        if not missing_cols:
            return

        # 先加列（ALTER 后立即提交，使后续模型查询可见新列）
        with db.engine.begin() as conn:
            for col in missing_cols:
                conn.execute(text(f"ALTER TABLE site_config ADD COLUMN {col} TEXT"))

        # 再用默认值回填为 NULL 的列（仅当真实数据行存在时）
        cfg = SiteConfig.query.first()
        if cfg is not None:
            defaults = SiteConfig.default_values()
            for col in missing_cols:
                if not getattr(cfg, col, None):
                    setattr(cfg, col, defaults.get(col, ""))
            db.session.commit()
        print(f"[自愈] 已为 site_config 补齐缺失列并回填: {missing_cols}")

    with app.app_context():
        db.create_all()

        # ── 自愈式加列（保险）：旧库未执行迁移脚本时，补齐 SiteConfig 新增列并回填 ──
        # 若 site_config 表已存在但缺新列，SELECT 会因缺列报错导致全站配置丢失，
        # 此处用 inspect 比对列集合，缺失则 ALTER 补齐，再用默认值回填。幂等、可重复。
        _ensure_site_config_columns()

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

        # 初始化联系信息默认数据（仅在为空时填充）
        from models import SiteContact, HomeFeature

        if not SiteContact.query.first():
            db.session.add(
                SiteContact(
                    address="美丽乡村示范村村委会大楼",
                    phone="0123-12345678",
                    mobile="138-0123-4567",
                    email="village@example.com",
                    website="www.village-demo.com",
                    work_hours=(
                        "周一至周五 8:30 - 17:30\n"
                        "周六 9:00 - 16:00\n"
                        "周日 休息\n"
                        "午休时间 12:00 - 14:00"
                    ),
                    work_note=(
                        "法定节假日休息\n紧急事务请拨打24小时热线\n建议提前电话预约"
                    ),
                    public_transit=(
                        '乘坐123路公交车到"村委会站"下车\n'
                        '乘坐456路公交车到"乡村广场站"下车，步行5分钟\n'
                        '地铁2号线"乡村站"A出口，转乘123路公交'
                    ),
                    driving_route=(
                        '导航搜索"美丽乡村村委会"\n'
                        "高速公路乡村出口下，直行3公里\n"
                        "村委会大楼提供免费停车位"
                    ),
                    wechat="village2024",
                )
            )

        if not HomeFeature.query.first():
            defaults = [
                HomeFeature(
                    title="生态农业",
                    description="推广绿色种植技术，发展有机农业，保护生态环境，提供健康农产品。",
                    icon="fa-leaf",
                    icon_color="red",
                    link="/services",
                    sort_order=1,
                ),
                HomeFeature(
                    title="乡村旅游",
                    description="开发特色民宿，打造乡村旅游路线，让游客体验纯正的乡村生活和文化。",
                    icon="fa-home",
                    icon_color="jade",
                    link="/services",
                    sort_order=2,
                ),
                HomeFeature(
                    title="便民服务",
                    description="提供政务咨询、医疗服务、教育资源等便民服务，解决村民生活难题。",
                    icon="fa-hands-helping",
                    icon_color="gold",
                    link="/services",
                    sort_order=3,
                ),
            ]
            db.session.add_all(defaults)

        # 初始化站点全局配置（单行，id=1）：仅在为空时填充
        from models import SiteConfig, FriendLink, VillageHighlight, VillageStat

        if not SiteConfig.query.first():
            cfg = SiteConfig(id=1, **SiteConfig.default_values())
            db.session.add(cfg)

        # 友情链接默认数据
        if not FriendLink.query.first():
            friend_links = [
                FriendLink(name="乡村振兴局", url="https://www.moa.gov.cn/", description="农业农村部官方网站", sort_order=1),
                FriendLink(name="中国文明网", url="http://www.wenming.cn/", description="精神文明建设门户网站", sort_order=2),
                FriendLink(name="学习强国", url="https://www.xuexi.cn/", description="权威学习平台", sort_order=3),
            ]
            db.session.add_all(friend_links)

        # 村情·乡村特色默认卡片
        if not VillageHighlight.query.first():
            highlights = [
                VillageHighlight(title="生态环境", description="山清水秀，空气清新，森林覆盖率高，是天然的生态氧吧", icon="fas fa-leaf", sort_order=1),
                VillageHighlight(title="民居特色", description="传统村落格局保存完好，白墙黛瓦与现代设施完美融合", icon="fas fa-home", sort_order=2),
                VillageHighlight(title="人文风情", description="淳朴民风，热情好客，丰富的民俗文化和传统手工艺", icon="fas fa-hands-helping", sort_order=3),
            ]
            db.session.add_all(highlights)

        # 村情·村庄信息默认指标
        if not VillageStat.query.first():
            stats = [
                VillageStat(label="耕地面积", value="约2800亩", group_name="自然资源", sort_order=1),
                VillageStat(label="山林面积", value="约5000亩", group_name="自然资源", sort_order=2),
                VillageStat(label="水域面积", value="约200亩", group_name="自然资源", sort_order=3),
                VillageStat(label="森林覆盖率", value="65%", group_name="自然资源", sort_order=4),
                VillageStat(label="户数", value="约620户", group_name="人口概况", sort_order=1),
                VillageStat(label="劳动力", value="约1500人", group_name="人口概况", sort_order=2),
                VillageStat(label="外出务工", value="约400人", group_name="人口概况", sort_order=3),
                VillageStat(label="党员", value="68人", group_name="人口概况", sort_order=4),
                VillageStat(label="主导产业", value="水稻种植", group_name="产业发展", sort_order=1),
                VillageStat(label="特色产业", value="乡村旅游", group_name="产业发展", sort_order=2),
                VillageStat(label="合作社", value="5家", group_name="产业发展", sort_order=3),
                VillageStat(label="电商平台", value="3个", group_name="产业发展", sort_order=4),
                VillageStat(label="道路硬化", value="100%", group_name="基础设施", sort_order=1),
                VillageStat(label="自来水", value="100%", group_name="基础设施", sort_order=2),
                VillageStat(label="网络覆盖", value="98%", group_name="基础设施", sort_order=3),
                VillageStat(label="路灯安装", value="156盏", group_name="基础设施", sort_order=4),
            ]
            db.session.add_all(stats)

        db.session.commit()

    # debug 保持关闭(生产环境不应开调试器),但单独开启模板自动重载,
    # 这样改 HTML 后无需重启服务即可生效
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True
    app.run(host="0.0.0.0", port=5000, debug=False)

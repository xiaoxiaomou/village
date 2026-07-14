"""
乡村记忆系统 - 应用入口
"""

import _compat  # noqa: F401 — Windows + asyncio 兼容桩

from routes import create_app

app = create_app()

if __name__ == "__main__":
    from werkzeug.security import generate_password_hash
    from models import db, User

    with app.app_context():
        db.create_all()
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

        db.session.commit()

    app.run(host="0.0.0.0", port=5000, debug=False)

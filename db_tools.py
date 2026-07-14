# -*- coding: utf-8 -*-
"""
农村记忆系统 - 数据库初始化和迁移工具
创建所有表 + 默认数据
"""

import os
import sys
import json
from datetime import datetime, date

from flask import Flask
from models import (
    db,
    User,
    Tag,
    People,
    Memory,
    MemoryTag,
    Backup,
    News,
    Category,
    Service,
    Government,
    VillageInfo,
    Message,
)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "village.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "village-memory-secret-key-change-me"
    db.init_app(app)
    return app


def init_database():
    app = create_app()
    with app.app_context():
        db.create_all()
    print("  数据库表已创建")
    return app


def init_default_data():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            print("  默认管理员已创建 (admin/admin123)")

        default_tags = [
            ("亲人", "person"),
            ("故乡", "place"),
            ("节日", "event"),
            ("丰收", "event"),
            ("童年", "emotion"),
            ("乡怀", "emotion"),
            ("传统技艺", "general"),
            ("村口老树", "place"),
            ("邻里互助", "event"),
        ]
        for name, category in default_tags:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name, category=category)
                db.session.add(tag)
                print(f"  默认标签已创建: {name}")

        default_people = [
            ("爷爷", "长辈", "家族的回忆守护者"),
            ("奶奶", "长辈", "村里最会讲故事的人"),
            ("小明", "同中", "从小一起长大的伙伴"),
        ]
        for name, relation, bio in default_people:
            person = People.query.filter_by(name=name).first()
            if not person:
                person = People(name=name, relation=relation, bio=bio)
                db.session.add(person)
                print(f"  默认人物已创建: {name}")

        sample_memory = Memory.query.first()
        if not sample_memory:
            memory = Memory(
                title="村口老槐树",
                content="村口的那棵老槐树，据村里老人说已经有几百年的历史了。每到夏天，村民们都会聚集在树下乘凉聊天。",
                reflection="小时候最喜欢在树下听爷爷讲故事，那棵老槐树见证了我们这一代人的成长。",
                memory_type="photo",
                date_recorded=date(2024, 6, 15),
                people_involved=json.dumps(["爷爷", "奶奶"]),
                locations=json.dumps(["村口老树"]),
                tags=json.dumps(["故乡", "童年"]),
            )
            db.session.add(memory)
            print("  示例记忆已创建: 村口老槐树")

        backfill_memory_tags()
        db.session.commit()


def backfill_memory_tags():
    """将 memories.tags(JSON 文本) 中记录的标签同步到 memory_tags 关联表，
    使「按标签筛选」可用。兼容历史数据：tags 字段可能是标签名，也可能是标签 id。"""
    created = 0
    for mem in Memory.query.all():
        if MemoryTag.query.filter_by(memory_id=mem.id).first():
            continue
        try:
            raw = json.loads(mem.tags) if mem.tags else []
        except Exception:
            raw = []
        for item in raw:
            tag = None
            if isinstance(item, int):
                tag = Tag.query.get(item)
            elif isinstance(item, str):
                item = item.strip()
                if item.isdigit():
                    tag = Tag.query.get(int(item))
                else:
                    tag = Tag.query.filter_by(name=item).first()
            if tag:
                db.session.add(
                    MemoryTag(
                        memory_id=mem.id,
                        tag_id=tag.id,
                        tag_category=tag.category,
                    )
                )
                created += 1
    if created:
        db.session.commit()
        print(f"  记忆标签已同步: {created} 条关联")


# ═══ 测试种子数据 ═══


def seed_test_data():
    """为每个模块添加 10 条测试数据（跳过已有数据）"""
    app = create_app()
    with app.app_context():
        import random
        from datetime import timedelta

        cats = ["政策解读", "乡村振兴", "农业科技", "文化活动", "民生实事"]
        # 先清理脏数据
        bad_cats = Category.query.filter(Category.name.in_(["1", "2", "3", "4", "5"])).all()
        for c in bad_cats:
            News.query.filter_by(category_id=c.id).update({"category_id": None}, synchronize_session=False)
            db.session.delete(c)
        db.session.flush()
        for name in cats:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name))
        db.session.commit()

        if News.query.count() < 10:
            news_data = [
                (
                    "2024年乡村振兴重点项目正式启动",
                    "今年我县将重点推进 12 个乡村振兴示范村建设，涵盖产业升级、基础设施改善、人居环境整治等多个方面，总投资预计超过 5000 万元。",
                ),
                (
                    "春季农业生产现场会顺利召开",
                    "全乡春季农业生产现场会在李家村召开，会议部署春耕备耕工作，推广水稻机械化插秧新技术。",
                ),
                (
                    "村级文化活动中心建成投用",
                    "经过半年建设，我村文化活动中心正式投入使用。中心配有图书室、棋牌室、健身广场等设施，丰富村民业余文化生活。",
                ),
                (
                    "农村电商培训助力农产品销售",
                    "乡政府联合电商平台举办为期三天的农村电商培训班，全村 50 余名种植大户参加培训，学习直播带货等新技能。",
                ),
                (
                    "乡村公路拓宽工程完工",
                    "连接三个自然村的 8 公里乡村公路拓宽工程顺利完工，路面由 3.5 米拓宽至 6 米，极大改善出行条件。",
                ),
                (
                    "首届村民议事会召开",
                    "首届村民议事会在村委会召开，村民代表就村庄规划、环境卫生、集体经济发展等议题充分讨论。",
                ),
                (
                    "传统手工艺培训班开班",
                    "村委会邀请非遗传承人开设竹编、剪纸、陶艺等传统手工艺培训班，吸引众多村民踊跃报名。",
                ),
                (
                    "高标准农田建设项目验收通过",
                    "800 亩高标准农田建设项目通过县级验收，配套完善灌溉排水系统，预计每亩增产约 15%。",
                ),
                (
                    "乡村医生签约服务惠及全村",
                    "村卫生室与乡卫生院联合开展家庭医生签约服务，全村常住人口签约率达 90% 以上。",
                ),
                (
                    "美丽庭院创建活动评选揭晓",
                    '经过一个季度评选，全村 30 户家庭获得"美丽庭院"称号，带动人居环境整体提升。',
                ),
            ]
            for title, content in news_data:
                if not News.query.filter_by(title=title).first():
                    cid = (
                        random.choice(Category.query.all()).id
                        if Category.query.count()
                        else None
                    )
                    n = News(
                        title=title, content=content, category_id=cid, author="村信息员"
                    )
                    n.create_time = datetime.utcnow() - timedelta(
                        days=random.randint(1, 180)
                    )
                    db.session.add(n)
            print("  新闻: 10 条")

        if Service.query.count() < 10:
            svc = [
                (
                    "农技服务站",
                    "提供农业技术咨询、土壤检测、病虫害防治指导等服务。",
                    "",
                ),
                (
                    "法律援助中心",
                    "每月 15 日、30 日开放，为村民提供免费法律咨询和援助服务。",
                    "",
                ),
                (
                    "卫生医疗服务点",
                    "村卫生室提供基础诊疗、慢性病管理、健康体检等服务。",
                    "",
                ),
                (
                    "民政事务代办点",
                    "代办低保申请、临时救助、残疾人补贴等民政业务。",
                    "",
                ),
                (
                    "社保医保服务窗口",
                    "协助办理城乡居民养老保险和医疗保险参保、缴费、报销等业务。",
                    "",
                ),
                (
                    "就业信息服务站",
                    "发布企业招聘信息，提供就业指导和职业技能培训报名。",
                    "",
                ),
                (
                    "农村电商服务站",
                    "提供农产品线上销售、快递收发、代购代销等电商服务。",
                    "",
                ),
                ("宅基地审批咨询", "解答农村宅基地申请、审批、确权等政策咨询。", ""),
                (
                    "文化体育设施",
                    "村文化广场、篮球场、健身路径等设施免费向村民开放。",
                    "",
                ),
                (
                    "水电维修服务队",
                    "由村里专业电工、水暖工组成，提供应急维修服务。",
                    "",
                ),
            ]
            for name, desc, url in svc:
                if not Service.query.filter_by(name=name).first():
                    db.session.add(Service(name=name, description=desc, file_url=url))
            print("  服务: 10 条")

        if Government.query.count() < 10:
            gov = [
                ("2024年度村集体经济发展规划", ""),
                ("第三季度村级财务收支公示", ""),
                ("农村低保对象名单公示（2024年）", ""),
                ("村级公益事业一事一议项目公告", ""),
                ("耕地地力保护补贴发放明细", ""),
                ("农村危房改造补助名单公示", ""),
                ("村规民约修订草案征求意见", ""),
                ("村级工程建设项目招标公告", ""),
                ("集体经济收益分配方案", ""),
                ("村干部年度考核结果公示", ""),
            ]
            for title, url in gov:
                if not Government.query.filter_by(title=title).first():
                    db.session.add(Government(title=title, file_url=url))
            print("  政务: 10 条")

        if VillageInfo.query.count() < 1:
            db.session.add(
                VillageInfo(
                    title="美丽新乡村",
                    content="全村总面积约 15 平方公里，辖 6 个自然村，总人口 2560 人。耕地面积 3200 亩，以水稻、蔬菜种植和畜禽养殖为主导产业。先后荣获省级文明村镇、市级美丽乡村示范村等荣誉称号。",
                    image_url="https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800",
                )
            )
            print("  村情: 1 条")

        if Message.query.count() < 10:
            msg = [
                (
                    "李大叔",
                    "137****5621",
                    "村里的路灯有几盏不亮了，晚上走路不方便，希望能安排维修。",
                ),
                ("张阿姨", "158****2349", "请问免费健康体检什么时候开始？需要预约吗？"),
                (
                    "王小明",
                    "139****8712",
                    "建议在村口公交站旁边建一个遮雨棚，等车时可以遮阳挡雨。",
                ),
                ("赵婶", "", "我家自来水最近水压有点小，能帮忙看看吗？"),
                (
                    "刘大爷",
                    "136****4538",
                    "老年活动中心的报纸好久没更新了，希望能定期换新。",
                ),
                (
                    "陈老师",
                    "150****6789",
                    "村里留守儿童暑假有什么活动安排？建议组织兴趣班。",
                ),
                ("小芳", "", "村口那块荒地能不能改造成小公园？放一些健身器材。"),
                ("老支书", "138****3456", "建议加强村里垃圾分类的宣传和监督。"),
                (
                    "周老板",
                    "189****2341",
                    "我想投资办一个农产品加工厂，请问需要办哪些手续？",
                ),
                ("孙大姐", "", "农业技术培训能不能多安排几次？上次错过了很遗憾。"),
            ]
            for name, contact, content in msg:
                m = Message(name=name, contact=contact, content=content)
                m.create_time = datetime.utcnow() - timedelta(
                    days=random.randint(1, 60)
                )
                db.session.add(m)
            print("  留言: 10 条")

        more_tags = [
            ("风景", "place"),
            ("美食", "general"),
            ("民俗", "event"),
            ("建筑", "place"),
            ("人物故事", "emotion"),
        ]
        for name, cat in more_tags:
            if not Tag.query.filter_by(name=name).first():
                db.session.add(Tag(name=name, category=cat))

        if Memory.query.count() < 10:
            mems = [
                (
                    "村口的老戏台",
                    "村口那座老戏台有四十多年历史了。小时候每到过年戏台上就唱大戏，十里八乡的人都赶来看，台上锣鼓喧天，台下人山人海。",
                    "2024-02-10",
                    ["民俗", "建筑"],
                    ["爷爷", "奶奶"],
                    ["村口"],
                ),
                (
                    "稻田里的童年",
                    "夏天放学后，我们一群孩子总爱跑到稻田里抓泥鳅、捉蜻蜓。绿油油的稻浪翻滚，光脚踩在田埂上，那是最自由快乐的时光。",
                    "2024-07-15",
                    ["童年", "乡怀"],
                    ["小明"],
                    ["稻田"],
                ),
                (
                    "老槐树下的故事会",
                    "村口那棵老槐树据说有三百年树龄了。夏天的傍晚，村里人都喜欢在树下乘凉，爷爷摇着蒲扇讲那些古老的故事。",
                    "2024-06-20",
                    ["村口老树", "故乡"],
                    ["爷爷", "奶奶"],
                    ["村口"],
                ),
                (
                    "打谷场的丰收季",
                    "秋天打谷场上堆满金黄稻谷，拖拉机轰隆隆响着，大人们忙着脱粒晾晒，孩子们在稻草堆里打滚捉迷藏。",
                    "2024-09-25",
                    ["丰收"],
                    [],
                    ["打谷场"],
                ),
                (
                    "腊月的年味",
                    "进入腊月村里就开始忙年了。杀年猪、打糍粑、磨豆腐、做腊肉，家家户户飘出诱人的香味。除夕夜全家围坐吃团圆饭。",
                    "2024-01-30",
                    ["节日", "美食"],
                    ["爷爷", "奶奶"],
                    ["老屋"],
                ),
                (
                    "村小的读书声",
                    "村小只有两排平房，操场是泥土的，但那是最快乐的地方。每天早晨的读书声、课间的追逐打闹、放学后在山坡上放风筝。",
                    "2024-05-01",
                    ["建筑", "童年"],
                    [],
                    ["村小"],
                ),
                (
                    "清明采茶记",
                    "后山那片茶园，清明前后满山茶树冒嫩芽。村里人挎竹篓采茶，山上飘着淡淡茶香。自己炒制的茶格外香甜。",
                    "2024-04-05",
                    ["传统技艺", "风景"],
                    ["奶奶"],
                    ["后山"],
                ),
                (
                    "端午龙舟赛",
                    "每年端午节乡里在清河上举办龙舟赛。各村龙舟队早早训练，锣鼓声呐喊声此起彼伏。我们村连续三年拿第一。",
                    "2024-06-10",
                    ["节日", "民俗"],
                    [],
                    ["清河"],
                ),
                (
                    "外婆家的老屋",
                    "外婆家是一座青砖黛瓦的老房子，天井里种着桂花树。秋天满院飘着桂花香，外婆在灶台前忙碌的身影是最温暖的记忆。",
                    "2024-08-15",
                    ["建筑", "美食"],
                    ["奶奶"],
                    ["外婆家"],
                ),
                (
                    "雪夜的村庄",
                    "那年冬天下很大的雪，整个村庄变成白色世界。雪夜里格外安静，只能听到雪花簌簌落下。第二天孩子们堆雪人打雪仗。",
                    "2024-12-25",
                    ["风景", "童年"],
                    [],
                    ["村庄"],
                ),
            ]
            for title, content, ds, tags, people, locs in mems:
                if not Memory.query.filter_by(title=title).first():
                    mem = Memory(
                        title=title,
                        content=content,
                        reflection="",
                        date_recorded=datetime.strptime(ds, "%Y-%m-%d").date(),
                        tags=json.dumps(tags),
                        people_involved=json.dumps(people),
                        locations=json.dumps(locs),
                        memory_type="text",
                        is_public=True,
                    )
                    db.session.add(mem)
            print("  记忆: 10 条")

        db.session.commit()
        print("  测试数据写入完成")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "init"
    if action == "init":
        init_database()
        init_default_data()
        print("  初始化完成")
    elif action == "seed":
        seed_test_data()
        print("  种子数据完成")
    elif action == "drop":
        app = create_app()
        with app.app_context():
            db.drop_all()
            print("  所有表已删除")
    elif action == "info":
        app = create_app()
        with app.app_context():
            # SQLAlchemy 2.0+ 兼容: 使用 inspect 替代已移除的 engine.table_names()
            from sqlalchemy import inspect, func

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"  数据库表: {tables}")
            for table in tables:
                try:
                    tbl = db.metadata.tables.get(table)
                    if tbl is not None:
                        count = db.session.execute(
                            db.select(func.count()).select_from(tbl)
                        ).scalar()
                        print(f"    {table}: {count} 条记录")
                except Exception as e:
                    print(f"    {table}: 查询失败 ({type(e).__name__})")
    else:
        print("  用法: python db_tools.py [init|drop|info|seed]")

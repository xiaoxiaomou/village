# 乡村记忆系统（Village Memory）

一个基于 Flask 的乡村信息展示与记忆管理 Web 应用。包含新闻动态、政务公开、村情介绍、便民服务、留言互动、记忆时间轴、人物档案、标签与媒体管理等模块，适合作为「美丽乡村 / 数字乡村」类项目的基础模板。

> 本项目使用 **SQLite** 作为数据库（开箱即用，无需安装 MySQL），便于本地运行与开源演示。

## 技术栈

- 后端：Python 3.8+ / Flask 3.x
- ORM：Flask-SQLAlchemy
- 数据库：SQLite（默认 `village.db`）
- 前端：原生 HTML / CSS / JavaScript + FontAwesome
- 接口文档：Flasgger（Swagger UI，可选）

## 功能概览

- 新闻动态：发布、编辑、删除、分页、搜索、分类
- 政务公开：政务信息发布与管理
- 村情介绍：村庄概况展示
- 便民服务：服务项目展示与维护
- 留言互动：用户留言 + 管理员回复
- 记忆时间轴：怀旧记录（文字 / 图片 / 视频 / 音频）、按标签筛选
- 人物档案、标签管理
- 媒体文件上传（图片 / 视频）与管理
- 用户注册审核、角色权限（admin / user）
- 系统通知、操作审计日志

## 目录结构

```
.
├── app.py              # 应用入口（创建表 + 默认数据）
├── start.py            # 智能启动脚本（建库、初始化、起服务）
├── config.py           # 配置（数据库 URI、密钥、上传目录等）
├── models.py           # SQLAlchemy 数据模型
├── db_tools.py         # 数据库工具（init / seed / drop / info / 标签回溯）
├── routes/             # 蓝图：auth / main / api / memories / admin
├── templates/          # Jinja2 模板
├── static/             # 静态资源（CSS / JS / 字体）
├── uploads/            # 用户上传文件（自动生成，已在 .gitignore 中忽略）
└── requirements.txt    # 依赖清单
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库并启动（自动建表 + 写入演示数据）
python start.py run
# 或者分步：python start.py init-db && python app.py

# 3. 浏览器访问
#   首页:        http://localhost:5000
#   Swagger API: http://localhost:5000/apidocs/
```

默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 部署到公网前请务必修改该密码，并通过环境变量 `SECRET_KEY` 设置独立的会话密钥。

## 配置说明

`config.py` 中的关键配置（均可通过环境变量覆盖）：

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `SECRET_KEY` | Flask 会话签名密钥 | 环境变量 `SECRET_KEY`，未设置时使用占位值 |
| `SQLALCHEMY_DATABASE_URI` | 数据库连接 | `sqlite:///<项目目录>/village.db` |
| `UPLOAD_FOLDER` | 上传文件目录 | `<项目目录>/uploads` |
| `PAGE_SIZE` | 后台每页条数 | 20 |
| `TINYMCE_API_KEY` | 后台富文本编辑器（TinyMCE）API Key | 环境变量 `TINYMCE_API_KEY`，未设置时回退为 `no-api-key`（编辑器会提示配置 Key） |

生成更强的密钥：

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

> 📄 本地开发可在项目根目录创建 `.env` 文件写入上述环境变量（已加入 `.gitignore`，**不会进入版本库**）。可参考 `.env.example` 模板。例如：
>
> ```ini
> TINYMCE_API_KEY=你的_tinymce_key
> SECRET_KEY=你的随机密钥
> ```
>
> 应用启动时会自动读取 `.env`，无需手动 `export`。

## 数据库维护

```bash
python db_tools.py init    # 建表 + 默认数据 + 记忆标签回溯
python db_tools.py seed    # 写入 10 条演示数据（新闻/政务/服务/记忆等）
python db_tools.py info    # 查看各表记录数
python db_tools.py drop    # 清空所有表（危险）
```

## 测试

```bash
pip install pytest
pytest -q
```

## 开源与贡献

- 许可证：见 [LICENSE](./LICENSE)（MIT）。
- 欢迎提交 Issue 与 Pull Request。
- 提交前请确保 `village.db`、`uploads/`、`cookies.txt` 等敏感 / 生成文件已被 `.gitignore` 忽略，不要将其推送到公开仓库。

## 安全提示

- 本仓库默认使用开发服务器（`app.run`），**请勿直接用于生产**。生产环境请使用 Gunicorn / uWSGI 等 WSGI 服务器，并置于 Nginx 反向代理之后。
- 切勿将包含真实用户数据的 `village.db` 或任何凭证文件提交到公开仓库。

# 乡村网站系统

## 项目简介

乡村网站系统是一个基于Flask的Web应用，用于乡村信息展示和管理。系统包含新闻发布、政务公开、村情介绍、留言互动等功能。

## 技术栈

- 后端：Python Flask
- 数据库：MySQL
- 前端：HTML, CSS, JavaScript

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置数据库

在`config.py`中配置MySQL数据库连接信息：

```python
MYSQL_HOST = '39.101.133.26'
MYSQL_USER = 'xiangcun'
MYSQL_PASSWORD = 'xiangcun123'
MYSQL_DB = 'xiangcun'
MYSQL_PORT = 3306
```

### 启动应用

直接运行启动脚本：

```bash
start.bat
```

或者手动执行以下步骤：

1. 初始化数据库：`python db_tools.py init`
2. 启动应用：`python app.py`

## 默认账户

- 用户名：admin
- 密码：admin123

## 主要功能

- 新闻管理：发布、编辑、删除新闻
- 政务公开：发布政务信息
- 村情介绍：展示村庄历史、文化等信息
- 留言互动：用户留言及管理员回复
- 用户管理：管理员账户管理

## 文件结构

- `app.py`：应用主程序
- `models.py`：数据模型定义
- `db_tools.py`：数据库工具（检查、修复、初始化）
- `start.bat`：一键启动脚本
- `templates/`：HTML模板
- `static/`：静态资源（CSS、JS、图片）
- `uploads/`：上传文件存储目录

## 数据库维护

使用`db_tools.py`进行数据库维护：

- 检查数据库：`python db_tools.py check`
- 修复数据库：`python db_tools.py fix`
- 初始化数据库：`python db_tools.py init`
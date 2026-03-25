# Syndra MySQL Client

[中文](#中文) | [English](#english)

---

## 中文

基于 PyQt6 开发的轻量级 MySQL 客户端工具，提供直观的图形界面管理 MySQL 数据库。

### 功能特性

✅ **连接管理**
- 保存多个数据库连接配置
- 密码加密存储
- 连接测试功能
- SSH 隧道支持（预留接口）

✅ **数据库浏览**
- Navicat 风格树形视图展示连接/数据库/表
- 未连接连接双击自动连接展开
- 双击打开表数据浏览
- 支持在新标签页打开多个表
- 标签页右键菜单：关闭所有/关闭左侧/关闭右侧
- 分页浏览（支持 10-100 条/页自定义）
- 右侧详情栏显示表创建 SQL、表大小、外键信息
- 底部搜索框实时筛选表名

✅ **SQL 编辑器**
- SQL 语法高亮
- 自动补全（关键字 + 函数 + **表名 + 字段名自动补全**）
- **SQL 格式化美化**（需要 `sqlparse` 库）
- **支持多个 SQL 查询标签页**
- 查询结果表格显示
- **SQL 历史记录与保存查询** - 最近 50 条历史，可保存常用查询

✅ **数据操作**
- 可直接编辑表格数据（增删改）
- 点击表头排序（当前页）
- 当前页搜索过滤
- 表格列宽度**支持手动调整**
- 右键**复制功能**：复制单元格 / 复制整行 / 复制全部
- **数据导出**：导出为 CSV / JSON 格式
- 结果可以直接复制粘贴到 Excel/Markdown

✅ **表结构操作**
- 可视化创建表（设计字段、索引）
- 修改表结构（增删改字段和索引）
- 新建数据库
- 重命名表/删除表/删除数据库

✅ **外观**
- 支持亮色/暗色主题切换
- 可调节分隔栏，布局灵活

### 项目结构

```
syndra_mysql/
├── main.py                    # 程序入口
├── __init__.py
├── gui/                       # UI 组件模块
│   ├── __init__.py
│   ├── highlighter.py         # SQL 语法高亮器
│   ├── sql_editor.py          # 支持自动补全的 SQL 编辑器
│   ├── connection_dialog.py   # 新建/编辑连接对话框
│   ├── table_info_dialog.py   # 表结构查看对话框
│   ├── table_data_browser_base.py  # 表格浏览逻辑基类
│   ├── table_data_browser_widget.py # 标签页版本
│   ├── table_create_dialog.py # 新建表设计对话框
│   ├── table_modify_dialog.py # 修改表结构对话框
│   ├── sql_history_dialog.py  # SQL历史与保存查询对话框
│   └── main_window.py         # 主窗口
├── core/                      # 核心逻辑模块
│   ├── __init__.py
│   ├── connection.py          # 连接管理器
│   └── workers.py            # 后台工作线程（连接测试、加载数据库）
└── utils/                    # 工具模块
    ├── __init__.py
    └── encryption.py         # 密码加密
```

### 依赖安装

```bash
pip install PyQt6 pymysql cryptography appdirs
```

**可选依赖**（用于 SQL 格式化）：
```bash
pip install sqlparse
```

### 运行

```bash
python main.py
```

### 打包为 exe (Windows)

安装 PyInstaller:
```bash
pip install pyinstaller
```

使用提供的 spec 文件打包:
```bash
pyinstaller Syndra-MySQL.spec
```

或者直接运行批处理脚本 (Windows):
```
build.bat
```

打包完成后，exe 文件在 `dist/` 目录下。

### 使用说明

#### 连接数据库
1. 点击左侧 **➕ 新建连接**
2. 填写连接信息：连接名、主机、端口、用户名、密码
3. 可以点击 **测试连接** 验证连接
4. 点击 **连接** 连接数据库，可选择保存连接配置

#### 浏览数据
1. 连接成功后会加载所有数据库和表
2. **双击** 连接自动连接，**双击** 表名在新标签页打开数据浏览
3. 底部搜索框输入关键词实时筛选表名
4. 支持分页浏览，可以调整每页显示条数
5. 单击表名在右侧详情栏查看表结构
6. 表格右键表头分隔线可以**手动调整列宽**
7. 右键单元格可以**复制**单元格/整行/全部数据

#### 执行 SQL 查询
1. 默认有一个 SQL Editor 标签页
2. 在菜单栏选择 **查询 → 新建SQL查询** 可以打开多个查询标签
3. 输入 SQL 后点击 **执行SQL**
4. SELECT 查询结果会显示在下方表格
5. 点击 **格式化SQL** 美化 SQL（需要 `sqlparse`）

### 安全
- 保存连接时密码使用 Fernet 对称加密存储
- 密钥基于固定密码导出，满足基本安全需求

### 许可证

MIT

---

## English

A lightweight MySQL client tool built with PyQt6, providing an intuitive graphical interface for managing MySQL databases.

### Features

✅ **Connection Management**
- Save multiple database connection configurations
- Encrypted password storage
- Connection testing
- SSH tunnel support (interface reserved)

✅ **Database Browser**
- Navicat-style tree view: connections → databases → tables
- Double-click an unconnected connection to connect and expand automatically
- Double-click a table to open data browser in new tab
- Open multiple tables in separate tabs
- Tab right-click menu: close all / close left / close right
- Pagination browsing (customizable 10-100 rows per page)
- Right sidebar shows table CREATE SQL, table size, foreign key info
- Real-time table name filtering with bottom search box

✅ **SQL Editor**
- SQL syntax highlighting
- Auto-completion (keywords + functions + **table names + column names**)
- **SQL formatting** (requires `sqlparse`)
- **Multiple SQL query tabs supported**
- Query results displayed in table
- **SQL History & Saved Queries** - last 50 queries, save frequently used queries

✅ **Data Manipulation**
- Direct table cell editing (insert/update/delete)
- Click header to sort (current page)
- Search/filter on current page
- **Manual column width adjustment**
- Right-click **copy**: copy cell / copy row / copy all
- **Data Export**: export to CSV / JSON format
- Results can be copied directly to Excel/Markdown

✅ **Schema Operations**
- Visual table creator (design columns, indexes)
- Alter table structure (add/drop/modify columns/indexes)
- Create new database
- Rename table / drop table / drop database

✅ **Appearance**
- Light/Dark theme toggle
- Adjustable splitters for flexible layout

### Project Structure

```
syndra_mysql/
├── main.py                    # Application entry
├── __init__.py
├── gui/                       # UI Components
│   ├── __init__.py
│   ├── highlighter.py         # SQL syntax highlighter
│   ├── sql_editor.py          # SQL editor with auto-completion
│   ├── connection_dialog.py   # New/edit connection dialog
│   ├── table_info_dialog.py   # Table info dialog
│   ├── table_data_browser_base.py  # Table browser base logic
│   ├── table_data_browser_widget.py # Tab version
│   ├── table_create_dialog.py # Create table dialog
│   ├── table_modify_dialog.py # Alter table dialog
│   ├── sql_history_dialog.py  # SQL history & saved queries dialog
│   └── main_window.py         # Main window
├── core/                      # Core logic
│   ├── __init__.py
│   ├── connection.py          # Connection manager
│   └── workers.py            # Background workers (connection test, load schema)
└── utils/                    # Utilities
    ├── __init__.py
    └── encryption.py         # Password encryption
```

### Dependencies Installation

```bash
pip install PyQt6 pymysql cryptography appdirs
```

**Optional dependency** (for SQL formatting):
```bash
pip install sqlparse
```

### Run

```bash
python main.py
```

### Build executable (Windows)

Install PyInstaller:
```bash
pip install pyinstaller
```

Build using the provided spec file:
```bash
pyinstaller Syndra-MySQL.spec
```

The executable will be generated in the `dist/` directory.

### Usage

#### Connect to Database
1. Click **➕ New Connection** on the left
2. Fill in connection info: name, host, port, username, password
3. Click **Test Connection** to verify
4. Click **Connect** to connect, you can choose to save the configuration

#### Browse Data
1. After connection succeeds, all databases and tables will be loaded
2. **Double-click** to connect, **double-click** table to open data in new tab
3. Type keywords in bottom search box to filter tables in real-time
4. Supports pagination, adjustable rows per page
5. Click a table to view its structure in the right detail panel
6. Adjust column widths by dragging header dividers
7. Right-click cell to copy cell/row/all data

#### Execute SQL Query
1. A SQL Editor tab is open by default
2. Go to menu **Query → New SQL Query** to open multiple query tabs
3. Enter SQL and click **Execute SQL**
4. SELECT results appear in the table below
5. Click **Format SQL** to beautify SQL (requires `sqlparse`)

### Security
- Passwords are encrypted with Fernet symmetric encryption when saved
- Key derived from a fixed password, meets basic security requirements

### License

MIT

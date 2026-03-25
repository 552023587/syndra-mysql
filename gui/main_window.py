"""
Main Window - The main application window.

This module contains the MainWindow class that is the root of the entire
application UI, coordinating all other components.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QInputDialog, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QMenu, QHeaderView, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QClipboard

from core.connection import ConnectionManager
from core.workers import DatabaseWorker
from gui.connection_dialog import DBConnectionDialog
from gui.sql_editor import SqlTextEdit
from gui.table_info_dialog import TableInfoDialog
from gui.table_data_browser_widget import TableDataBrowserWidget

import pymysql


class MainWindow(QMainWindow):
    """
    The main application window.

    Coordinates all functionality:
    - Connection management (new, edit, delete, connect)
    - Database tree view with tables
    - SQL editor with execution
    - Table browsing in tabs
    - Context menus for operations
    """

    def __init__(self):
        """Initialize the main window and setup the UI."""
        super().__init__()
        self.setWindowTitle("MySQL客户端 - 增强版数据浏览")
        self.setGeometry(100, 100, 1400, 800)

        # Connection manager for saved connections
        self.conn_manager = ConnectionManager()

        # Database connections storage
        self.connections = {}
        self.current_connection = None
        self.current_tunnel = None

        # Setup the complete UI
        self.setup_ui()

    def setup_ui(self):
        """Create and arrange all UI components."""
        # Create main splitter (left tree, right content)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create and setup left panel
        self.setup_left_panel(splitter)

        # Create and setup right panel (tabs)
        self.setup_right_panel(splitter)

        # Set initial splitter sizes
        splitter.setSizes([300, 1100])
        self.setCentralWidget(splitter)

        # Setup menu bar
        self.setup_menubar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def setup_left_panel(self, parent: QSplitter):
        """
        Setup the left panel with connection list and database tree.

        Args:
            parent: The parent splitter widget
        """
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # New connection button
        connect_btn = QPushButton("新建连接")
        connect_btn.clicked.connect(self.add_connection)
        left_layout.addWidget(connect_btn)

        # Saved connections label
        saved_conn_label = QLabel("已保存连接:")
        left_layout.addWidget(saved_conn_label)

        # Saved connections list
        self.saved_conn_list = QListWidget()
        self.saved_conn_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_conn_list.customContextMenuRequested.connect(self.show_context_menu)
        self.refresh_saved_connections()
        left_layout.addWidget(self.saved_conn_list)

        # Database tree view
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel("数据库")
        self.db_tree.itemDoubleClicked.connect(self.tree_item_clicked)
        self.db_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.db_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        left_layout.addWidget(self.db_tree)

        left_panel.setLayout(left_layout)
        parent.addWidget(left_panel)

    def setup_right_panel(self, parent: QSplitter):
        """
        Setup the right panel with tabs for SQL editor and table browsers.

        Args:
            parent: The parent splitter widget
        """
        right_container = QWidget()
        right_container_layout = QVBoxLayout()

        # Create tab widget for multiple open tables
        self.table_tabs = QTabWidget()
        self.table_tabs.setTabsClosable(True)
        self.table_tabs.tabCloseRequested.connect(self.close_tab)

        # Create SQL Editor tab (always open)
        self._create_sql_editor_tab()

        right_container_layout.addWidget(self.table_tabs)
        right_container.setLayout(right_container_layout)
        parent.addWidget(right_container)

    def add_sql_query_tab(self):
        """Add a new SQL query tab."""
        sql_tab, sql_editor, result_table = self._create_sql_query_tab("SQL 查询")
        self.table_tabs.addTab(sql_tab, "SQL 查询")
        self.table_tabs.setCurrentWidget(sql_tab)

    def _create_sql_query_tab(self, title: str):
        """
        Create a new SQL query tab with editor and result table.

        Args:
            title: Tab title

        Returns:
            (sql_tab_widget, sql_editor, result_table)
        """
        sql_tab = QWidget()
        sql_layout = QVBoxLayout()

        # SQL editor label
        sql_label = QLabel("SQL查询:")
        sql_layout.addWidget(sql_label)

        # SQL editor with syntax highlighting and auto-completion
        sql_editor = SqlTextEdit()
        sql_editor.setPlainText("SELECT * FROM ")
        sql_layout.addWidget(sql_editor)

        # Buttons row: Execute + Format SQL
        button_layout = QHBoxLayout()
        execute_btn = QPushButton("执行SQL")
        execute_btn.clicked.connect(lambda: self.execute_sql_in_tab(sql_editor, result_table))
        button_layout.addWidget(execute_btn)

        format_btn = QPushButton("格式化SQL")
        format_btn.clicked.connect(lambda: self.format_sql_in_tab(sql_editor))
        button_layout.addWidget(format_btn)
        button_layout.addStretch()
        sql_layout.addLayout(button_layout)

        # Results table
        result_table = QTableWidget()
        # Enable custom context menu for copy operations
        result_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        result_table.customContextMenuRequested.connect(lambda pos: self.show_result_table_context_menu_for_tab(result_table, pos))
        sql_layout.addWidget(result_table)

        sql_tab.setLayout(sql_layout)
        return sql_tab, sql_editor, result_table

    def _create_sql_editor_tab(self):
        """Create the default SQL Editor tab that stays open permanently."""
        sql_tab, self.sql_editor, self.result_table = self._create_sql_query_tab("SQL Editor")
        self.table_tabs.addTab(sql_tab, "SQL Editor")

    def setup_menubar(self):
        """Setup the top menu bar with file operations."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('文件')

        # New connection action
        new_conn_action = file_menu.addAction('新建连接')
        new_conn_action.triggered.connect(self.add_connection)

        # Save connections action
        save_conns_action = file_menu.addAction('保存连接配置')
        save_conns_action.triggered.connect(self.save_connections_to_file)

        # Query menu
        query_menu = menubar.addMenu('查询')

        # New SQL query tab
        new_query_action = query_menu.addAction('新建SQL查询')
        new_query_action.triggered.connect(self.add_sql_query_tab)

    def refresh_saved_connections(self):
        """Refresh the saved connections list in the left panel."""
        self.saved_conn_list.clear()
        for name in self.conn_manager.connections.keys():
            item = QListWidgetItem(name)
            self.saved_conn_list.addItem(item)

    def show_context_menu(self, position):
        """
        Show context menu for saved connections list.

        Args:
            position: Click position for menu placement
        """
        item = self.saved_conn_list.itemAt(position)
        if not item:
            return

        menu = QMenu()
        connect_action = menu.addAction("连接")
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")

        action = menu.exec(self.saved_conn_list.mapToGlobal(position))

        if action == connect_action:
            self.connect_to_saved(item.text())
        elif action == edit_action:
            self.edit_saved_connection(item.text())
        elif action == delete_action:
            self.delete_saved_connection(item.text())

    def show_tree_context_menu(self, position):
        """
        Show context menu for database tree.

        Different options are shown depending on whether the item is a
        connection, database, or table.

        Args:
            position: Click position for menu placement
        """
        item = self.db_tree.itemAt(position)
        if not item:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        item_type, item_name = item_data

        menu = QMenu()

        if item_type == 'table':
            # Right-click on a table
            view_data_action = menu.addAction("查看数据")
            rename_action = menu.addAction("重命名表")
            delete_action = menu.addAction("删除表")
            design_action = menu.addAction("设计表")

            action = menu.exec(self.db_tree.mapToGlobal(position))

            if action == view_data_action:
                self.view_table_data(item.parent().text(0), item_name)
            elif action == rename_action:
                self.rename_table(item.parent().text(0), item_name)
            elif action == delete_action:
                self.delete_table(item.parent().text(0), item_name)
            elif action == design_action:
                self.design_table(item.parent().text(0), item_name)

        elif item_type == 'database':
            # Right-click on a database
            create_table_action = menu.addAction("创建表")
            delete_db_action = menu.addAction("删除数据库")

            action = menu.exec(self.db_tree.mapToGlobal(position))

            if action == create_table_action:
                self.create_table(item_name)
            elif action == delete_db_action:
                self.delete_database(item_name)

        elif item_type == 'connection':
            # Right-click on a connection
            refresh_action = menu.addAction("刷新")
            disconnect_action = menu.addAction("断开连接")

            action = menu.exec(self.db_tree.mapToGlobal(position))

            if action == refresh_action:
                self.refresh_connection(item_name)
            elif action == disconnect_action:
                self.disconnect_connection(item_name)

    def connect_to_saved(self, name: str):
        """
        Connect to a saved connection.

        Args:
            name: Connection name
        """
        if name in self.conn_manager.connections:
            config = self.conn_manager.connections[name].copy()
            # Use the saved password and connect
            self.create_connection(config)

    def edit_saved_connection(self, name: str):
        """
        Edit an existing saved connection.

        Opens the dialog with current values for editing.

        Args:
            name: Connection name
        """
        if name in self.conn_manager.connections:
            config = self.conn_manager.connections[name].copy()
            dialog = DBConnectionDialog(self, config)
            if dialog.exec() == dialog.DialogCode.Accepted:
                updated_config = dialog.get_config()
                # Update the configuration
                self.conn_manager.connections[name] = updated_config
                self.conn_manager.save_connections()
                self.refresh_saved_connections()

    def delete_saved_connection(self, name: str):
        """
        Delete a saved connection.

        Args:
            name: Connection name
        """
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除连接 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.conn_manager.connections[name]
            self.conn_manager.save_connections()
            self.refresh_saved_connections()

    def add_connection(self):
        """Open dialog to add a new connection."""
        dialog = DBConnectionDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            config = dialog.get_config()
            # Ask user if they want to save the connection
            save_reply = QMessageBox.question(
                self, "保存连接", "是否保存此连接配置？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if save_reply == QMessageBox.StandardButton.Yes:
                # Save with encrypted password
                self.conn_manager.connections[config['name']] = config
                self.conn_manager.save_connections()
                self.refresh_saved_connections()

            self.create_connection(config)

    def create_connection(self, config: dict):
        """
        Create a database connection and load schema in background.

        Args:
            config: Connection configuration
        """
        # Show connecting progress dialog
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate progress
        status_label = QLabel(f"正在连接到 {config['name']}...")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("连接中...")
        msg_box.setText(status_label.text())
        msg_box.setDetailedText(f"主机: {config['host']}:{config['port']}")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg_box.layout().addWidget(progress, 4, 0, 1, msg_box.layout().columnCount())
        msg_box.show()

        # Create background worker
        worker = DatabaseWorker(config)
        worker.result_ready.connect(lambda data: self.on_connection_success(config['name'], data, msg_box))
        worker.error_occurred.connect(lambda error: self.on_connection_error(error, msg_box))
        worker.start()

        # Store worker for later management
        self.connections[config['name']] = {'worker': worker, 'config': config}

    def on_connection_success(self, name: str, data: dict, msg_box: QMessageBox):
        """
        Handle successful database connection.

        Updates the database tree with the new connection's schema.

        Args:
            name: Connection name
            data: Result data containing databases, tables, and connection
            msg_box: Progress message box to close
        """
        # Close progress dialog
        msg_box.close()

        # Clear existing tree content
        self.db_tree.clear()

        # Add connection to tree
        conn_item = QTreeWidgetItem(
            self.db_tree,
            [f"{name} ({data['connection'].host}:{data['connection'].port})"]
        )
        conn_item.setData(0, Qt.ItemDataRole.UserRole, ('connection', name))

        # Add databases and tables
        # Collect all table names for auto-completion
        all_table_names = []
        for db_name in data['databases']:
            db_item = QTreeWidgetItem(conn_item, [db_name])
            db_item.setData(0, Qt.ItemDataRole.UserRole, ('database', db_name))

            for table_name in data['tables'][db_name]:
                table_item = QTreeWidgetItem(db_item, [table_name])
                table_item.setData(0, Qt.ItemDataRole.UserRole, ('table', table_name))
                all_table_names.append(table_name)

        # Expand the connection node
        conn_item.setExpanded(True)

        # Store connection data
        self.connections[name]['data'] = data

        # Set as current connection
        self.current_connection = data['connection']

        # Update SQL editor auto-completion with all table names
        self.sql_editor.set_table_names(all_table_names)

        # Update status bar
        self.status_bar.showMessage(f"已连接到 {name}")

    def on_connection_error(self, error_msg: str, msg_box: QMessageBox):
        """
        Handle connection error.

        Args:
            error_msg: Error message to display
            msg_box: Progress message box to close
        """
        msg_box.close()
        QMessageBox.critical(self, "连接错误", f"连接失败: {error_msg}")
        self.status_bar.showMessage("连接失败")

    def tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Handle double-click on tree item.

        Depending on the item type:
        - Connection: Switches current connection
        - Database: Inserts name into SQL editor
        - Table: Opens table data in new tab

        Args:
            item: The clicked tree item
            column: The clicked column
        """
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        item_type, item_name = item_data

        if item_type == 'connection':
            # Switch current connection to this one
            conn_name = item_name
            if conn_name in self.connections and 'data' in self.connections[conn_name]:
                conn_data = self.connections[conn_name]['data']
                self.current_connection = conn_data['connection']
                self.status_bar.showMessage(f"已切换到连接: {conn_name}")

        elif item_type == 'database':
            # Insert database name into SQL editor if not already there
            current_text = self.sql_editor.toPlainText()
            if 'FROM' not in current_text.upper():
                self.sql_editor.insertPlainText(item_name + '.')

        elif item_type == 'table':
            # Double-click opens table data in new tab
            database_name = item.parent().text(0)
            self.view_table_data(database_name, item_name)

    def close_tab(self, index: int):
        """
        Close a tab.

        The first tab (SQL Editor) cannot be closed.

        Args:
            index: Tab index to close
        """
        # Don't allow closing the first (SQL Editor) tab
        if index == 0:
            return
        # Remove the tab
        self.table_tabs.removeTab(index)

    def view_table_data(self, database: str, table: str):
        """
        Open table data in a new tab.

        If the table is already open, switches to its tab.

        Args:
            database: Database name
            table: Table name
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        # Check if this table is already open in a tab
        tab_title = f"{database}.{table}"
        for i in range(self.table_tabs.count()):
            if self.table_tabs.tabText(i) == tab_title:
                # Already open - just switch to it
                self.table_tabs.setCurrentIndex(i)
                return

        # Create new browser widget and add as a new tab
        browser = TableDataBrowserWidget(self.current_connection, database, table, self.table_tabs)
        self.table_tabs.addTab(browser, tab_title)
        self.table_tabs.setCurrentWidget(browser)

    def rename_table(self, database: str, table: str):
        """
        Rename a table.

        Args:
            database: Database containing the table
            table: Current table name
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        new_name, ok = QInputDialog.getText(
            self, "重命名表", "请输入新的表名:",
            QLineEdit.EchoMode.Normal, table
        )
        if ok and new_name:
            try:
                self.current_connection.select_db(database)
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"ALTER TABLE `{table}` RENAME TO `{new_name}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表已重命名为: {new_name}")
                    # Refresh the database node in the tree
                    self.refresh_database_node(database)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")

    def delete_table(self, database: str, table: str):
        """
        Delete a table from the database.

        Args:
            database: Database containing the table
            table: Table name to delete
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除表 '{table}' 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_connection.select_db(database)
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE `{table}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表 '{table}' 已删除")
                    # Refresh the database node in the tree
                    self.refresh_database_node(database)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def design_table(self, database: str, table: str):
        """
        Show table structure (DESCRIBE).

        Args:
            database: Database containing the table
            table: Table name
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        try:
            self.current_connection.select_db(database)
            with self.current_connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table}`;")
                table_info = cursor.fetchall()

                dialog = TableInfoDialog(table_info, self)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法获取表结构: {str(e)}")

    def create_table(self, database: str):
        """
        Prompt to create a new table (placeholder for future implementation).

        Args:
            database: Database to create table in
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        table_name, ok = QInputDialog.getText(self, "创建表", "请输入表名:")
        if ok and table_name:
            # Full table creation UI not yet implemented
            QMessageBox.information(self, "提示", "表结构设计功能待实现")

    def delete_database(self, database: str):
        """
        Delete an entire database.

        Args:
            database: Database name to delete
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除数据库 '{database}' 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE `{database}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"数据库 '{database}' 已删除")
                    # Refresh the entire connection tree
                    self.refresh_connection_tree()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除数据库失败: {str(e)}")

    def refresh_connection_tree(self):
        """Refresh the entire connection tree for the current connection."""
        if not self.current_connection:
            return

        # Reconnect and reload everything
        conn_name = self.get_current_connection_name()
        if conn_name and conn_name in self.connections:
            config = self.connections[conn_name]['config']
            self.create_connection(config)

    def refresh_database_node(self, database: str):
        """
        Refresh just the tables for a specific database.

        Used after table operations like rename/delete.

        Args:
            database: Database name to refresh
        """
        # Find the database node in the tree
        for i in range(self.db_tree.topLevelItemCount()):
            conn_item = self.db_tree.topLevelItem(i)
            for j in range(conn_item.childCount()):
                db_item = conn_item.child(j)
                if db_item.text(0) == database:
                    # Remove all children (tables)
                    db_item.takeChildren()
                    # Reload tables from database
                    if self.current_connection:
                        try:
                            self.current_connection.select_db(database)
                            with self.current_connection.cursor() as cursor:
                                cursor.execute("SHOW TABLES;")
                                results = cursor.fetchall()
                                for row in results:
                                    table_name = row[0]
                                    table_item = QTreeWidgetItem(db_item, [table_name])
                                    table_item.setData(0, Qt.ItemDataRole.UserRole, ('table', table_name))
                        except Exception as e:
                            print(f"刷新数据库节点失败: {e}")

    def get_current_connection_name(self) -> str | None:
        """
        Get the name of the currently active connection.

        Returns:
            Connection name or None if no current connection
        """
        for name, info in self.connections.items():
            if 'data' in info and info['data']['connection'] == self.current_connection:
                return name
        return None

    def refresh_connection(self, name: str):
        """
        Refresh a connection (reload all databases and tables).

        Args:
            name: Connection name
        """
        if name in self.connections:
            config = self.connections[name]['config']
            self.create_connection(config)

    def disconnect_connection(self, name: str):
        """
        Disconnect and remove a connection from the tree.

        Args:
            name: Connection name
        """
        if name in self.connections:
            if 'worker' in self.connections[name]:
                worker = self.connections[name]['worker']
                worker.close_connection()
            del self.connections[name]
            # Clear tree if this was the current connection
            if self.current_connection:
                # Check if this disconnect removes the last connection
                if not self.connections:
                    self.db_tree.clear()
                    self.current_connection = None
                    self.status_bar.showMessage("就绪")
                else:
                    # TODO: refresh tree - simpler to just recreate
                    self.refresh_connection_tree()

    def execute_sql(self):
        """Execute the SQL query from the editor and display results."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return

        try:
            connection = self.current_connection
            with connection.cursor() as cursor:
                cursor.execute(sql)

                if sql.strip().upper().startswith('SELECT'):
                    # For SELECT queries, display results in table
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]

                    # Update results table
                    self.result_table.setColumnCount(len(columns))
                    self.result_table.setHorizontalHeaderLabels(columns)
                    self.result_table.setRowCount(len(results))

                    for i, row in enumerate(results):
                        for j, value in enumerate(row):
                            item = QTableWidgetItem(str(value) if value is not None else "")
                            self.result_table.setItem(i, j, item)

                    # Allow interactive manual adjustment, stretch last section to fill space
                    header = self.result_table.horizontalHeader()
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                    header.setStretchLastSection(True)

                    self.status_bar.showMessage(f"查询完成，返回 {len(results)} 行结果")
                else:
                    # For non-SELECT queries, commit and show affected rows
                    connection.commit()
                    QMessageBox.information(
                        self, "成功",
                        f"执行完成，影响 {cursor.rowcount} 行"
                    )
                    self.status_bar.showMessage(f"执行完成，影响 {cursor.rowcount} 行")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"SQL执行失败: {str(e)}")
            self.status_bar.showMessage("SQL执行失败")

    def format_sql(self):
        """Format/beautify the SQL in the editor."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return

        try:
            import sqlparse
        except ImportError:
            QMessageBox.warning(
                self, "缺少依赖",
                "请先安装sqlparse库:\n\npip install sqlparse\n\n安装后重启应用即可使用SQL格式化功能。"
            )
            return

        try:
            # Format the SQL with proper indentation
            formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')
            self.sql_editor.setPlainText(formatted.strip())
            self.status_bar.showMessage("SQL格式化完成")
        except Exception as e:
            QMessageBox.critical(self, "格式化失败", f"无法格式化SQL: {str(e)}")
            self.status_bar.showMessage("SQL格式化失败")

    def show_result_table_context_menu(self, position):
        """Show context menu with copy operations for SQL result table."""
        menu = QMenu()

        # Get the cell at the right-click position
        index = self.result_table.indexAt(position)
        row = index.row()
        col = index.column()

        # Add copy operations if a cell is under the cursor
        if index.isValid():
            copy_cell_action = menu.addAction("复制单元格")
            copy_row_action = menu.addAction("复制整行")
            copy_all_action = menu.addAction("复制全部")

        action = menu.exec(self.result_table.mapToGlobal(position))

        if not action:
            return

        if not index.isValid():
            return

        clipboard = QApplication.clipboard()

        if action == copy_cell_action:
            # Copy single cell
            item = self.result_table.item(row, col)
            if item:
                text = item.text()
                clipboard.setText(text)
        elif action == copy_row_action:
            # Copy entire row (tab-separated)
            row_data = []
            col_count = self.result_table.columnCount()
            for c in range(col_count):
                item = self.result_table.item(row, c)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            text = "\t".join(row_data)
            clipboard.setText(text)
        elif action == copy_all_action:
            # Copy entire table (tab-separated)
            all_data = []
            row_count = self.result_table.rowCount()
            col_count = self.result_table.columnCount()
            # Add header
            headers = []
            for c in range(col_count):
                header = self.result_table.horizontalHeaderItem(c)
                if header and header.text():
                    headers.append(header.text())
                else:
                    headers.append("")
            all_data.append("\t".join(headers))
            # Add data rows
            for r in range(row_count):
                row_data = []
                for c in range(col_count):
                    item = self.result_table.item(r, c)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                all_data.append("\t".join(row_data))
            text = "\n".join(all_data)
            clipboard.setText(text)

    def execute_sql_in_tab(self, sql_editor: SqlTextEdit, result_table: QTableWidget):
        """Execute SQL query from a tab and display results in that tab's result table."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        sql = sql_editor.toPlainText().strip()
        if not sql:
            return

        try:
            connection = self.current_connection
            with connection.cursor() as cursor:
                cursor.execute(sql)

                if sql.strip().upper().startswith('SELECT'):
                    # For SELECT queries, display results in table
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]

                    # Update results table
                    result_table.setColumnCount(len(columns))
                    result_table.setHorizontalHeaderLabels(columns)
                    result_table.setRowCount(len(results))

                    for i, row in enumerate(results):
                        for j, value in enumerate(row):
                            item = QTableWidgetItem(str(value) if value is not None else "")
                            result_table.setItem(i, j, item)

                    # Allow interactive manual adjustment, stretch last section to fill space
                    header = result_table.horizontalHeader()
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                    header.setStretchLastSection(True)

                    self.status_bar.showMessage(f"查询完成，返回 {len(results)} 行结果")
                else:
                    # For non-SELECT queries, commit and show affected rows
                    connection.commit()
                    QMessageBox.information(
                        self, "成功",
                        f"执行完成，影响 {cursor.rowcount} 行"
                    )
                    self.status_bar.showMessage(f"执行完成，影响 {cursor.rowcount} 行")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"SQL执行失败: {str(e)}")
            self.status_bar.showMessage("SQL执行失败")

    def format_sql_in_tab(self, sql_editor: SqlTextEdit):
        """Format/beautify the SQL in the given editor."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        sql = sql_editor.toPlainText().strip()
        if not sql:
            return

        try:
            import sqlparse
        except ImportError:
            QMessageBox.warning(
                self, "缺少依赖",
                "请先安装sqlparse库:\n\npip install sqlparse\n\n安装后重启应用即可使用SQL格式化功能。"
            )
            return

        try:
            # Format the SQL with proper indentation
            formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')
            sql_editor.setPlainText(formatted.strip())
            self.status_bar.showMessage("SQL格式化完成")
        except Exception as e:
            QMessageBox.critical(self, "格式化失败", f"无法格式化SQL: {str(e)}")
            self.status_bar.showMessage("SQL格式化失败")

    def show_result_table_context_menu_for_tab(self, result_table: QTableWidget, position):
        """Show context menu with copy operations for a specific result table in a tab."""
        menu = QMenu()

        # Get the cell at the right-click position
        index = result_table.indexAt(position)
        row = index.row()
        col = index.column()

        # Add copy operations if a cell is under the cursor
        if index.isValid():
            copy_cell_action = menu.addAction("复制单元格")
            copy_row_action = menu.addAction("复制整行")
            copy_all_action = menu.addAction("复制全部")

        action = menu.exec(result_table.mapToGlobal(position))

        if not action:
            return

        if not index.isValid():
            return

        clipboard = QApplication.clipboard()

        if action == copy_cell_action:
            # Copy single cell
            item = result_table.item(row, col)
            if item:
                text = item.text()
                clipboard.setText(text)
        elif action == copy_row_action:
            # Copy entire row (tab-separated)
            row_data = []
            col_count = result_table.columnCount()
            for c in range(col_count):
                item = result_table.item(row, c)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            text = "\t".join(row_data)
            clipboard.setText(text)
        elif action == copy_all_action:
            # Copy entire table (tab-separated)
            all_data = []
            row_count = result_table.rowCount()
            col_count = result_table.columnCount()
            # Add header
            headers = []
            for c in range(col_count):
                header = result_table.horizontalHeaderItem(c)
                if header and header.text():
                    headers.append(header.text())
                else:
                    headers.append("")
            all_data.append("\t".join(headers))
            # Add data rows
            for r in range(row_count):
                row_data = []
                for c in range(col_count):
                    item = result_table.item(r, c)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                all_data.append("\t".join(row_data))
            text = "\n".join(all_data)
            clipboard.setText(text)

    def save_connections_to_file(self):
        """Manually save connection configurations to disk."""
        self.conn_manager.save_connections()
        QMessageBox.information(self, "保存成功", "连接配置已保存到文件")

    def closeEvent(self, event):
        """
        Handle window close event.

        Automatically saves connection configurations before exiting.

        Args:
            event: Close event
        """
        # Save connections when closing the application
        self.conn_manager.save_connections()
        event.accept()

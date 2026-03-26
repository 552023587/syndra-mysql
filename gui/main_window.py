"""
Main Window - The main application window.

This module contains the MainWindow class that is the root of the entire
application UI, coordinating all other components.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QInputDialog, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QMenu, QHeaderView, QStatusBar, QApplication,
    QTextEdit, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QClipboard

from core.connection import ConnectionManager
from core.workers import DatabaseWorker
from gui.connection_dialog import DBConnectionDialog
from gui.sql_editor import SqlTextEdit
from gui.table_info_dialog import TableInfoDialog
from gui.table_data_browser_widget import TableDataBrowserWidget
from gui.table_create_dialog import TableCreateDialog
from gui.table_modify_dialog import TableModifyDialog
from gui.sql_history_dialog import SqlHistoryDialog

import os
import logging
import appdirs

import pymysql

logger = logging.getLogger(__name__)


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
        self.setWindowTitle("🐬 MySQL 客户端 - Syndra")
        self.setGeometry(100, 100, 1400, 800)

        # Connection manager for saved connections
        self.conn_manager = ConnectionManager()

        # Database connections storage
        self.connections = {}
        self.current_connection = None
        self.current_tunnel = None

        # SQL history and saved queries file
        app_dir = appdirs.user_data_dir("syndra-mysql", "syndra")
        self.sql_history_file = os.path.join(app_dir, "sql_history.json")
        # Settings file for layout persistence
        self.settings_file = os.path.join(app_dir, "settings.json")

        # Transaction settings - default to auto-commit for backward compatibility
        self.auto_commit = True

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
        self.central_splitter = splitter
        self.setCentralWidget(splitter)

        # Setup menu bar
        self.setup_menubar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # Add transaction status indicator to status bar
        self.transaction_label = QLabel("自动提交")
        self.transaction_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding-right: 10px;
            }
        """)
        self.status_bar.addPermanentWidget(self.transaction_label)

        # Initial tree population with all saved connections
        self.refresh_connection_tree()

        # Load and restore saved layout settings
        self.load_layout_settings()

    def setup_left_panel(self, parent: QSplitter):
        """
        Setup the left panel with connection tree (navicat-style).

        Args:
            parent: The parent splitter widget
        """
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Top button bar
        button_layout = QHBoxLayout()
        # New connection button
        connect_btn = QPushButton(" ➕ 新建连接 ")
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #337ab7;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #286090;
            }
            QPushButton:pressed {
                background-color: #204d74;
            }
        """)
        connect_btn.clicked.connect(self.add_connection)
        button_layout.addWidget(connect_btn)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        left_layout.addSpacing(5)

        # Database tree view - navicat-style: connections as top-level nodes
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderHidden(True)
        self.db_tree.itemDoubleClicked.connect(self.tree_item_clicked)
        self.db_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.db_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        left_layout.addWidget(self.db_tree)

        # Table search/filter box at bottom
        from PyQt6.QtWidgets import QLineEdit
        self.table_filter = QLineEdit()
        self.table_filter.setPlaceholderText("搜索")
        self.table_filter.textChanged.connect(self.filter_tree_tables)
        left_layout.addWidget(self.table_filter)

        left_panel.setLayout(left_layout)
        parent.addWidget(left_panel)

    def setup_right_panel(self, parent: QSplitter):
        """
        Setup the right panel with tabs for SQL editor and table browsers, plus detail sidebar.

        Args:
            parent: The parent splitter widget
        """
        # Create nested splitter: tabs on left, detail panel on right
        right_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tab container
        tab_container = QWidget()
        tab_layout = QVBoxLayout()

        # Create tab widget for multiple open tables
        self.table_tabs = QTabWidget()
        self.table_tabs.setTabsClosable(True)
        self.table_tabs.tabCloseRequested.connect(self.close_tab)
        # Enable custom context menu for tab bar
        self.table_tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_tabs.tabBar().customContextMenuRequested.connect(self.show_tab_bar_context_menu)

        # Create SQL Editor tab (always open)
        self._create_sql_editor_tab()

        tab_layout.addWidget(self.table_tabs)
        tab_container.setLayout(tab_layout)
        right_splitter.addWidget(tab_container)

        # Create detail panel for table information
        self.detail_panel = QWidget()
        detail_layout = QVBoxLayout()

        detail_label = QLabel("表详情")
        detail_layout.addWidget(detail_label)

        # Use read-only text edit to display CREATE TABLE statement
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)

        # Table information summary
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        detail_layout.addWidget(self.info_label)

        self.detail_panel.setLayout(detail_layout)
        right_splitter.addWidget(self.detail_panel)

        # Set initial sizes: 4/5 for tabs, 1/5 for detail panel
        total_width = parent.size().width() if parent.size().width() > 0 else 1100
        right_splitter.setSizes([int(total_width * 0.8), int(total_width * 0.2)])

        # Store reference for later use
        self.right_splitter = right_splitter

        parent.addWidget(right_splitter)

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

        # Show saved queries
        saved_queries_action = query_menu.addAction('📝 历史与保存查询')
        saved_queries_action.triggered.connect(self.show_saved_queries)

        # View menu
        view_menu = menubar.addMenu('视图')

        # Toggle dark theme
        self.dark_theme_action = view_menu.addAction('🌙 暗色主题')
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.setChecked(False)
        self.dark_theme_action.triggered.connect(self.toggle_dark_theme)

        # Store current theme
        self.dark_theme_enabled = False

        # Saved queries
        saved_queries_action = query_menu.addAction('📝 查看保存的查询')
        saved_queries_action.triggered.connect(self.show_saved_queries)

        # Transaction menu
        transaction_menu = menubar.addMenu('事务')

        # Toggle auto-commit
        self.auto_commit_action = QAction('自动提交', self)
        self.auto_commit_action.setCheckable(True)
        self.auto_commit_action.setChecked(self.auto_commit)
        self.auto_commit_action.triggered.connect(self.toggle_auto_commit)
        transaction_menu.addAction(self.auto_commit_action)

        transaction_menu.addSeparator()

        # Manual commit and rollback
        commit_action = QAction('✔ 提交事务', self)
        commit_action.triggered.connect(self.commit_transaction)
        transaction_menu.addAction(commit_action)

        rollback_action = QAction('✖ 回滚事务', self)
        rollback_action.triggered.connect(self.rollback_transaction)
        transaction_menu.addAction(rollback_action)


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
            menu.addSeparator()
            modify_structure_action = menu.addAction("修改表结构")
            rename_action = menu.addAction("重命名表")
            delete_action = menu.addAction("删除表")

            action = menu.exec(self.db_tree.mapToGlobal(position))

            if action == view_data_action:
                self.view_table_data(item.parent().text(0), item_name)
            elif action == modify_structure_action:
                self.modify_table_structure(item.parent().text(0), item_name)
            elif action == rename_action:
                self.rename_table(item.parent().text(0), item_name)
            elif action == delete_action:
                self.delete_table(item.parent().text(0), item_name)

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
            new_db_action = menu.addAction("新建数据库")
            menu.addSeparator()
            edit_action = menu.addAction("编辑连接")
            disconnect_action = menu.addAction("断开连接")

            action = menu.exec(self.db_tree.mapToGlobal(position))

            if action == refresh_action:
                self.refresh_connection(item_name)
            elif action == new_db_action:
                self.create_database(item_name)
            elif action == edit_action:
                self.edit_saved_connection(item_name)
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
                # If already connected, disconnect the old connection first
                if name in self.connections:
                    # Close SSH tunnel if exists
                    if 'tunnel' in self.connections[name]:
                        tunnel = self.connections[name]['tunnel']
                        if tunnel:
                            tunnel.stop()
                    if 'worker' in self.connections[name]:
                        worker = self.connections[name]['worker']
                        worker.close_connection()
                    del self.connections[name]
                self.refresh_connection_tree()

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
            # Also remove from connected connections if it was connected
            if name in self.connections:
                del self.connections[name]
            self.conn_manager.save_connections()
            self.refresh_connection_tree()

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
                self.refresh_connection_tree()

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

        # Store connection data
        self.connections[name]['data'] = data

        # Set as current connection
        self.current_connection = data['connection']

        # Store SSH tunnel if exists
        tunnel = data.get('tunnel')
        self.current_tunnel = tunnel
        self.connections[name]['tunnel'] = tunnel

        # Refresh the entire tree to show all connections with the newly connected one
        self.refresh_connection_tree()

        # Collect all table names from all connected connections for auto-completion
        all_table_names = []
        all_column_names = []

        # Iterate through all connected connections and collect tables/columns
        # Column names are already collected in worker thread for the new connection
        for conn_name in self.connections:
            if 'data' not in self.connections[conn_name]:
                continue
            conn_data = self.connections[conn_name]['data']

            # Add all table names
            for db_name in conn_data['tables']:
                for table_name in conn_data['tables'][db_name]:
                    if table_name not in all_table_names:
                        all_table_names.append(table_name)

            # Add column names from worker result for this connection
            if 'all_column_names' in conn_data:
                for col_name in conn_data['all_column_names']:
                    if col_name not in all_column_names:
                        all_column_names.append(col_name)

        # Update SQL editor auto-completion with all table and column names
        self.sql_editor.set_table_names(all_table_names)
        self.sql_editor.set_column_names(all_column_names)

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
        logger.error(f"Database connection failed: {error_msg}")
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
                # Toggle expansion on double-click
                item.setExpanded(not item.isExpanded())
            else:
                # Not connected yet - double-click to connect
                if conn_name in self.conn_manager.connections:
                    config = self.conn_manager.connections[conn_name].copy()
                    self.create_connection(config)

        elif item_type == 'database':
            # Insert database name into SQL editor if not already there
            current_text = self.sql_editor.toPlainText()
            if 'FROM' not in current_text.upper():
                self.sql_editor.insertPlainText(item_name + '.')

        elif item_type == 'table':
            # Single-click shows table details in detail panel
            database_name = item.parent().text(0)
            self.load_table_details(database_name, item_name)
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
        # Pass auto-commit setting to browser logic
        browser.logic.auto_commit = self.auto_commit
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
                    if self.auto_commit:
                        self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表已重命名为: {new_name}")
                    # Refresh the database node in the tree
                    self.refresh_database_node(database)
            except Exception as e:
                logger.error(f"Rename table failed: {str(e)}")
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
                    if self.auto_commit:
                        self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表 '{table}' 已删除")
                    # Refresh the database node in the tree
                    self.refresh_database_node(database)
            except Exception as e:
                logger.error(f"Delete table failed: {str(e)}")
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
            logger.error(f"Failed to get table structure: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法获取表结构: {str(e)}")

    def modify_table_structure(self, database: str, table: str):
        """
        Open the table structure modification dialog.

        Args:
            database: Database containing the table
            table: Table name to modify
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        dialog = TableModifyDialog(database, table, self.current_connection, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the database node
            self.refresh_database_node(database)

    def create_table(self, database: str):
        """
        Open the visual table create dialog to design a new table.

        Args:
            database: Database to create table in
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        dialog = TableCreateDialog(database, self.current_connection, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the database node tables
            self.refresh_database_node(database)


    def create_database(self, connection_name: str):
        """
        Create a new database on the connection.

        Args:
            connection_name: Connection name where to create the database
        """
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        db_name, ok = QInputDialog.getText(self, "新建数据库", "请输入数据库名称:")
        if ok and db_name:
            try:
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE `{db_name}`;")
                    if self.auto_commit:
                        self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"数据库 '{db_name}' 已创建")
                    # Refresh the entire connection tree
                    self.refresh_connection_tree()
            except Exception as e:
                logger.error(f"Create database failed: {str(e)}")
                QMessageBox.critical(self, "错误", f"创建数据库失败: {str(e)}")

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
                    if self.auto_commit:
                        self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"数据库 '{database}' 已删除")
                    # Refresh the entire connection tree
                    self.refresh_connection_tree()
            except Exception as e:
                logger.error(f"Delete database failed: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除数据库失败: {str(e)}")

    def refresh_connection_tree(self):
        """Refresh the entire connection tree showing all saved connections."""
        self.db_tree.clear()

        # Add all saved connections as top-level nodes
        for conn_name in self.conn_manager.connections:
            if conn_name in self.connections:
                # Already connected
                conn_info = self.connections[conn_name]
                data = conn_info['data']
                conn_item = QTreeWidgetItem(
                    self.db_tree,
                    [f"🔌 {conn_name} ({data['connection'].host}:{data['connection'].port})"]
                )
                conn_item.setData(0, Qt.ItemDataRole.UserRole, ('connection', conn_name))
                conn_item.setExpanded(True)

                # Add databases
                for db_name in data['databases']:
                    db_item = QTreeWidgetItem(conn_item, [db_name])
                    db_item.setData(0, Qt.ItemDataRole.UserRole, ('database', db_name))
                    # Add tables
                    for table_name in data['tables'][db_name]:
                        table_item = QTreeWidgetItem(db_item, [table_name])
                        table_item.setData(0, Qt.ItemDataRole.UserRole, ('table', table_name))
            else:
                # Not connected yet
                config = self.conn_manager.connections[conn_name]
                conn_item = QTreeWidgetItem(
                    self.db_tree,
                    [f"🔌 {conn_name} ({config['host']}:{config['port']})"]
                )
                conn_item.setData(0, Qt.ItemDataRole.UserRole, ('connection', conn_name))

    def refresh_connection(self, connection_name: str):
        """Refresh a specific connection (reconnect and reload databases)."""
        if connection_name in self.connections:
            config = self.connections[connection_name]['config']
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
            # Close SSH tunnel if exists
            if 'tunnel' in self.connections[name]:
                tunnel = self.connections[name]['tunnel']
                if tunnel:
                    tunnel.stop()
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

    def filter_tree_tables(self):
        """
        Filter tree nodes to show only tables matching search text.

        Hides tables that don't match the search text. When search is empty,
        shows all tables. Also ensures parent nodes (connection, database) are
        visible if they have at least one matching child.
        """
        search_text = self.table_filter.text().strip().lower()

        # Iterate all top-level items (connections)
        for i in range(self.db_tree.topLevelItemCount()):
            conn_item = self.db_tree.topLevelItem(i)
            conn_has_match = False

            # If no search text, show everything
            if not search_text:
                conn_item.setHidden(False)
                # Show all children
                for j in range(conn_item.childCount()):
                    db_item = conn_item.child(j)
                    db_item.setHidden(False)
                    for k in range(db_item.childCount()):
                        table_item = db_item.child(k)
                        table_item.setHidden(False)
                continue

            # With search text - check each database
            for j in range(conn_item.childCount()):
                db_item = conn_item.child(j)
                db_has_match = False

                # Check each table in this database
                for k in range(db_item.childCount()):
                    table_item = db_item.child(k)
                    table_name = table_item.text(0).lower()
                    if search_text in table_name:
                        table_item.setHidden(False)
                        db_has_match = True
                        conn_has_match = True
                    else:
                        table_item.setHidden(True)

                # Show database if it has any matching tables
                db_item.setHidden(not db_has_match)
                if db_has_match:
                    db_item.setExpanded(True)
                    conn_item.setExpanded(True)

            # Show connection if it has any match
            conn_item.setHidden(not conn_has_match)

        # Update status
        if search_text:
            self.status_bar.showMessage(f"筛选中: {search_text}")
        else:
            self.status_bar.showMessage("就绪")

    def execute_sql(self):
        """Execute the SQL query from the editor and display results."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return

        # Add to SQL history
        dialog = SqlHistoryDialog(self.sql_history_file, self)
        dialog.add_sql_to_history(sql)

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
                            # Make cells editable
                            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                            self.result_table.setItem(i, j, item)

                    # Allow interactive manual adjustment, stretch last section to fill space
                    header = self.result_table.horizontalHeader()
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                    header.setStretchLastSection(True)

                    self.status_bar.showMessage(f"查询完成，返回 {len(results)} 行结果")
                else:
                    # For non-SELECT queries, commit and show affected rows
                    if self.auto_commit:
                        connection.commit()
                    QMessageBox.information(
                        self, "成功",
                        f"执行完成，影响 {cursor.rowcount} 行"
                    )
                    self.status_bar.showMessage(f"执行完成，影响 {cursor.rowcount} 行")

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
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
            logger.error(f"SQL formatting failed: {str(e)}")
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
                    if self.auto_commit:
                        connection.commit()
                    QMessageBox.information(
                        self, "成功",
                        f"执行完成，影响 {cursor.rowcount} 行"
                    )
                    self.status_bar.showMessage(f"执行完成，影响 {cursor.rowcount} 行")

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
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
            logger.error(f"SQL formatting failed: {str(e)}")
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

    def show_saved_queries(self):
        """Show the SQL history and saved queries dialog."""
        dialog = SqlHistoryDialog(self.sql_history_file, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_sql:
            # Open a new query tab and put the SQL in it
            sql_tab, sql_editor, result_table = self._create_sql_query_tab("SQL 查询")
            sql_editor.setPlainText(dialog.selected_sql)
            self.table_tabs.addTab(sql_tab, "SQL 查询")
            self.table_tabs.setCurrentWidget(sql_tab)

    def toggle_dark_theme(self):
        """Toggle dark theme on/off."""
        self.dark_theme_enabled = self.dark_theme_action.isChecked()
        if self.dark_theme_enabled:
            # Apply dark theme stylesheet
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #cccccc;
            }
            QLineEdit {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #cccccc;
                selection-background-color: #505050;
            }
            QTableWidget {
                background-color: #3c3f41;
                color: #cccccc;
                gridline-color: #555;
            }
            QTableWidget QHeaderView::section {
                background-color: #505050;
                color: #cccccc;
                border: 1px solid #666;
            }
            QTableWidget::item:selected {
                background-color: #4080c0;
            }
            QTreeWidget {
                background-color: #3c3f41;
                color: #cccccc;
            }
            QTreeWidget::item:selected {
                background-color: #4080c0;
            }
            QListWidget {
                background-color: #3c3f41;
                color: #cccccc;
            }
            QListWidget::item:selected {
                background-color: #4080c0;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #cccccc;
            }
            QPushButton {
                background-color: #505050;
                color: #cccccc;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QLabel {
                color: #cccccc;
            }
            QMenu {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QSpinBox {
                background-color: #3c3f41;
                color: #cccccc;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #cccccc;
            }
            QTextEdit {
                background-color: #3c3f41;
                color: #cccccc;
            }
            QHeaderView {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #505050;
                color: #cccccc;
                border: 1px solid #666;
                padding: 6px 12px;
            }
            QTabBar::tab:selected {
                background-color: #3c3f41;
            }
            QSplitter::handle {
                background-color: #555;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606060;
            }
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
            }
            QScrollBar::handle:horizontal {
                background-color: #505050;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #606060;
            }
            QMessageBox {
                background-color: #2b2b2b;
            }
            QMessageBox QLabel {
                color: #cccccc;
            }
            """
            self.setStyleSheet(dark_style)
        else:
            # Clear stylesheet to use default light theme
            self.setStyleSheet("")

    def closeEvent(self, event):
        """
        Handle window close event.

        Automatically saves connection configurations before exiting.

        Args:
            event: Close event
        """
        # Save connections when closing the application
        self.conn_manager.save_connections()
        # Save layout settings
        self.save_layout_settings()
        event.accept()

    def show_tab_bar_context_menu(self, position):
        """
        Show context menu for tab bar with close options.

        Args:
            position: Click position for menu placement
        """
        # Get the tab index at the clicked position
        tab_index = self.table_tabs.tabBar().tabAt(position)
        if tab_index < 0:
            return

        menu = QMenu()

        close_all_action = menu.addAction("关闭所有")
        close_right_action = menu.addAction("关闭最右")
        close_left_action = menu.addAction("关闭最左")

        action = menu.exec(self.table_tabs.tabBar().mapToGlobal(position))

        if action == close_all_action:
            self.close_all_tabs()
        elif action == close_right_action:
            self.close_tabs_to_right(tab_index)
        elif action == close_left_action:
            self.close_tabs_to_left(tab_index)

    def close_all_tabs(self):
        """Close all tabs except the first SQL Editor tab."""
        # Close from last to first to avoid index shifting issues
        for index in range(self.table_tabs.count() - 1, 0, -1):
            self.table_tabs.removeTab(index)

    def close_tabs_to_right(self, current_index: int):
        """
        Close all tabs to the right of the current tab.

        Args:
            current_index: Current tab index
        """
        # Close from last to current_index + 1
        for index in range(self.table_tabs.count() - 1, current_index, -1):
            self.table_tabs.removeTab(index)

    def close_tabs_to_left(self, current_index: int):
        """
        Close all tabs to the left of the current tab, keeping the first SQL Editor tab.

        Args:
            current_index: Current tab index
        """
        # Close from current_index - 1 down to 1 (don't close index 0)
        for index in range(current_index - 1, 0, -1):
            self.table_tabs.removeTab(index)

    def load_table_details(self, database: str, table: str):
        """
        Load table details including CREATE TABLE statement and table size.

        Args:
            database: Database name containing the table
            table: Table name
        """
        if not self.current_connection:
            self.detail_text.clear()
            self.info_label.setText("请先连接数据库")
            return

        try:
            self.current_connection.select_db(database)

            # Get CREATE TABLE statement
            create_sql = ""
            with self.current_connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{database}`.`{table}`;")
                result = cursor.fetchone()
                if result and len(result) >= 2:
                    create_sql = result[1]

            # Get table size information from information_schema
            table_rows = 0
            data_size = 0
            index_size = 0
            try:
                with self.current_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH
                        FROM information_schema.TABLES
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    """, (database, table))
                    result = cursor.fetchone()
                    if result:
                        table_rows = result[0] or 0
                        data_size = result[1] or 0
                        index_size = result[2] or 0
            except Exception as e:
                # Fall back to COUNT(*) if information_schema access fails
                try:
                    with self.current_connection.cursor() as cursor:
                        cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table}`")
                        result = cursor.fetchone()
                        if result:
                            table_rows = result[0]
                except Exception:
                    pass

            # Get foreign keys
            foreign_keys = []
            try:
                with self.current_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            CONSTRAINT_NAME,
                            COLUMN_NAME,
                            REFERENCED_TABLE_NAME,
                            REFERENCED_COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = %s
                          AND TABLE_NAME = %s
                          AND REFERENCED_TABLE_NAME IS NOT NULL
                        ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
                    """, (database, table))
                    fk_result = cursor.fetchall()

                    # Group by constraint name
                    fk_map = {}
                    for constraint_name, col_name, ref_table, ref_col in fk_result:
                        if constraint_name not in fk_map:
                            fk_map[constraint_name] = {
                                'cols': [],
                                'ref_table': ref_table,
                                'ref_cols': []
                            }
                        fk_map[constraint_name]['cols'].append(col_name)
                        fk_map[constraint_name]['ref_cols'].append(ref_col)

                    for name, data in fk_map.items():
                        cols = ", ".join(data['cols'])
                        ref = f"{data['ref_table']}({', '.join(data['ref_cols'])})"
                        foreign_keys.append(f"• {name}: {cols} → {ref}")
            except Exception:
                pass

            # Format size to human-readable format
            def format_size(size_bytes: int) -> str:
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

            total_size = data_size + index_size
            info_text = f"""表: {database}.{table}
行数: {table_rows:,}
数据大小: {format_size(data_size)}
索引大小: {format_size(index_size)}
总大小: {format_size(total_size)}"""

            if foreign_keys:
                info_text += "\n\n外键关系:\n" + "\n".join(foreign_keys)

            # Update UI
            self.detail_text.setPlainText(create_sql)
            self.info_label.setText(info_text)
            self.status_bar.showMessage(f"已加载表详情: {database}.{table}")

        except Exception as e:
            self.detail_text.clear()
            self.info_label.setText(f"获取详情失败: {str(e)}")

    def keyPressEvent(self, event):
        """
        Handle key press events for global shortcuts.

        Ctrl+F: Focus and select content in table search bar.
        """
        # Check for Ctrl+F
        if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Focus the table filter search box
            self.table_filter.setFocus()
            # Select all existing text for easy overwriting
            self.table_filter.selectAll()
            event.accept()
            return

        # Let parent handle other keys
        super().keyPressEvent(event)

    def save_layout_settings(self):
        """Save current layout (splitter positions) and theme to settings file."""
        try:
            # Get current sizes from both splitters
            central_sizes = self.central_splitter.sizes()
            right_sizes = self.right_splitter.sizes()

            settings = {
                'central_splitter_sizes': central_sizes,
                'right_splitter_sizes': right_sizes,
                'dark_theme_enabled': self.dark_theme_enabled
            }

            # Ensure directory exists
            app_dir = appdirs.user_data_dir("syndra-mysql", "syndra")
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存布局设置失败: {e}")

    def load_layout_settings(self):
        """Load and restore saved layout settings and theme from settings file."""
        if not os.path.exists(self.settings_file):
            return  # No settings file, use defaults

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                import json
                settings = json.load(f)

            # Restore main splitter sizes
            if 'central_splitter_sizes' in settings and len(settings['central_splitter_sizes']) == 2:
                self.central_splitter.setSizes(settings['central_splitter_sizes'])

            # Restore right nested splitter sizes
            if 'right_splitter_sizes' in settings and len(settings['right_splitter_sizes']) == 2:
                self.right_splitter.setSizes(settings['right_splitter_sizes'])

            # Restore theme setting
            if 'dark_theme_enabled' in settings:
                self.dark_theme_enabled = settings['dark_theme_enabled']
                self.dark_theme_action.setChecked(self.dark_theme_enabled)
                if self.dark_theme_enabled:
                    self.toggle_dark_theme()
        except Exception as e:
            print(f"加载布局设置失败: {e}")

    def toggle_auto_commit(self):
        """Toggle between auto-commit and manual transaction mode."""
        self.auto_commit = self.auto_commit_action.isChecked()

        if self.auto_commit:
            self.transaction_label.setText("自动提交")
            self.transaction_label.setStyleSheet("QLabel { color: #666; padding-right: 10px; }")
        else:
            self.transaction_label.setText("⚠ 手动事务")
            self.transaction_label.setStyleSheet("QLabel { color: #d9534f; padding-right: 10px; font-weight: bold; }")

            # If entering manual mode and have active connection,提示用户
            if self.current_connection:
                self.status_bar.showMessage("已进入手动事务模式，请手动提交或回滚更改")

    def commit_transaction(self):
        """Commit current active transaction."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        try:
            self.current_connection.commit()
            self.status_bar.showMessage("事务已提交")
            QMessageBox.information(self, "成功", "事务已成功提交")
        except Exception as e:
            logger.error(f"Transaction commit failed: {str(e)}")
            QMessageBox.critical(self, "错误", f"提交失败: {str(e)}")

    def rollback_transaction(self):
        """Roll back current active transaction."""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return

        try:
            reply = QMessageBox.question(
                self, "确认回滚",
                "确定要回滚当前未提交的所有更改吗？\n此操作不可撤销！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.current_connection.rollback()
                self.status_bar.showMessage("事务已回滚")
                QMessageBox.information(self, "成功", "事务已回滚")
        except Exception as e:
            logger.error(f"Transaction rollback failed: {str(e)}")
            QMessageBox.critical(self, "错误", f"回滚失败: {str(e)}")

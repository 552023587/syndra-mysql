"""
Table Data Browser Base - Shared logic for table data browsing.

This module contains all the shared business logic and widget creation
for both dialog and widget versions of the table browser.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QTableWidget, QTableWidgetItem, QMenu, QInputDialog,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from pymysql import Connection
from gui.table_info_dialog import TableInfoDialog


class TableDataBrowserLogic:
    """
    Contains all shared logic for table data browsing with pagination.

    This class doesn't inherit from any Qt class, it just creates widgets
    and holds the business logic. The dialog/widget containers use this
    class to handle all the functionality.
    """

    def __init__(self, connection: Connection, database: str, table: str):
        """
        Initialize the table browser logic.

        Args:
            connection: Active pymysql connection
            database: Database name containing the table
            table: Table name to browse
        """
        self.connection = connection
        self.database = database
        self.table = table
        self.current_page = 0
        self.page_size = 20
        self.total_rows = 0
        self.current_data = []

        # Create all widgets
        self._create_pagination_controls()
        self._create_table_widget()

    def _create_pagination_controls(self):
        """Create all pagination control widgets."""
        # Pagination buttons and displays
        self.first_btn = QPushButton("首页")
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.last_btn = QPushButton("末页")
        self.page_label = QLabel("第 1 页")
        self.total_pages_label = QLabel("共 0 页")
        self.page_input = QSpinBox()
        self.page_input.setRange(1, 1)
        self.page_input.setValue(1)
        self.go_btn = QPushButton("跳转")
        self.page_size_combo = QSpinBox()
        self.page_size_combo.setRange(10, 100)
        self.page_size_combo.setValue(20)
        self.page_size_combo.setSuffix(" 条/页")

        # Connect signals
        self.first_btn.clicked.connect(self.first_page)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.last_btn.clicked.connect(self.last_page)
        self.go_btn.clicked.connect(self.go_to_page)
        self.page_input.returnPressed.connect(self.go_to_page)
        self.page_size_combo.valueChanged.connect(self.change_page_size)

    def _create_table_widget(self):
        """Create the data table widget with context menu."""
        self.table_widget = QTableWidget()
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # context menu is connected by the container

    def setup_layout(self, layout: QVBoxLayout):
        """
        Add all widgets to the container's layout.

        Args:
            layout: The VBoxLayout to add widgets to
        """
        # Create pagination layout
        pagination_layout = QHBoxLayout()
        pagination_layout.addWidget(self.first_btn)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.total_pages_label)
        pagination_layout.addWidget(QLabel("跳转到:"))
        pagination_layout.addWidget(self.page_input)
        pagination_layout.addWidget(self.go_btn)
        pagination_layout.addWidget(QLabel("每页显示:"))
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(self.last_btn)
        pagination_layout.addStretch()

        # Add to container layout
        layout.addLayout(pagination_layout)
        layout.addWidget(self.table_widget)

    def change_page_size(self):
        """Change the number of rows per page and reload data."""
        self.page_size = self.page_size_combo.value()

        # Recalculate current page to avoid out-of-bounds
        if self.total_rows > 0:
            total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = total_pages - 1
                if self.current_page < 0:
                    self.current_page = 0
        else:
            self.current_page = 0

        self.load_data()

    def load_data(self):
        """Load the current page of data from the database."""
        try:
            self.connection.select_db(self.database)
            with self.connection.cursor() as cursor:
                # Get total number of rows
                cursor.execute(f"SELECT COUNT(*) FROM `{self.table}`;")
                self.total_rows = cursor.fetchone()[0]

                # Calculate total pages
                total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
                self.page_input.setMaximum(total_pages)
                self.total_pages_label.setText(f"共 {total_pages} 页")

                # Get current page data with LIMIT/OFFSET
                offset = self.current_page * self.page_size
                cursor.execute(f"SELECT * FROM `{self.table}` LIMIT {self.page_size} OFFSET {offset};")
                self.current_data = cursor.fetchall()

                # Get column names from cursor description
                columns = [desc[0] for desc in cursor.description]

                # Update the table display
                self.update_table(columns, self.current_data)

                # Update page display
                self.page_label.setText(f"第 {self.current_page + 1} 页")
                self.page_input.setValue(self.current_page + 1)

                # Update button enabled states
                self.first_btn.setEnabled(self.current_page > 0)
                self.prev_btn.setEnabled(self.current_page > 0)
                self.next_btn.setEnabled((self.current_page + 1) * self.page_size < self.total_rows)
                self.last_btn.setEnabled((self.current_page + 1) * self.page_size < self.total_rows)

        except Exception as e:
            # The parent widget will be used for the message box
            if hasattr(self, 'parent_widget'):
                parent = self.parent_widget
            else:
                parent = None
            QMessageBox.critical(parent, "错误", f"加载数据失败: {str(e)}")

    def update_table(self, columns: list, data: list):
        """
        Update the table widget with new data.

        Args:
            columns: List of column names
            data: List of row data tuples
        """
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.setRowCount(len(data))

        # Fill table with data
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                # Make cells read-only (browsing only)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, j, item)

        # Allow interactive manual adjustment, still stretch to fill available space initially
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Stretch the last section to fill remaining space
        header.setStretchLastSection(True)

    def first_page(self):
        """Go to the first page."""
        if self.current_page != 0:
            self.current_page = 0
            self.load_data()

    def prev_page(self):
        """Go to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        """Go to the next page."""
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_data()

    def last_page(self):
        """Go to the last page."""
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.current_page != total_pages - 1:
            self.current_page = total_pages - 1
            self.load_data()

    def go_to_page(self):
        """Jump to a specific page based on user input."""
        target_page = self.page_input.value() - 1
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size

        if 0 <= target_page < total_pages:
            self.current_page = target_page
            self.load_data()
        else:
            if hasattr(self, 'parent_widget'):
                parent = self.parent_widget
            else:
                parent = None
            QMessageBox.warning(parent, "警告", f"页码超出范围 (1-{total_pages})")

    def rename_table(self, parent_widget):
        """
        Handle rename table operation.

        Args:
            parent_widget: The parent widget for dialogs
        """
        new_name, ok = QInputDialog.getText(
            parent_widget,
            "重命名表", "请输入新的表名:",
            QLineEdit.EchoMode.Normal, self.table
        )
        if ok and new_name:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"ALTER TABLE `{self.table}` RENAME TO `{new_name}`;")
                    self.connection.commit()
                    QMessageBox.information(
                        parent_widget,
                        "成功", f"表已重命名为: {new_name}"
                    )
                    self.table = new_name
                    # Reload data with new table name
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(
                    parent_widget,
                    "错误", f"重命名失败: {str(e)}"
                )

    def delete_table(self, parent_widget):
        """
        Handle delete table operation.

        Args:
            parent_widget: The parent widget for dialogs
        """
        reply = QMessageBox.question(
            parent_widget,
            "确认删除",
            f"确定要删除表 '{self.table}' 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE `{self.table}`;")
                    self.connection.commit()
                    QMessageBox.information(
                        parent_widget,
                        "成功", f"表 '{self.table}' 已删除"
                    )
            except Exception as e:
                QMessageBox.critical(
                    parent_widget,
                    "错误", f"删除失败: {str(e)}"
                )

    def design_table(self, parent_widget):
        """
        Show table structure information.

        Args:
            parent_widget: The parent widget for dialogs
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{self.table}`;")
                table_info = cursor.fetchall()

                dialog = TableInfoDialog(table_info, parent_widget)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "错误", f"无法获取表结构: {str(e)}"
            )

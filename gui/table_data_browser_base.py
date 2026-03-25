"""
Table Data Browser Base - Shared logic for table data browsing.

This module contains all the shared business logic and widget creation
for both dialog and widget versions of the table browser.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSpinBox, QTableWidget, QTableWidgetItem, QMenu, QInputDialog,
    QMessageBox, QHeaderView, QComboBox, QFileDialog
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

        # Create all widgets - create table first for sorting connection
        self._create_table_widget()
        self._create_pagination_controls()

    def _create_pagination_controls(self):
        """Create all pagination control widgets."""
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索当前页数据...")
        self.search_btn = QPushButton(" 搜索 ")
        self.clear_search_btn = QPushButton(" 清除 ")
        self.search_btn.clicked.connect(self.apply_search)
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #5bc0de;
                color: white;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #31b0d5;
            }
        """)
        self.clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        # Sorting state
        self.sort_column = -1
        self.sort_order = Qt.SortOrder.AscendingOrder
        self.original_full_data = []

        # Pagination buttons and displays
        self.first_btn = QPushButton(" 首页 ")
        self.prev_btn = QPushButton(" 上一页 ")
        self.next_btn = QPushButton(" 下一页 ")
        self.last_btn = QPushButton(" 末页 ")
        self.page_label = QLabel("第 1 页")
        self.total_pages_label = QLabel("共 0 页")
        self.page_input = QSpinBox()
        self.page_input.setRange(1, 1)
        self.page_input.setValue(1)
        self.page_input.setFixedWidth(60)
        self.go_btn = QPushButton(" 跳转 ")
        self.page_size_combo = QSpinBox()
        self.page_size_combo.setRange(10, 100)
        self.page_size_combo.setValue(20)
        self.page_size_combo.setSuffix(" 条/页")
        self.page_size_combo.setFixedWidth(100)

        # Edit operation buttons
        self.add_row_btn = QPushButton(" ➕ 新增行 ")
        self.save_changes_btn = QPushButton(" 💾 保存修改 ")

        # Add some styling
        self.add_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
            QPushButton:pressed {
                background-color: #449d44;
            }
        """)
        self.save_changes_btn.setStyleSheet("""
            QPushButton {
                background-color: #337ab7;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #286090;
            }
            QPushButton:pressed {
                background-color: #204d74;
            }
        """)

        # Connect signals
        self.first_btn.clicked.connect(self.first_page)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.last_btn.clicked.connect(self.last_page)
        self.go_btn.clicked.connect(self.go_to_page)
        self.page_input.returnPressed.connect(self.go_to_page)
        self.page_size_combo.valueChanged.connect(self.change_page_size)
        self.add_row_btn.clicked.connect(self.add_empty_row)
        self.save_changes_btn.clicked.connect(self.save_all_changes)
        # Connect header click for sorting
        self.table_widget.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

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
        # Create action buttons layout (add row, save)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addWidget(self.add_row_btn)
        action_layout.addWidget(self.save_changes_btn)
        action_layout.addStretch()

        # Search bar layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_search_btn)

        # Create pagination layout
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        pagination_layout.addWidget(self.first_btn)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.total_pages_label)
        pagination_layout.addSpacing(10)
        pagination_layout.addWidget(QLabel("跳转到:"))
        pagination_layout.addWidget(self.page_input)
        pagination_layout.addWidget(self.go_btn)
        pagination_layout.addSpacing(10)
        pagination_layout.addWidget(QLabel("每页显示:"))
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(self.last_btn)

        # Add to container layout
        layout.addLayout(action_layout)
        layout.addSpacing(5)
        layout.addLayout(search_layout)
        layout.addSpacing(5)
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
                # Make cells editable for editing
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
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

    def get_primary_key_columns(self) -> list:
        """
        Get the list of primary key column names for the table.

        Returns:
            List of primary key column names, empty if no primary key
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = %s
                      AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY ORDINAL_POSITION
                """, (self.table,))
                result = cursor.fetchall()
                if not result:
                    # Try again with explicit database name
                    cursor.execute("""
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = %s
                          AND TABLE_NAME = %s
                          AND CONSTRAINT_NAME = 'PRIMARY'
                        ORDER BY ORDINAL_POSITION
                    """, (self.database, self.table))
                    result = cursor.fetchall()
                return [row[0] for row in result]
        except Exception:
            return []

    def add_empty_row(self):
        """Add an empty row at the end of the current page for inserting new data."""
        current_rows = self.table_widget.rowCount()
        self.table_widget.insertRow(current_rows)

        # Create empty editable cells
        for col in range(self.table_widget.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table_widget.setItem(current_rows, col, item)

    def delete_current_row(self, parent_widget, row_index: int):
        """
        Delete the selected row from the database.

        Args:
            parent_widget: Parent widget for dialogs
            row_index: Row index to delete
        """
        pk_columns = self.get_primary_key_columns()
        if not pk_columns:
            QMessageBox.warning(parent_widget, "警告",
                "无法删除: 表没有主键，删除功能需要表有主键才能定位记录\n"
                "请在数据库手动执行DELETE语句删除。")
            return

        # Get primary key values
        column_names = [self.table_widget.horizontalHeaderItem(col).text()
                       for col in range(self.table_widget.columnCount())]

        pk_conditions = []
        pk_values = []
        for pk_col in pk_columns:
            if pk_col not in column_names:
                QMessageBox.critical(parent_widget, "错误",
                    f"主键列 '{pk_col}' 不在当前查询结果中，请刷新重试")
                return
            col_idx = column_names.index(pk_col)
            item = self.table_widget.item(row_index, col_idx)
            pk_value = item.text() if item else ""
            pk_conditions.append(f"`{pk_col}` = %s")
            pk_values.append(pk_value)

        condition_str = " AND ".join(pk_conditions)

        reply = QMessageBox.question(
            parent_widget, "确认删除",
            f"确定要删除选中行吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.connection.select_db(self.database)
            with self.connection.cursor() as cursor:
                sql = f"DELETE FROM `{self.table}` WHERE {condition_str}"
                cursor.execute(sql, pk_values)
                self.connection.commit()
                QMessageBox.information(parent_widget, "成功", "行已删除")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(parent_widget, "错误", f"删除失败: {str(e)}")

    def save_all_changes(self):
        """
        Save all modified/added rows to the database.

        - Modified rows are updated via UPDATE
        - New empty rows are inserted via INSERT
        """
        if hasattr(self, 'parent_widget'):
            parent_widget = self.parent_widget
        else:
            parent_widget = None

        pk_columns = self.get_primary_key_columns()
        if not pk_columns:
            QMessageBox.warning(parent_widget, "警告",
                "表没有主键，无法自动检测更新。仅会插入新增行。\n"
                "建议给表添加主键以获得完整的编辑功能。")

        column_names = [self.table_widget.horizontalHeaderItem(col).text()
                       for col in range(self.table_widget.columnCount())]

        updated_count = 0
        inserted_count = 0
        errors = []

        try:
            self.connection.select_db(self.database)

            # Original data from database: first len(self.current_data) rows are existing
            # Any rows added after that are new rows to insert
            existing_rows_count = len(self.current_data)

            for row_idx in range(self.table_widget.rowCount()):
                # Collect all non-empty values from the row
                row_data = {}
                for col_idx, col_name in enumerate(column_names):
                    item = self.table_widget.item(row_idx, col_idx)
                    value = item.text() if item else ""

                    # Convert empty string to None (NULL)
                    if value == "":
                        value = None

                    row_data[col_name] = value

                if row_idx >= existing_rows_count:
                    # This is a newly added row - always insert
                    # Filter out None values for insert
                    insert_cols = []
                    insert_values = []
                    for col_name, value in row_data.items():
                        if value is not None:
                            insert_cols.append(f"`{col_name}`")
                            insert_values.append(value)

                    if not insert_cols:
                        # All empty - skip
                        continue

                    try:
                        with self.connection.cursor() as cursor:
                            placeholders = ", ".join(["%s"] * len(insert_values))
                            sql = f"INSERT INTO `{self.table}` ({', '.join(insert_cols)}) VALUES ({placeholders})"
                            cursor.execute(sql, insert_values)
                            inserted_count += 1
                    except Exception as e:
                        errors.append(f"插入行 {row_idx + 1} 失败: {str(e)}")
                else:
                    # This is an existing row from database - update
                    if not pk_columns:
                        # No primary key - can't update, skip
                        errors.append(f"跳过行 {row_idx + 1}: 表没有主键，无法更新")
                        continue

                    # Get original row data from database
                    original_row = self.current_data[row_idx]

                    # Check if any value actually changed
                    has_changed = False
                    for col_idx, (col_name, current_value) in enumerate(row_data.items()):
                        original_value = original_row[col_idx]
                        # Compare string representation
                        current_str = "" if current_value is None else str(current_value)
                        original_str = "" if original_value is None else str(original_value)
                        if current_str != original_str:
                            has_changed = True
                            break

                    if not has_changed:
                        # No changes, skip this row
                        continue

                    # Get original primary key values from the originally loaded data
                    # This ensures we find the correct row even if user changed the PK value
                    original_pk_values = []
                    for pk_col in pk_columns:
                        if pk_col not in column_names:
                            errors.append(f"更新行 {row_idx + 1} 失败: 主键列 '{pk_col}' 不存在")
                            continue
                        col_idx = column_names.index(pk_col)
                        original_value = original_row[col_idx]
                        original_pk_values.append(original_value)

                    # Build WHERE clause from ORIGINAL primary key values
                    where_conditions = []
                    for pk_col in pk_columns:
                        where_conditions.append(f"`{pk_col}` = %s")

                    # Build SET clause for all columns with current values
                    set_parts = []
                    set_values = []
                    for col_name, value in row_data.items():
                        set_parts.append(f"`{col_name}` = %s")
                        set_values.append(value)

                    if not set_parts:
                        continue

                    try:
                        with self.connection.cursor() as cursor:
                            sql = f"UPDATE `{self.table}` SET {', '.join(set_parts)} WHERE {' AND '.join(where_conditions)}"
                            # Parameters: set values + original PK values for WHERE
                            cursor.execute(sql, set_values + original_pk_values)
                            updated_count += 1
                    except Exception as e:
                        errors.append(f"更新行 {row_idx + 1} 失败: {str(e)}")

            # Commit all changes
            self.connection.commit()

            # Show result
            message = f"保存完成\n- 更新: {updated_count} 行\n- 插入: {inserted_count} 行"
            if errors:
                message += f"\n\n{len(errors)} 个错误:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    message += f"\n... 还有 {len(errors) - 10} 个错误"
                QMessageBox.warning(parent_widget, "保存完成（有错误）", message)
            else:
                if inserted_count > 0 or updated_count > 0:
                    QMessageBox.information(parent_widget, "保存成功", message)

            # Go to last page to show newly inserted rows
            # First get updated total rows
            try:
                self.connection.select_db(self.database)
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM `{self.table}`;")
                    self.total_rows = cursor.fetchone()[0]
            except Exception:
                pass

            # Jump to last page
            if self.total_rows > 0:
                total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
                self.current_page = total_pages - 1

            # Reload data to refresh
            self.load_data()

        except Exception as e:
            QMessageBox.critical(parent_widget, "错误", f"保存失败: {str(e)}")

    def export_data(self, parent_widget, format_type: str):
        """
        Export all currently displayed data to file.

        Args:
            parent_widget: Parent widget for dialogs
            format_type: "csv" or "json"
        """
        # Get file extension filter
        if format_type == "csv":
            filter_str = "CSV 文件 (*.csv);;所有文件 (*.*)"
            default_ext = ".csv"
        else:
            filter_str = "JSON 文件 (*.json);;all files (*.*)"
            default_ext = ".json"

        # Get save path from user
        default_name = f"{self.table}{default_ext}"
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            f"导出数据 - {format_type.upper()}",
            default_name,
            filter_str
        )
        if not file_path:
            return

        # Collect data from table
        column_names = [
            self.table_widget.horizontalHeaderItem(col).text()
            for col in range(self.table_widget.columnCount())
        ]

        data = []
        for row_idx in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row_idx):
                row_data = {}
                for col_idx, col_name in enumerate(column_names):
                    item = self.table_widget.item(row_idx, col_idx)
                    value = item.text() if item else ""
                    row_data[col_name] = value
                data.append(row_data)

        try:
            if format_type == "csv":
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=column_names)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                parent_widget,
                "导出成功",
                f"成功导出 {len(data)} 行到文件:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "导出失败",
                f"写入文件失败: {str(e)}"
            )

    def apply_search(self):
        """Filter current page data by search keyword."""
        keyword = self.search_input.text().strip().lower()
        if not keyword:
            self.clear_search()
            return

        # Keep only rows that contain the keyword in any cell
        filtered_rows = []
        for row_idx in range(self.table_widget.rowCount()):
            has_match = False
            for col_idx in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row_idx, col_idx)
                if item:
                    text = item.text().lower()
                    if keyword in text:
                        has_match = True
                        break
            if has_match:
                filtered_rows.append(row_idx)

        # Hide rows that don't match
        for row_idx in range(self.table_widget.rowCount()):
            self.table_widget.setRowHidden(row_idx, row_idx not in filtered_rows)

        # Show how many rows matched
        if hasattr(self, 'parent_widget'):
            parent = self.parent_widget
        else:
            parent = None
        if filtered_rows:
            QMessageBox.information(parent, "搜索完成", f"找到 {len(filtered_rows)} 行匹配")
        else:
            QMessageBox.information(parent, "搜索完成", "没有找到匹配的行")

    def clear_search(self):
        """Clear search filter and show all rows."""
        self.search_input.clear()
        for row_idx in range(self.table_widget.rowCount()):
            self.table_widget.setRowHidden(row_idx, False)

    def on_header_clicked(self, logical_index: int):
        """
        Handle header click to sort by this column.

        Args:
            logical_index: Column index clicked
        """
        # Toggle sort order if clicking the same column again
        if self.sort_column == logical_index:
            if self.sort_order == Qt.SortOrder.AscendingOrder:
                self.sort_order = Qt.SortOrder.DescendingOrder
            else:
                self.sort_order = Qt.SortOrder.AscendingOrder
        else:
            self.sort_column = logical_index
            self.sort_order = Qt.SortOrder.AscendingOrder

        # Get all visible rows
        rows_data = []
        for row_idx in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row_idx):
                item = self.table_widget.item(row_idx, self.sort_column)
                text = item.text() if item else ""
                # Try to convert to number for numeric sorting
                try:
                    sort_key = float(text)
                except ValueError:
                    sort_key = text
                rows_data.append((sort_key, row_idx))

        # Sort
        rows_data.sort(key=lambda x: x[0], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))

        # Reorder rows in the table
        # We need to move rows one by one
        for new_pos, (_, old_pos) in enumerate(rows_data):
            self.table_widget.verticalHeader().moveSection(old_pos, new_pos)

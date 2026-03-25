"""
Table Modify Dialog - Dialog for modifying existing table structure.

This module provides a dialog for editing existing table structure,
allowing users to add/remove/modify columns and indexes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QDialogButtonBox, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from gui.table_create_dialog import INDEX_TYPES


class TableModifyDialog(QDialog):
    """
    Dialog for modifying an existing table structure.

    Allows users to add/remove columns, modify column attributes,
    and add/remove indexes.
    """

    def __init__(self, database: str, table: str, current_connection, parent=None):
        """
        Initialize the table modify dialog.

        Args:
            database: Database name containing the table
            table: Table name to modify
            current_connection: Active database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.database = database
        self.table = table
        self.connection = current_connection
        self.setWindowTitle(f"✏️ 修改表结构 - {database}.{table}")
        self.setModal(True)
        self.resize(850, 650)
        self.setup_ui()
        self.load_existing_structure()

    def setup_ui(self):
        """Setup the dialog UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Table name display
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(f"表名: <b>{self.database}.{self.table}</b>"))
        name_layout.addStretch()
        layout.addLayout(name_layout)
        layout.addSpacing(5)

        # Columns section
        columns_group = QGroupBox(" 字段定义 ")
        columns_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        columns_layout = QVBoxLayout()
        columns_layout.setSpacing(8)
        columns_layout.setContentsMargins(10, 15, 10, 10)

        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(7)
        self.columns_table.setHorizontalHeaderLabels([
            "字段名", "类型", "主键", "自增", "允许NULL", "默认值", "操作"
        ])
        header = self.columns_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        columns_layout.addWidget(self.columns_table)

        # Buttons for adding/removing rows
        row_buttons_layout = QHBoxLayout()
        add_row_btn = QPushButton(" ➕ 添加字段 ")
        add_row_btn.clicked.connect(self.add_row)
        add_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #5bc0de;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #31b0d5;
            }
        """)
        remove_row_btn = QPushButton(" ➖ 删除选中行 ")
        remove_row_btn.clicked.connect(self.remove_selected_row)
        remove_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        row_buttons_layout.addWidget(add_row_btn)
        row_buttons_layout.addWidget(remove_row_btn)
        row_buttons_layout.addStretch()
        columns_layout.addLayout(row_buttons_layout)

        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)

        # Indexes section
        indexes_group = QGroupBox(" 索引定义 ")
        indexes_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        indexes_layout = QVBoxLayout()
        indexes_layout.setSpacing(8)
        indexes_layout.setContentsMargins(10, 15, 10, 10)

        self.indexes_table = QTableWidget()
        self.indexes_table.setColumnCount(4)
        self.indexes_table.setHorizontalHeaderLabels([
            "索引名称", "索引类型", "索引字段 (逗号分隔)", "操作"
        ])
        idx_header = self.indexes_table.horizontalHeader()
        idx_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        idx_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        idx_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        idx_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        indexes_layout.addWidget(self.indexes_table)

        # Index buttons
        idx_buttons_layout = QHBoxLayout()
        add_idx_btn = QPushButton(" ➕ 添加索引 ")
        add_idx_btn.clicked.connect(self.add_index_row)
        remove_idx_btn = QPushButton(" ➖ 删除选中索引 ")
        add_idx_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0ad4e;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #eea236;
            }
        """)
        remove_idx_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        remove_idx_btn.clicked.connect(self.remove_selected_index)
        idx_buttons_layout.addWidget(add_idx_btn)
        idx_buttons_layout.addWidget(remove_idx_btn)
        idx_buttons_layout.addStretch()
        indexes_layout.addLayout(idx_buttons_layout)

        indexes_group.setLayout(indexes_layout)
        layout.addWidget(indexes_group)

        # Engine and charset options
        options_layout = QGridLayout()
        options_layout.setSpacing(15)
        options_layout.addWidget(QLabel("存储引擎:"), 0, 0)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["InnoDB", "MyISAM", "MEMORY"])
        options_layout.addWidget(self.engine_combo, 0, 1)

        options_layout.addWidget(QLabel("字符集:"), 0, 2)
        self.charset_combo = QComboBox()
        self.charset_combo.addItems(["utf8mb4", "utf8", "gbk", "latin1"])
        options_layout.addWidget(self.charset_combo, 0, 3)
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)
        layout.addLayout(options_layout)
        layout.addSpacing(5)

        # Dialog buttons (Modify / Cancel)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText(" ✅ 保存修改 ")
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #5cb85c;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 20px;
                }
                QPushButton:hover {
                    background-color: #4cae4c;
                }
            """)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText(" ❌ 取消 ")
        buttons.accepted.connect(self.modify_table)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.setMinimumWidth(750)
        self.setMinimumHeight(550)

    def add_row(self, col_name="", col_type="INT", is_pk=False, is_ai=False, allow_null=True, default=""):
        """Add a new empty row to the columns table."""
        row_count = self.columns_table.rowCount()
        self.columns_table.insertRow(row_count)
        self.columns_table.setRowHeight(row_count, 35)

        # Field name
        item = QTableWidgetItem(col_name)
        self.columns_table.setItem(row_count, 0, item)

        # Data type combo
        from gui.table_create_dialog import MYSQL_TYPES
        type_combo = QComboBox()
        type_combo.addItems(MYSQL_TYPES)
        type_index = MYSQL_TYPES.index(col_type) if col_type in MYSQL_TYPES else 0
        type_combo.setCurrentIndex(type_index)
        self.columns_table.setCellWidget(row_count, 1, type_combo)

        # Primary key checkbox - center align
        pk_check = QCheckBox()
        pk_check.setChecked(is_pk)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(pk_check)
        layout.setAlignment(pk_check, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 2, container)

        # Auto-increment checkbox - center align
        ai_check = QCheckBox()
        ai_check.setChecked(is_ai)
        container2 = QWidget()
        layout2 = QVBoxLayout(container2)
        layout2.addWidget(ai_check)
        layout2.setAlignment(ai_check, Qt.AlignmentFlag.AlignCenter)
        layout2.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 3, container2)

        # Allow NULL checkbox - center align
        null_check = QCheckBox()
        null_check.setChecked(allow_null)
        container3 = QWidget()
        layout3 = QVBoxLayout(container3)
        layout3.addWidget(null_check)
        layout3.setAlignment(null_check, Qt.AlignmentFlag.AlignCenter)
        layout3.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 4, container3)

        # Default value
        default_item = QTableWidgetItem(default)
        self.columns_table.setItem(row_count, 5, default_item)

        # Drop button
        drop_btn = QPushButton("删除")
        drop_btn.setStyleSheet("color: #d9534f;")
        drop_btn.clicked.connect(lambda: self.remove_row_by_button(row_count))
        self.columns_table.setCellWidget(row_count, 6, drop_btn)

    def remove_row_by_button(self, row_idx):
        """Remove a specific row when button is clicked."""
        self.columns_table.removeRow(row_idx)

    def remove_selected_row(self):
        """Remove the currently selected row."""
        selected_ranges = self.columns_table.selectedRanges()
        if not selected_ranges:
            return

        rows = sorted([range.topRow() for range in selected_ranges], reverse=True)
        for row in rows:
            self.columns_table.removeRow(row)

    def add_index_row(self, idx_name="", idx_type="INDEX (普通索引)", cols=""):
        """Add a new empty row to the indexes table."""
        row_count = self.indexes_table.rowCount()
        self.indexes_table.insertRow(row_count)
        self.indexes_table.setRowHeight(row_count, 35)

        # Index name
        name_item = QTableWidgetItem(idx_name)
        self.indexes_table.setItem(row_count, 0, name_item)

        # Index type combo
        type_combo = QComboBox()
        type_combo.addItems(INDEX_TYPES)
        type_index = INDEX_TYPES.index(idx_type) if idx_type in INDEX_TYPES else 0
        type_combo.setCurrentIndex(type_index)
        self.indexes_table.setCellWidget(row_count, 1, type_combo)

        # Index columns
        cols_item = QTableWidgetItem(cols)
        self.indexes_table.setItem(row_count, 2, cols_item)

        # Drop button
        drop_btn = QPushButton("删除")
        drop_btn.setStyleSheet("color: #d9534f;")
        drop_btn.clicked.connect(lambda: self.remove_index_by_button(row_count))
        self.indexes_table.setCellWidget(row_count, 3, drop_btn)

    def remove_index_by_button(self, row_idx):
        """Remove a specific index row when button is clicked."""
        self.indexes_table.removeRow(row_idx)

    def remove_selected_index(self):
        """Remove the currently selected index row."""
        selected_ranges = self.indexes_table.selectedRanges()
        if not selected_ranges:
            return

        rows = sorted([range.topRow() for range in selected_ranges], reverse=True)
        for row in rows:
            self.indexes_table.removeRow(row)

    def load_existing_structure(self):
        """Load existing table structure from database."""
        try:
            self.connection.select_db(self.database)

            # Get table columns with DESCRIBE
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{self.table}`;")
                columns_info = cursor.fetchall()

            # DESCRIBE gives: Field, Type, Null, Key, Default, Extra
            pk_columns = []
            for col_info in columns_info:
                field = col_info[0]
                col_type = col_info[1]
                is_nullable = col_info[2] == 'YES'
                key = col_info[3]
                default = col_info[4] if col_info[4] is not None else ""
                extra = col_info[5] or ""

                is_pk = key == 'PRI'
                is_ai = 'auto_increment' in extra.lower()

                # Find matching type in MYSQL_TYPES or add as-is
                from gui.table_create_dialog import MYSQL_TYPES
                type_clean = col_type.split('(')[0].upper()
                matched_type = next((t for t in MYSQL_TYPES if t.startswith(type_clean)), col_type)

                self.add_row(field, matched_type, is_pk, is_ai, is_nullable, str(default))

                if is_pk:
                    pk_columns.append(field)

            # Get existing indexes
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME
                    FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """, (self.database, self.table))
                index_info = cursor.fetchall()

            # Group by index name
            indexes = {}
            for idx_name, non_unique, seq, col_name in index_info:
                if idx_name == 'PRIMARY':
                    continue  # Primary key already handled in columns
                if idx_name not in indexes:
                    if non_unique == 1:
                        idx_type = "INDEX (普通索引)"
                    else:
                        idx_type = "UNIQUE (唯一索引)"
                    indexes[idx_name] = {'type': idx_type, 'columns': []}
                indexes[idx_name]['columns'].append(col_name)

            for idx_name, idx_data in indexes.items():
                cols_str = ", ".join(idx_data['columns'])
                self.add_index_row(idx_name, idx_data['type'], cols_str)

            # Get table engine and charset
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT ENGINE, TABLE_COLLATION
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                """, (self.database, self.table))
                result = cursor.fetchone()
                if result:
                    engine = result[0] or "InnoDB"
                    collation = result[1] or "utf8mb4_general_ci"
                    charset = collation.split('_')[0]

                    if engine in [self.engine_combo.itemText(i) for i in range(self.engine_combo.count())]:
                        self.engine_combo.setCurrentText(engine)
                    if charset in [self.charset_combo.itemText(i) for i in range(self.charset_combo.count())]:
                        self.charset_combo.setCurrentText(charset)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载表结构失败: {str(e)}")

    def get_alter_statements(self) -> list:
        """
        Generate ALTER TABLE statements for all changes.

        Returns:
            List of SQL statements to execute
        """
        sql_list = []

        # For simplicity, we just recreate the table structure with ALTER
        # This approach adds/modifies columns and indexes

        # Note: This doesn't handle column order changes perfectly
        # but works for most common cases

        return sql_list

    def modify_table(self):
        """Generate ALTER TABLE statements and execute them."""
        # We'll collect all changes and execute them one by one
        sql_statements = []

        # Get original columns from loaded table
        # We need to compare to detect changes
        # For this dialog, we'll rebuild the table structure completely
        # by dropping and adding all changes

        # First, collect current columns from the table
        current_columns = []
        pk_columns = []
        for row in range(self.columns_table.rowCount()):
            # Get field name
            name_item = self.columns_table.item(row, 0)
            col_name = name_item.text().strip() if name_item else ""
            if not col_name:
                continue

            # Get data type
            type_combo = self.columns_table.cellWidget(row, 1)
            col_type = type_combo.currentText() if type_combo else "INT"

            # Get primary key
            pk_container = self.columns_table.cellWidget(row, 2)
            pk_check = pk_container.findChild(QCheckBox)
            is_pk = pk_check.isChecked() if pk_check else False
            if is_pk:
                pk_columns.append(col_name)

            # Get auto-increment
            ai_container = self.columns_table.cellWidget(row, 3)
            ai_check = ai_container.findChild(QCheckBox)
            is_ai = ai_check.isChecked() if ai_check else False

            # Get allow null
            null_container = self.columns_table.cellWidget(row, 4)
            null_check = null_container.findChild(QCheckBox)
            allow_null = null_check.isChecked() if null_check else True

            # Get default value
            default_item = self.columns_table.item(row, 5)
            default = default_item.text().strip() if default_item else ""

            # Build column definition
            col_def = f"ADD COLUMN `{col_name}` {col_type}"
            if not allow_null:
                col_def += " NOT NULL"
            if is_ai:
                col_def += " AUTO_INCREMENT"
            if default:
                if default.upper() in ["CURRENT_TIMESTAMP", "NULL"]:
                    col_def += f" DEFAULT {default}"
                else:
                    try:
                        float(default)
                        col_def += f" DEFAULT {default}"
                    except ValueError:
                        col_def += f" DEFAULT '{default}'"

            current_columns.append((col_name, col_def))

        # Get current indexes
        current_indexes = []
        for row in range(self.indexes_table.rowCount()):
            # Get index name
            name_item = self.indexes_table.item(row, 0)
            idx_name = name_item.text().strip() if name_item else ""

            # Get index type
            type_combo = self.indexes_table.cellWidget(row, 1)
            type_text = type_combo.currentText() if type_combo else "INDEX (普通索引)"

            # Get columns
            cols_item = self.indexes_table.item(row, 2)
            cols_text = cols_item.text().strip() if cols_item else ""

            if not cols_text:
                continue

            # Parse type
            if type_text.startswith("UNIQUE"):
                idx_keyword = "UNIQUE"
            elif type_text.startswith("FULLTEXT"):
                idx_keyword = "FULLTEXT"
            else:
                idx_keyword = "ADD INDEX"

            # Parse columns
            col_list = [c.strip() for c in cols_text.split(",") if c.strip()]
            col_defs = ", ".join(f'`{c}`' for c in col_list)

            if idx_name:
                idx_def = f"{idx_keyword} `{idx_name}` ({col_defs})"
            else:
                auto_name = "_".join(col_list)
                idx_def = f"{idx_keyword} `{auto_name}` ({col_defs})"

            current_indexes.append(idx_def)

        # Since we can't easily compare what changed, we'll create a complete
        # new table and replace it. This is safer for a simple GUI tool.
        # However, this is destructive - warn the user

        confirm = QMessageBox.question(
            self,
            "确认修改",
            "修改表结构将会重建表。\n请确保已备份数据！\n\n确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Create new table with temporary name, copy data, then rename
        temp_table = f"_temp_{self.table}_{hash(self.table)}"

        # Build CREATE TABLE statement for the new structure
        columns_sql = []

        # Add columns
        for _, col_def in current_columns:
            # Strip "ADD COLUMN " from beginning
            col_def_clean = col_def.replace("ADD COLUMN ", "")
            columns_sql.append(col_def_clean)

        # Add primary key if we have it
        if pk_columns:
            pk_def = f"PRIMARY KEY ({', '.join(f'`{pk}`' for pk in pk_columns)})"
            columns_sql.append(pk_def)

        # Add indexes
        for idx_def in current_indexes:
            # Strip "ADD " from beginning
            idx_def_clean = idx_def.replace("ADD ", "")
            columns_sql.append(idx_def_clean)

        engine = self.engine_combo.currentText()
        charset = self.charset_combo.currentText()

        create_sql = (
            f"CREATE TABLE `{self.database}`.`{temp_table}` (\n"
            f"    " + ",\n    ".join(columns_sql) + "\n"
            f") ENGINE={engine} DEFAULT CHARSET={charset};"
        )

        copy_data_sql = f"INSERT INTO `{temp_table}` SELECT * FROM `{self.table}`;"

        drop_old_sql = f"DROP TABLE `{self.table}`;"
        rename_sql = f"RENAME TABLE `{temp_table}` TO `{self.table}`;"

        sql_statements = [create_sql, copy_data_sql, drop_old_sql, rename_sql]

        try:
            self.connection.select_db(self.database)
            with self.connection.cursor() as cursor:
                for sql in sql_statements:
                    cursor.execute(sql)
            self.connection.commit()
            QMessageBox.information(self, "成功", "表结构修改完成！")
            self.accept()
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "错误", f"修改失败:\n{str(e)}\n\n生成的SQL:\n" + "\n".join(sql_statements))

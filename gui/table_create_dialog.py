"""
Table Create Dialog - Dialog for visually designing and creating new tables.

This module provides a dialog for creating new tables with visual field design,
allowing users to specify column names, data types, primary keys, and other options.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QDialogButtonBox, QHeaderView, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt

# Common MySQL data types for quick selection
MYSQL_TYPES = [
    "INT", "BIGINT", "VARCHAR(255)", "VARCHAR(500)", "TEXT", "LONGTEXT",
    "DECIMAL(10,2)", "FLOAT", "DOUBLE", "DATE", "DATETIME", "TIMESTAMP",
    "BOOLEAN", "TINYINT", "SMALLINT", "BLOB", "JSON"
]

# Index types
INDEX_TYPES = [
    "INDEX (普通索引)",
    "UNIQUE (唯一索引)",
    "FULLTEXT (全文索引)"
]


class TableCreateDialog(QDialog):
    """
    Dialog for visually creating a new table.

    Allows users to add/remove columns, specify column names, data types,
    primary key, auto-increment, nullability, default values, and additional indexes.
    """

    def __init__(self, database: str, current_connection, parent=None):
        """
        Initialize the table create dialog.

        Args:
            database: Database where the table will be created
            current_connection: Active database connection
            parent: Parent widget
        """
        super().__init__(parent)
        self.database = database
        self.connection = current_connection
        self.setWindowTitle(f"创建表 - {database}")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Table name input
        name_layout = QHBoxLayout()
        name_label = QLabel("表名:")
        name_label.setMinimumWidth(60)
        name_layout.addWidget(name_label)
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("请输入新表名称")
        name_layout.addWidget(self.table_name_input)
        layout.addLayout(name_layout)
        layout.addSpacing(5)

        # Columns section
        columns_group = QGroupBox(" 字段定义 ")
        columns_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        columns_layout = QVBoxLayout()
        columns_layout.setSpacing(8)
        columns_layout.setContentsMargins(10, 15, 10, 10)

        self.columns_table = QTableWidget()
        self.columns_table.setColumnCount(6)
        self.columns_table.setHorizontalHeaderLabels([
            "字段名", "类型", "主键", "自增", "允许NULL", "默认值"
        ])
        self.columns_table.setRowHeight(0, 30)
        header = self.columns_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        # Add one default row
        self.add_row()

        columns_layout.addWidget(self.columns_table)

        # Buttons for adding/removing rows
        row_buttons_layout = QHBoxLayout()
        add_row_btn = QPushButton(" ➕ 添加字段 ")
        add_row_btn.clicked.connect(self.add_row)
        remove_row_btn = QPushButton(" ➖ 删除选中行 ")
        remove_row_btn.clicked.connect(self.remove_selected_row)
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
        self.indexes_table.setColumnCount(3)
        self.indexes_table.setHorizontalHeaderLabels([
            "索引名称", "索引类型", "索引字段 (逗号分隔多个字段)"
        ])
        self.indexes_table.setRowHeight(0, 30)
        idx_header = self.indexes_table.horizontalHeader()
        idx_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        idx_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        idx_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        indexes_layout.addWidget(self.indexes_table)

        # Index buttons
        idx_buttons_layout = QHBoxLayout()
        add_idx_btn = QPushButton(" ➕ 添加索引 ")
        add_idx_btn.clicked.connect(self.add_index_row)
        remove_idx_btn = QPushButton(" ➖ 删除选中索引 ")
        remove_idx_btn.clicked.connect(self.remove_selected_index)
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
        self.engine_combo.setCurrentIndex(0)
        options_layout.addWidget(self.engine_combo, 0, 1)

        options_layout.addWidget(QLabel("字符集:"), 0, 2)
        self.charset_combo = QComboBox()
        self.charset_combo.addItems(["utf8mb4", "utf8", "gbk", "latin1"])
        self.charset_combo.setCurrentIndex(0)
        options_layout.addWidget(self.charset_combo, 0, 3)
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(3, 1)
        layout.addLayout(options_layout)
        layout.addSpacing(5)

        # Dialog buttons (Create / Cancel)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText(" 创建表 ")
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText(" 取消 ")
        buttons.accepted.connect(self.create_table)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.setMinimumWidth(750)
        self.setMinimumHeight(550)

    def add_row(self):
        """Add a new empty row to the columns table."""
        row_count = self.columns_table.rowCount()
        self.columns_table.insertRow(row_count)
        self.columns_table.setRowHeight(row_count, 32)

        # Field name
        item = QTableWidgetItem("")
        self.columns_table.setItem(row_count, 0, item)

        # Data type combo
        type_combo = QComboBox()
        type_combo.addItems(MYSQL_TYPES)
        type_combo.setCurrentIndex(0)
        self.columns_table.setCellWidget(row_count, 1, type_combo)

        # Primary key checkbox - center align
        pk_check = QCheckBox()
        pk_check.setChecked(False)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(pk_check)
        layout.setAlignment(pk_check, Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 2, container)

        # Auto-increment checkbox - center align
        ai_check = QCheckBox()
        ai_check.setChecked(False)
        container2 = QWidget()
        layout2 = QVBoxLayout(container2)
        layout2.addWidget(ai_check)
        layout2.setAlignment(ai_check, Qt.AlignmentFlag.AlignCenter)
        layout2.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 3, container2)

        # Allow NULL checkbox - center align
        null_check = QCheckBox()
        null_check.setChecked(True)
        container3 = QWidget()
        layout3 = QVBoxLayout(container3)
        layout3.addWidget(null_check)
        layout3.setAlignment(null_check, Qt.AlignmentFlag.AlignCenter)
        layout3.setContentsMargins(0, 0, 0, 0)
        self.columns_table.setCellWidget(row_count, 4, container3)

        # Default value
        default_item = QTableWidgetItem("")
        self.columns_table.setItem(row_count, 5, default_item)

    def remove_selected_row(self):
        """Remove the currently selected row."""
        selected_ranges = self.columns_table.selectedRanges()
        if not selected_ranges:
            return

        # Remove from bottom to top
        rows = sorted([range.topRow() for range in selected_ranges], reverse=True)
        for row in rows:
            self.columns_table.removeRow(row)

    def add_index_row(self):
        """Add a new empty row to the indexes table."""
        row_count = self.indexes_table.rowCount()
        self.indexes_table.insertRow(row_count)
        self.indexes_table.setRowHeight(row_count, 32)

        # Index name
        name_item = QTableWidgetItem("")
        self.indexes_table.setItem(row_count, 0, name_item)

        # Index type combo
        type_combo = QComboBox()
        type_combo.addItems(INDEX_TYPES)
        type_combo.setCurrentIndex(0)
        self.indexes_table.setCellWidget(row_count, 1, type_combo)

        # Index columns
        cols_item = QTableWidgetItem("")
        self.indexes_table.setItem(row_count, 2, cols_item)

    def remove_selected_index(self):
        """Remove the currently selected index row."""
        selected_ranges = self.indexes_table.selectedRanges()
        if not selected_ranges:
            return

        # Remove from bottom to top
        rows = sorted([range.topRow() for range in selected_ranges], reverse=True)
        for row in rows:
            self.indexes_table.removeRow(row)

    def get_create_sql(self) -> str:
        """
        Generate the CREATE TABLE SQL statement from the UI inputs.

        Returns:
            Generated SQL string
        """
        table_name = self.table_name_input.text().strip()
        if not table_name:
            return ""

        columns = []
        primary_keys = []
        indexes = []

        # Process columns
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
            pk_check = self.columns_table.cellWidget(row, 2)
            is_pk = pk_check.isChecked() if pk_check else False
            if is_pk:
                primary_keys.append(col_name)

            # Get auto-increment
            ai_check = self.columns_table.cellWidget(row, 3)
            is_ai = ai_check.isChecked() if ai_check else False

            # Get allow null
            null_check = self.columns_table.cellWidget(row, 4)
            allow_null = null_check.isChecked() if null_check else True

            # Get default value
            default_item = self.columns_table.item(row, 5)
            default = default_item.text().strip() if default_item else ""

            # Build column definition
            col_def = f"`{col_name}` {col_type}"

            if not allow_null:
                col_def += " NOT NULL"

            if is_ai:
                col_def += " AUTO_INCREMENT"

            if default:
                # Handle special default values
                if default.upper() in ["CURRENT_TIMESTAMP", "NULL"]:
                    col_def += f" DEFAULT {default}"
                else:
                    # Quote string defaults
                    try:
                        float(default)
                        col_def += f" DEFAULT {default}"
                    except ValueError:
                        col_def += f" DEFAULT '{default}'"

            columns.append(col_def)

        # Add primary key constraint if any
        if primary_keys:
            pk_def = f"PRIMARY KEY ({', '.join(f'`{pk}`' for pk in primary_keys)})"
            columns.append(pk_def)

        # Process additional indexes
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
                idx_keyword = "INDEX"

            # Parse columns
            col_list = [c.strip() for c in cols_text.split(",") if c.strip()]
            col_defs = ", ".join(f'`{c}`' for c in col_list)

            # Build index definition
            if idx_name:
                idx_def = f"{idx_keyword} `{idx_name}` ({col_defs})"
            else:
                # Auto-generate name from columns
                auto_name = "_".join(col_list)
                idx_def = f"{idx_keyword} `{auto_name}` ({col_defs})"

            indexes.append(idx_def)

        # Add all indexes
        columns.extend(indexes)

        engine = self.engine_combo.currentText()
        charset = self.charset_combo.currentText()

        sql = (
            f"CREATE TABLE `{self.database}`.`{table_name}` (\n"
            f"    " + ",\n    ".join(columns) + "\n"
            f") ENGINE={engine} DEFAULT CHARSET={charset};"
        )

        return sql

    def create_table(self):
        """Execute the CREATE TABLE statement and close the dialog."""
        table_name = self.table_name_input.text().strip()
        if not table_name:
            QMessageBox.warning(self, "警告", "请输入表名")
            return

        if self.columns_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "至少需要一个字段")
            return

        # Validate at least one field has name
        has_valid_field = False
        for row in range(self.columns_table.rowCount()):
            name_item = self.columns_table.item(row, 0)
            if name_item and name_item.text().strip():
                has_valid_field = True
                break
        if not has_valid_field:
            QMessageBox.warning(self, "警告", "至少一个字段需要填写名称")
            return

        sql = self.get_create_sql()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
            self.connection.commit()
            QMessageBox.information(self, "成功", f"表 '{table_name}' 创建成功")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建表失败:\n{str(e)}\n\n生成的SQL:\n{sql}")

"""
Table Info Dialog - Dialog for displaying table structure information.

This module contains the TableInfoDialog class that shows the structure
of a MySQL table in a readable table format.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt


class TableInfoDialog(QDialog):
    """
    Dialog for displaying table structure (DESCRIBE result).

    Shows the columns, types, nullability, keys, default values, and extra
    information for a MySQL table.
    """

    def __init__(self, table_info, parent=None):
        """
        Initialize the table info dialog.

        Args:
            table_info: List of column information from DESCRIBE query
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("表结构")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        # Create table widget to display column information
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(['字段', '类型', '空', '键', '默认', '额外'])

        # Fill the table with data
        self.table_widget.setRowCount(len(table_info))
        for i, col in enumerate(table_info):
            for j, value in enumerate(col):
                item = QTableWidgetItem(str(value) if value is not None else "")
                # Make cells read-only
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, j, item)

        layout.addWidget(self.table_widget)

        # Close button
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

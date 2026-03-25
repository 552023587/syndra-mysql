"""
Table Data Browser - Dialog version of table data browser.

This module provides a dialog window for browsing table data separately.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMenu, QApplication
from PyQt6.QtGui import QClipboard
from pymysql import Connection
from gui.table_data_browser_base import TableDataBrowserLogic


class TableDataBrowser(QDialog):
    """
    Table data browser as a standalone dialog window.

    Used when opening table data in a separate dialog.
    Uses composition with TableDataBrowserLogic for all logic.
    """

    def __init__(self, connection: Connection, database: str, table: str, parent=None):
        """
        Initialize the table browser dialog.

        Args:
            connection: Active pymysql connection
            database: Database name
            table: Table name
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(f"数据浏览 - {database}.{table}")
        self.setGeometry(200, 200, 1000, 600)

        # Store reference to self for message boxes
        self.logic = TableDataBrowserLogic(connection, database, table)
        self.logic.parent_widget = self

        # Connect context menu signal
        self.logic.table_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Create layout and add widgets
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.logic.setup_layout(layout)

        # Load data after everything is setup
        self.logic.load_data()

    def show_context_menu(self, position):
        """Show context menu with copy operations and table operations."""
        menu = QMenu()

        # Get the cell at the right-click position
        index = self.logic.table_widget.indexAt(position)
        row = index.row()
        col = index.column()

        # Add row operations if a cell is under the cursor
        if index.isValid():
            copy_cell_action = menu.addAction("复制单元格")
            copy_row_action = menu.addAction("复制整行")
            delete_row_action = menu.addAction("删除当前行")
            menu.addSeparator()

        # Add export operations
        export_csv_action = menu.addAction("📄 导出CSV")
        export_json_action = menu.addAction("📋 导出JSON")
        menu.addSeparator()

        # Add table operations
        rename_action = menu.addAction("重命名表")
        delete_action = menu.addAction("删除表")
        design_action = menu.addAction("设计表")

        action = menu.exec(self.logic.table_widget.mapToGlobal(position))

        if not action:
            return

        # Handle row operations
        if index.isValid():
            if action == copy_cell_action:
                self._copy_cell(row, col)
            elif action == copy_row_action:
                self._copy_row(row)
            elif 'delete_row_action' in locals() and action == delete_row_action:
                self.logic.delete_current_row(self, row)

        # Handle export operations
        if action == export_csv_action:
            self.logic.export_data(self, "csv")
        elif action == export_json_action:
            self.logic.export_data(self, "json")

        # Handle table operations
        if action == rename_action:
            self.logic.rename_table(self)
            # Update window title after rename
            if self.logic.table != self.windowTitle().split('.')[1]:
                self.setWindowTitle(f"数据浏览 - {self.logic.database}.{self.logic.table}")
        elif action == delete_action:
            self.logic.delete_table(self)
            if self.logic.table not in [t for t in self.windowTitle().split('.')]:
                # Table deleted, close the dialog
                self.close()
        elif action == design_action:
            self.logic.design_table(self)

    def _copy_cell(self, row: int, col: int):
        """Copy the content of a single cell to clipboard."""
        item = self.logic.table_widget.item(row, col)
        if item:
            text = item.text()
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def _copy_row(self, row: int):
        """Copy all cells in a row to clipboard (tab-separated)."""
        row_data = []
        col_count = self.logic.table_widget.columnCount()
        for col in range(col_count):
            item = self.logic.table_widget.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append("")
        text = "\t".join(row_data)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    # Delegate any needed methods to logic
    def change_page_size(self):
        self.logic.change_page_size()

    def load_data(self):
        self.logic.load_data()

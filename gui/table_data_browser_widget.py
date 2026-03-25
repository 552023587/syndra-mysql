"""
Table Data Browser Widget - Widget version of table data browser for tabs.

This module provides a widget version that can be embedded in a tab
in the main window. Uses composition with TableDataBrowserLogic.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMenu, QApplication
from PyQt6.QtGui import QClipboard
from pymysql import Connection
from gui.table_data_browser_base import TableDataBrowserLogic


class TableDataBrowserWidget(QWidget):
    """
    Table data browser as a widget for embedding in tabs.

    Used when opening tables as tabs in the main window.
    All logic is handled by TableDataBrowserLogic.
    """

    def __init__(self, connection: Connection, database: str, table: str, parent=None):
        """
        Initialize the table browser widget.

        Args:
            connection: Active pymysql connection
            database: Database name containing the table
            table: Table name to browse
            parent: Parent widget (usually the QTabWidget)
        """
        super().__init__(parent)

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

        # Add copy operations if a cell is under the cursor
        if index.isValid():
            copy_cell_action = menu.addAction("复制单元格")
            copy_row_action = menu.addAction("复制整行")
            menu.addSeparator()

        # Add table operations
        rename_action = menu.addAction("重命名表")
        delete_action = menu.addAction("删除表")
        design_action = menu.addAction("设计表")

        action = menu.exec(self.logic.table_widget.mapToGlobal(position))

        if not action:
            return

        # Handle copy operations
        if index.isValid():
            if action == copy_cell_action:
                self._copy_cell(row, col)
            elif action == copy_row_action:
                self._copy_row(row)

        # Handle table operations
        if action == rename_action:
            self.logic.rename_table(self)
        elif action == delete_action:
            self.logic.delete_table(self)
            # Note: After deletion, closing the tab needs to be handled by MainWindow
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

    # Delegate public methods
    def change_page_size(self):
        self.logic.change_page_size()

    def load_data(self):
        self.logic.load_data()

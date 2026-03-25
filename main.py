"""
Syndra MySQL Client - Main Entry Point

A PyQt6-based MySQL database management client with:
- Connection management with encrypted password storage
- SQL editor with syntax highlighting and auto-completion
- Table data browsing with pagination
- Database tree view with context menu operations
- Multiple open tables in tabs
"""

import sys
from PyQt6.QtWidgets import QApplication

# Explicit imports for PyInstaller to find all modules
import gui
import gui.main_window
import gui.sql_editor
import gui.connection_dialog
import gui.highlighter
import gui.table_info_dialog
import gui.table_data_browser_base
import gui.table_data_browser_widget
import gui.table_create_dialog
import gui.table_modify_dialog
import gui.sql_history_dialog
import core
import core.connection
import core.workers
import utils
import utils.encryption

from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Check for required dependencies
    try:
        import cryptography
    except ImportError:
        print("请安装cryptography库: pip install cryptography")
        sys.exit(1)

    try:
        import pymysql
    except ImportError:
        print("请安装pymysql库: pip install pymysql")
        sys.exit(1)

    try:
        from PyQt6 import QtWidgets
    except ImportError:
        print("请安装PyQt6库: pip install PyQt6")
        sys.exit(1)

    # Create and run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

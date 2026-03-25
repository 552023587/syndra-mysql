#!/usr/bin/env python3
"""Test all imports after adding table name completion."""

try:
    from utils.encryption import EncryptionManager
    print('[OK] utils.encryption imported OK')

    from core.workers import TestConnectionWorker, DatabaseWorker
    print('[OK] core.workers imported OK')

    from core.connection import ConnectionManager
    print('[OK] core.connection imported OK')

    from gui.highlighter import SqlHighlighter
    print('[OK] gui.highlighter imported OK')

    from gui.sql_editor import SqlTextEdit
    print('[OK] gui.sql_editor imported OK')

    # Test table completion methods
    editor = SqlTextEdit(None)
    editor.set_table_names(['users', 'products'])
    print('[OK] SqlTextEdit set_table_names method works')

    editor.add_table_names(['orders'])
    print('[OK] SqlTextEdit add_table_names method works')

    editor.clear_table_names()
    print('[OK] SqlTextEdit clear_table_names method works')

    from gui.connection_dialog import DBConnectionDialog
    print('[OK] gui.connection_dialog imported OK')

    from gui.table_info_dialog import TableInfoDialog
    print('[OK] gui.table_info_dialog imported OK')

    from gui.table_data_browser import TableDataBrowser, BaseTableDataBrowser
    print('[OK] gui.table_data_browser imported OK')

    from gui.table_data_browser_widget import TableDataBrowserWidget
    print('[OK] gui.table_data_browser_widget imported OK')

    from gui.main_window import MainWindow
    print('[OK] gui.main_window imported OK')

    from main import main
    print('[OK] main imported OK')

    print()
    print('All imports successful! Table name auto-completion added.')

except ImportError as e:
    print(f'\n[ERROR] Import error: {e}')
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f'\n[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()

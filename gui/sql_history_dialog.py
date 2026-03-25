"""
SQL History and Saved Queries Dialog.

This module provides a dialog for viewing SQL execution history
and managing saved commonly used queries.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QWidget,
    QPushButton, QTextEdit, QMessageBox, QSplitter, QTabWidget,
    QDialogButtonBox, QLabel, QInputDialog
)
from PyQt6.QtCore import Qt
import json
import os


class SqlHistoryDialog(QDialog):
    """
    Dialog for viewing SQL execution history and saved queries.

    Provides two tabs:
    - History: Recently executed SQL statements
    - Saved: User saved commonly used queries
    """

    def __init__(self, history_file: str, parent=None):
        """
        Initialize the dialog.

        Args:
            history_file: Path to the JSON file storing history and saved queries
            parent: Parent widget
        """
        super().__init__(parent)
        self.history_file = history_file
        self.setWindowTitle("📜 SQL历史与保存查询")
        self.setModal(True)
        self.resize(700, 500)
        self.selected_sql = ""

        self.load_data()
        self.setup_ui()

    def load_data(self):
        """Load history and saved queries from file."""
        self.history = []
        self.saved = []

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])
                    self.saved = data.get('saved', [])
            except Exception:
                pass

        # Keep only last 50 history items
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def save_data(self):
        """Save history and saved queries to file."""
        data = {
            'history': self.history,
            'saved': self.saved
        }

        try:
            directory = os.path.dirname(self.history_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存失败: {str(e)}")

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Tab widget
        tabs = QTabWidget()

        # History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # History list
        self.history_list = QListWidget()
        for item in reversed(self.history):
            # Truncate for display
            display = item[:80].replace('\n', ' ')
            if len(item) > 80:
                display += '...'
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

        self.history_list.itemSelectionChanged.connect(self.on_history_selection)
        splitter.addWidget(self.history_list)

        # Preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("SQL预览:"))
        self.history_preview = QTextEdit()
        self.history_preview.setReadOnly(True)
        self.history_preview.setPlaceholderText("选择一条历史记录查看详情")
        preview_layout.addWidget(self.history_preview)

        # Buttons for history
        history_btn_layout = QHBoxLayout()
        use_btn = QPushButton(" 使用此SQL ")
        use_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
        """)
        use_btn.clicked.connect(self.use_selected_history)
        clear_btn = QPushButton(" 清空历史 ")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        history_btn_layout.addStretch()
        history_btn_layout.addWidget(use_btn)
        history_btn_layout.addWidget(clear_btn)
        preview_layout.addLayout(history_btn_layout)

        splitter.addWidget(preview_widget)
        splitter.setSizes([300, 200])

        history_layout.addWidget(splitter)
        tabs.addTab(history_widget, "📜 历史记录")

        # Saved tab
        saved_widget = QWidget()
        saved_layout = QVBoxLayout(saved_widget)

        saved_splitter = QSplitter(Qt.Orientation.Vertical)

        # Saved list
        self.saved_list = QListWidget()
        for item in self.saved:
            name = item.get('name', 'Unnamed')
            display = f"{name}"
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.saved_list.addItem(list_item)

        self.saved_list.itemSelectionChanged.connect(self.on_saved_selection)
        saved_splitter.addWidget(self.saved_list)

        # Preview
        saved_preview_widget = QWidget()
        saved_preview_layout = QVBoxLayout(saved_preview_widget)
        saved_preview_layout.addWidget(QLabel("SQL内容:"))
        self.saved_preview = QTextEdit()
        self.saved_preview.setReadOnly(True)
        self.saved_preview.setPlaceholderText("选择一个保存的查询查看详情")
        saved_preview_layout.addWidget(self.saved_preview)

        # Buttons
        saved_btn_layout = QHBoxLayout()
        save_use_btn = QPushButton(" 使用此SQL ")
        save_save_btn = QPushButton(" 保存当前SQL ")
        delete_save_btn = QPushButton(" 删除 ")

        save_use_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
        """)
        save_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #337ab7;
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #286090;
            }
        """)
        delete_save_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)

        save_use_btn.clicked.connect(self.use_selected_saved)
        delete_save_btn.clicked.connect(self.delete_selected_saved)

        saved_btn_layout.addStretch()
        saved_btn_layout.addWidget(save_use_btn)
        saved_btn_layout.addWidget(delete_save_btn)
        saved_preview_layout.addLayout(saved_btn_layout)

        saved_splitter.addWidget(saved_preview_widget)
        saved_splitter.setSizes([300, 200])

        saved_layout.addWidget(saved_splitter)
        tabs.addTab(saved_widget, "⭐ 保存的查询")

        layout.addWidget(tabs)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def on_history_selection(self):
        """Handle history list selection change."""
        items = self.history_list.selectedItems()
        if not items:
            self.history_preview.clear()
            return
        item = items[0]
        sql = item.data(Qt.ItemDataRole.UserRole)
        self.history_preview.setPlainText(sql)

    def on_saved_selection(self):
        """Handle saved list selection change."""
        items = self.saved_list.selectedItems()
        if not items:
            self.saved_preview.clear()
            return
        item = items[0]
        data = item.data(Qt.ItemDataRole.UserRole)
        sql = data.get('sql', '')
        self.saved_preview.setPlainText(sql)

    def use_selected_history(self):
        """Use the selected SQL from history."""
        items = self.history_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "警告", "请先选择一条历史记录")
            return
        item = items[0]
        self.selected_sql = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def use_selected_saved(self):
        """Use the selected SQL from saved queries."""
        items = self.saved_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "警告", "请先选择一个保存的查询")
            return
        item = items[0]
        data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_sql = data.get('sql', '')
        self.accept()

    def clear_history(self):
        """Clear all history."""
        confirm = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有SQL历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.history_list.clear()
            self.history_preview.clear()
            self.save_data()

    def delete_selected_saved(self):
        """Delete selected saved query."""
        items = self.saved_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "警告", "请先选择要删除的查询")
            return

        confirm = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个保存的查询吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        row = self.saved_list.row(items[0])
        del self.saved[row]
        self.saved_list.takeItem(row)
        self.saved_preview.clear()
        self.save_data()

    def add_saved_query(self, name: str, sql: str):
        """Add a new saved query."""
        self.saved.append({'name': name, 'sql': sql})
        list_item = QListWidgetItem(name)
        list_item.setData(Qt.ItemDataRole.UserRole, {'name': name, 'sql': sql})
        self.saved_list.addItem(list_item)
        self.save_data()

    def add_sql_to_history(self, sql: str):
        """Add a SQL statement to history."""
        # Don't add duplicate empty or whitespace only
        cleaned = sql.strip()
        if not cleaned:
            return

        # Remove if already exists (move to end)
        self.history = [h for h in self.history if h.strip() != cleaned]
        self.history.append(cleaned)

        # Keep only last 50
        if len(self.history) > 50:
            self.history = self.history[-50:]

        self.save_data()

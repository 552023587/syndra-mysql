"""
SQL Text Editor - SQL editor with auto-completion support.

This module contains the SqlTextEdit class that extends QTextEdit with
SQL syntax highlighting and auto-completion functionality.
"""

from PyQt6.QtWidgets import QTextEdit, QCompleter
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QKeyEvent, QTextCursor
from gui.highlighter import SqlHighlighter


class SqlTextEdit(QTextEdit):
    """
    SQL text editor with syntax highlighting and auto-completion.

    Extends QTextEdit to provide:
    - SQL syntax coloring via SqlHighlighter
    - Auto-completion for SQL keywords, functions, and table names
    """

    def __init__(self, parent=None):
        """
        Initialize the SQL text editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Set up syntax highlighter
        self.highlighter = SqlHighlighter(self.document())

        # Set up auto-completer
        self.completer = QCompleter()
        # Case-insensitive matching for auto-completion
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setModelSorting(QCompleter.ModelSorting.UnsortedModel)

        # Store table names for auto-completion
        self._table_names = []

        # Combine keywords, functions, and table names for auto-completion
        self._rebuild_completion_model()

        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)

        # Track completion state
        self.completion_prefix = ""
        self.completion_popup_shown = False

    def _rebuild_completion_model(self):
        """Rebuild the completion model with current keywords, functions, and table names."""
        all_completions = SqlHighlighter.KEYWORDS + SqlHighlighter.FUNCTIONS + self._table_names
        self.completer.setModel(QStringListModel(all_completions))

    def set_table_names(self, table_names: list[str]):
        """
        Set the table names for auto-completion.

        Call this after connecting to a database to update the
        list of available table names for auto-completion.

        Args:
            table_names: List of table names to add to auto-completion
        """
        self._table_names = table_names
        self._rebuild_completion_model()

    def add_table_names(self, table_names: list[str]):
        """
        Add additional table names to auto-completion.

        Args:
            table_names: List of additional table names to add
        """
        self._table_names.extend(table_names)
        self._rebuild_completion_model()

    def clear_table_names(self):
        """Clear all table names from auto-completion."""
        self._table_names = []
        self._rebuild_completion_model()

    def insert_completion(self, completion: str):
        """
        Insert the selected completion into the editor.

        Args:
            completion: The completed text to insert
        """
        tc = self.textCursor()
        # Calculate how much of the word we need to add
        extra = len(completion) - len(self.completion_prefix)
        # Move to the end of the current word and insert the completion
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events for auto-completion.

        Intercepts key events to trigger auto-completion when typing
        alphanumeric characters.

        Args:
            event: Key event to handle
        """
        if self.completer.popup().isVisible():
            # If popup is visible and user presses enter or tab, accept completion
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                event.ignore()
                self.completer.popup().hide()
                return

        # Hide popup when space is pressed
        if event.key() == Qt.Key.Key_Space:
            self.completer.popup().hide()

        # Trigger auto-completion when typing alphanumeric characters
        if event.text().isalnum():
            self.handle_auto_completion(event)
        else:
            super().keyPressEvent(event)

    def handle_auto_completion(self, event: QKeyEvent):
        """
        Handle auto-completion logic when a character is typed.

        Extracts the word under the cursor and shows completion popup
        if the word is long enough (2+ characters).

        Args:
            event: Key event that triggered auto-completion
        """
        tc = self.textCursor()
        # Select the word under the cursor
        tc.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.MoveAnchor)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)

        word_under_cursor = tc.selectedText()

        # Get current line and cursor position
        line_text = self.textCursor().block().text()
        cursor_pos = self.textCursor().positionInBlock()
        prefix = ""

        # Walk backwards from cursor to get the full prefix (handles underscores)
        for i in range(cursor_pos - 1, -1, -1):
            if i >= len(line_text):
                break
            char = line_text[i]
            # Alphanumeric and underscores are part of the word
            if char.isalnum() or char == '_':
                prefix = char + prefix
            else:
                break

        # Only show auto-completion if we have at least 2 characters
        if len(prefix) > 1:
            self.completion_prefix = prefix
            self.completer.setCompletionPrefix(prefix)

            popup = self.completer.popup()
            # Select the first item in the popup
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))

            # Position popup at the cursor
            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

        # Continue with normal key processing
        super().keyPressEvent(event)

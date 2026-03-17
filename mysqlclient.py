import sys
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pymysql
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton, QLineEdit,
    QTabWidget, QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
    QInputDialog, QDialog, QFormLayout, QCheckBox, QProgressBar,
    QSplitter, QListWidget, QListWidgetItem, QCompleter, QMenu,
    QHeaderView, QSpinBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel, QTimer
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QKeyEvent,
    QKeySequence, QTextCursor, QAction
)
import threading
import socket
from contextlib import closing
import re

class SqlHighlighter(QSyntaxHighlighter):
    """SQL语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # 函数格式
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#800080"))
        function_format.setFontWeight(QFont.Weight.Bold)
        
        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        
        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)
        
        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF0000"))
        
        # 正则表达式模式
        self.rules = [
            # 关键字
            (r'\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|DATABASE|INDEX|PRIMARY|KEY|FOREIGN|REFERENCES|ON|SET|VALUES|INTO|JOIN|INNER|LEFT|RIGHT|OUTER|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|DISTINCT|UNION|ALL|AS|IS|NULL|NOT|AND|OR|IN|EXISTS|BETWEEN|LIKE|CASE|WHEN|THEN|ELSE|END|IF|FOR|DO|BEGIN|COMMIT|ROLLBACK|TRUNCATE|USE|SHOW|DESCRIBE|EXPLAIN|PROCEDURE|FUNCTION|VIEW|TRIGGER|EVENT|LOGFILE|MASTER|SLAVE|REPLICATE|START|STOP|RESET|PURGE|CHANGE|GRANT|REVOKE|USER|PASSWORD|WITH|GRANT|OPTION|REPLACE|IGNORE|DUPLICATE|KEY|AUTO_INCREMENT|ENGINE|CHARSET|COLLATE|COMMENT|DEFAULT|CURRENT_TIMESTAMP|NOW|CURDATE|CURTIME|DATE|TIME|DATETIME|TIMESTAMP|YEAR|MONTH|DAY|HOUR|MINUTE|SECOND|MICROSECOND|TINYINT|SMALLINT|MEDIUMINT|INT|INTEGER|BIGINT|DECIMAL|NUMERIC|FLOAT|DOUBLE|REAL|BIT|BOOLEAN|BOOL|SERIAL|DATE|TIME|DATETIME|TIMESTAMP|YEAR|CHAR|VARCHAR|BINARY|VARBINARY|TINYBLOB|BLOB|MEDIUMBLOB|LONGBLOB|TINYTEXT|TEXT|MEDIUMTEXT|LONGTEXT|ENUM|SET|GEOMETRY|POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)\b', keyword_format),
            
            # 函数
            (r'\b(ABS|ACOS|ADDDATE|ADDTIME|AES_DECRYPT|AES_ENCRYPT|ASCII|ASIN|ATAN|ATAN2|AVG|BENCHMARK|BIN|BIT_AND|BIT_COUNT|BIT_LENGTH|BIT_OR|BIT_XOR|CAST|CEIL|CEILING|CHAR_LENGTH|CHARACTER_LENGTH|CHARSET|COALESCE|COERCIBILITY|COLLATION|COMPRESS|CONCAT|CONCAT_WS|CONNECTION_ID|CONV|CONVERT_TZ|COS|COT|COUNT|CRC32|CURDATE|CURRENT_DATE|CURRENT_TIME|CURRENT_TIMESTAMP|CURRENT_USER|CURTIME|DATABASE|DATE_ADD|DATE_FORMAT|DATE_SUB|DATEDIFF|DAY|DAYNAME|DAYOFMONTH|DAYOFWEEK|DAYOFYEAR|DECODE|DEGREES|DES_DECRYPT|DES_ENCRYPT|ELT|ENCODE|ENCRYPT|EXP|EXPORT_SET|EXTRACT|FIELD|FIND_IN_TABLE|FLOOR|FORMAT|FOUND_ROWS|FROM_DAYS|FROM_UNIXTIME|GET_FORMAT|GET_LOCK|GREATEST|GROUP_CONCAT|HEX|HOUR|IF|IFNULL|INET_ATON|INET_NTOA|INSERT|INSTR|INTERVAL|IS_FREE_LOCK|IS_USED_LOCK|LAST_DAY|LAST_INSERT_ID|LCASE|LEAST|LEFT|LENGTH|LN|LOAD_FILE|LOCALTIME|LOCALTIMESTAMP|LOCATE|LOG|LOG10|LOG2|LOWER|LPAD|LTRIM|MAKE_SET|MAKEDATE|MAKETIME|MASTER_POS_WAIT|MAX|MD5|MICROSECOND|MIN|MINUTE|MOD|MONTH|MONTHNAME|NAME_CONST|NOW|NULLIF|OCT|OCTET_LENGTH|OLD_PASSWORD|ORD|PASSWORD|PERIOD_ADD|PERIOD_DIFF|PI|POSITION|POW|POWER|QUARTER|RADIANS|RAND|RELEASE_LOCK|REPEAT|REPLACE|REVERSE|RIGHT|ROUND|ROW_COUNT|RTRIM|SEC_TO_TIME|SECOND|SESSION_USER|SHA|SHA1|SIGN|SIN|SLEEP|SOUNDEX|SPACE|SQRT|STD|STDDEV|STDDEV_POP|STDDEV_SAMP|STR_TO_DATE|STRCMP|SUBDATE|SUBSTRING|SUBSTRING_INDEX|SUBTIME|SUM|SYSDATE|SYSTEM_USER|TAN|TIME|TIME_FORMAT|TIME_TO_SEG|TIMEDIFF|TIMESTAMP|TIMESTAMPADD|TIMESTAMPDIFF|TO_DAYS|TRIM|TRUNCATE|UCASE|UNCOMPRESS|UNCOMPRESSED_LENGTH|UNHEX|UNIX_TIMESTAMP|UPPER|USER|UTC_DATE|UTC_TIME|UTC_TIMESTAMP|UUID|VALUES|VAR_POP|VAR_SAMP|VARIANCE|VERSION|WEEK|WEEKDAY|WEEKOFYEAR|YEAR|YEARWEEK)\b', function_format),
            
            # 字符串
            (r"'(?:[^'\\]|\\.)*'", string_format),
            (r'"(?:[^"\\]|\\.)*"', string_format),
            
            # 注释
            (r'--.*', comment_format),
            (r'/\*.*?\*/', comment_format),
            
            # 数字
            (r'\b\d+\.?\d*\b', number_format),
        ]
        
        # 关键字列表（用于自动补全）
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'DATABASE', 'INDEX', 'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'ON', 'SET',
            'VALUES', 'INTO', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ORDER', 'BY', 'GROUP',
            'HAVING', 'LIMIT', 'OFFSET', 'DISTINCT', 'UNION', 'ALL', 'AS', 'IS', 'NULL', 'NOT',
            'AND', 'OR', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'IF', 'FOR', 'DO', 'BEGIN', 'COMMIT', 'ROLLBACK', 'TRUNCATE', 'USE', 'SHOW', 'DESCRIBE',
            'EXPLAIN', 'PROCEDURE', 'FUNCTION', 'VIEW', 'TRIGGER', 'EVENT', 'LOGFILE', 'MASTER',
            'SLAVE', 'REPLICATE', 'START', 'STOP', 'RESET', 'PURGE', 'CHANGE', 'GRANT', 'REVOKE',
            'USER', 'PASSWORD', 'WITH', 'GRANT', 'OPTION', 'REPLACE', 'IGNORE', 'DUPLICATE', 'KEY',
            'AUTO_INCREMENT', 'ENGINE', 'CHARSET', 'COLLATE', 'COMMENT', 'DEFAULT', 'CURRENT_TIMESTAMP',
            'NOW', 'CURDATE', 'CURTIME', 'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'YEAR', 'MONTH',
            'DAY', 'HOUR', 'MINUTE', 'SECOND', 'MICROSECOND', 'TINYINT', 'SMALLINT', 'MEDIUMINT',
            'INT', 'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL', 'BIT',
            'BOOLEAN', 'BOOL', 'SERIAL', 'DATE', 'TIME', 'DATETIME', 'TIMESTAMP', 'YEAR', 'CHAR',
            'VARCHAR', 'BINARY', 'VARBINARY', 'TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB',
            'TINYTEXT', 'TEXT', 'MEDIUMTEXT', 'LONGTEXT', 'ENUM', 'SET', 'GEOMETRY', 'POINT',
            'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION'
        ]
        
        # 函数列表（用于自动补全）
        self.functions = [
            'ABS', 'ACOS', 'ADDDATE', 'ADDTIME', 'AES_DECRYPT', 'AES_ENCRYPT', 'ASCII', 'ASIN',
            'ATAN', 'ATAN2', 'AVG', 'BENCHMARK', 'BIN', 'BIT_AND', 'BIT_COUNT', 'BIT_LENGTH',
            'BIT_OR', 'BIT_XOR', 'CAST', 'CEIL', 'CEILING', 'CHAR_LENGTH', 'CHARACTER_LENGTH',
            'CHARSET', 'COALESCE', 'COERCIBILITY', 'COLLATION', 'COMPRESS', 'CONCAT', 'CONCAT_WS',
            'CONNECTION_ID', 'CONV', 'CONVERT_TZ', 'COS', 'COT', 'COUNT', 'CRC32', 'CURDATE',
            'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'CURRENT_USER', 'CURTIME', 'DATABASE',
            'DATE_ADD', 'DATE_FORMAT', 'DATE_SUB', 'DATEDIFF', 'DAY', 'DAYNAME', 'DAYOFMONTH',
            'DAYOFWEEK', 'DAYOFYEAR', 'DECODE', 'DEGREES', 'DES_DECRYPT', 'DES_ENCRYPT', 'ELT',
            'ENCODE', 'ENCRYPT', 'EXP', 'EXPORT_SET', 'EXTRACT', 'FIELD', 'FIND_IN_TABLE', 'FLOOR',
            'FORMAT', 'FOUND_ROWS', 'FROM_DAYS', 'FROM_UNIXTIME', 'GET_FORMAT', 'GET_LOCK',
            'GREATEST', 'GROUP_CONCAT', 'HEX', 'HOUR', 'IF', 'IFNULL', 'INET_ATON', 'INET_NTOA',
            'INSERT', 'INSTR', 'INTERVAL', 'IS_FREE_LOCK', 'IS_USED_LOCK', 'LAST_DAY', 'LAST_INSERT_ID',
            'LCASE', 'LEAST', 'LEFT', 'LENGTH', 'LN', 'LOAD_FILE', 'LOCALTIME', 'LOCALTIMESTAMP',
            'LOCATE', 'LOG', 'LOG10', 'LOG2', 'LOWER', 'LPAD', 'LTRIM', 'MAKE_SET', 'MAKEDATE',
            'MAKETIME', 'MASTER_POS_WAIT', 'MAX', 'MD5', 'MICROSECOND', 'MIN', 'MINUTE', 'MOD',
            'MONTH', 'MONTHNAME', 'NAME_CONST', 'NOW', 'NULLIF', 'OCT', 'OCTET_LENGTH', 'OLD_PASSWORD',
            'ORD', 'PASSWORD', 'PERIOD_ADD', 'PERIOD_DIFF', 'PI', 'POSITION', 'POW', 'POWER',
            'QUARTER', 'RADIANS', 'RAND', 'RELEASE_LOCK', 'REPEAT', 'REPLACE', 'REVERSE', 'RIGHT',
            'ROUND', 'ROW_COUNT', 'RTRIM', 'SEC_TO_TIME', 'SECOND', 'SESSION_USER', 'SHA', 'SHA1',
            'SIGN', 'SIN', 'SLEEP', 'SOUNDEX', 'SPACE', 'SQRT', 'STD', 'STDDEV', 'STDDEV_POP',
            'STDDEV_SAMP', 'STR_TO_DATE', 'STRCMP', 'SUBDATE', 'SUBSTRING', 'SUBSTRING_INDEX',
            'SUBTIME', 'SUM', 'SYSDATE', 'SYSTEM_USER', 'TAN', 'TIME', 'TIME_FORMAT', 'TIME_TO_SEG',
            'TIMEDIFF', 'TIMESTAMP', 'TIMESTAMPADD', 'TIMESTAMPDIFF', 'TO_DAYS', 'TRIM', 'TRUNCATE',
            'UCASE', 'UNCOMPRESS', 'UNCOMPRESSED_LENGTH', 'UNHEX', 'UNIX_TIMESTAMP', 'UPPER', 'USER',
            'UTC_DATE', 'UTC_TIME', 'UTC_TIMESTAMP', 'UUID', 'VALUES', 'VAR_POP', 'VAR_SAMP',
            'VARIANCE', 'VERSION', 'WEEK', 'WEEKDAY', 'WEEKOFYEAR', 'YEAR', 'YEARWEEK'
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

class SqlTextEdit(QTextEdit):
    """支持自动补全的SQL编辑器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置语法高亮
        self.highlighter = SqlHighlighter(self.document())
        
        # 设置自动补全
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setModelSorting(QCompleter.ModelSorting.UnsortedModel)
        
        # 设置关键词和函数
        all_items = SqlHighlighter().keywords + SqlHighlighter().functions
        self.completer.setModel(QStringListModel(all_items))
        
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)
        
        self.completion_prefix = ""
        self.completion_popup_shown = False
        
    def insert_completion(self, completion):
        """插入补全文本"""
        tc = self.textCursor()
        extra = len(completion) - len(self.completion_prefix)
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)
        
    def keyPressEvent(self, event: QKeyEvent):
        """处理按键事件"""
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                event.ignore()
                self.completer.popup().hide()
                return
        
        # 检查是否需要触发自动补全
        if event.key() == Qt.Key.Key_Space:
            self.completer.popup().hide()
        
        # 检查是否是字母数字字符，触发自动补全
        if event.text().isalnum():
            self.handle_auto_completion(event)
        else:
            super().keyPressEvent(event)
    
    def handle_auto_completion(self, event: QKeyEvent):
        """处理自动补全逻辑"""
        tc = self.textCursor()
        tc.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.MoveAnchor)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)
        
        word_under_cursor = tc.selectedText()
        
        # 获取光标前的单词
        line_text = self.textCursor().block().text()
        cursor_pos = self.textCursor().positionInBlock()
        prefix = ""
        
        # 查找光标前的单词
        for i in range(cursor_pos - 1, -1, -1):
            if i >= len(line_text):
                break
            char = line_text[i]
            if char.isalnum() or char == '_':
                prefix = char + prefix
            else:
                break
        
        if len(prefix) > 1:
            self.completion_prefix = prefix
            self.completer.setCompletionPrefix(prefix)
            
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            
            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()
        
        super().keyPressEvent(event)

class TestConnectionWorker(QThread):
    test_result = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            # 非SSH模式：直接测试MySQL连接
            connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config.get('database', ''),
                charset='utf8mb4',
                connect_timeout=10
            )
            
            # 尝试执行简单查询验证连接
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()
                
            connection.close()
            
            # 成功
            self.test_result.emit(True, f"连接成功！MySQL版本: {version[0] if version else 'Unknown'}")
            
        except Exception as e:
            self.test_result.emit(False, f"连接失败: {str(e)}")

class DBConnectionDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("数据库连接")
        self.setGeometry(300, 300, 400, 400)
        
        layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("3306")
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.database_edit = QLineEdit()
        self.use_ssh_check = QCheckBox("使用SSH隧道")
        
        layout.addRow("连接名:", self.name_edit)
        layout.addRow("主机:", self.host_edit)
        layout.addRow("端口:", self.port_edit)
        layout.addRow("用户名:", self.username_edit)
        layout.addRow("密码:", self.password_edit)
        layout.addRow("数据库:", self.database_edit)
        layout.addRow(self.use_ssh_check)
        
        self.use_ssh_check.stateChanged.connect(self.toggle_ssh_options)
        
        self.ssh_config_widget = QWidget()
        ssh_layout = QFormLayout()
        self.ssh_host_edit = QLineEdit()
        self.ssh_port_edit = QLineEdit("22")
        self.ssh_username_edit = QLineEdit()
        self.ssh_password_edit = QLineEdit()
        self.ssh_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        ssh_layout.addRow("SSH主机:", self.ssh_host_edit)
        ssh_layout.addRow("SSH端口:", self.ssh_port_edit)
        ssh_layout.addRow("SSH用户名:", self.ssh_username_edit)
        ssh_layout.addRow("SSH密码:", self.ssh_password_edit)
        self.ssh_config_widget.setLayout(ssh_layout)
        self.ssh_config_widget.setVisible(False)
        
        layout.addRow(self.ssh_config_widget)
        
        # 测试连接按钮和状态显示
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_status_label = QLabel("未测试")
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status_label)
        layout.addRow(test_layout)
        layout.addRow(self.test_progress)
        
        # 确定取消按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("连接")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
        
        # 如果传入配置，则填充表单
        if config:
            self.fill_form(config)

    def fill_form(self, config):
        """填充表单数据"""
        self.name_edit.setText(config.get('name', ''))
        self.host_edit.setText(config.get('host', ''))
        self.port_edit.setText(str(config.get('port', 3306)))
        self.username_edit.setText(config.get('username', ''))
        self.password_edit.setText(config.get('password', ''))
        self.database_edit.setText(config.get('database', ''))
        self.use_ssh_check.setChecked(config.get('use_ssh', False))
        
        if config.get('use_ssh') and 'ssh_config' in config:
            ssh_config = config['ssh_config']
            self.ssh_host_edit.setText(ssh_config.get('host', ''))
            self.ssh_port_edit.setText(str(ssh_config.get('port', 22)))
            self.ssh_username_edit.setText(ssh_config.get('username', ''))
            self.ssh_password_edit.setText(ssh_config.get('password', ''))

    def toggle_ssh_options(self, state):
        self.ssh_config_widget.setVisible(state == Qt.CheckState.Checked.value)

    def test_connection(self):
        config = self.get_config()
        if not config['host'] or not config['username'] or not config['password']:
            QMessageBox.warning(self, "警告", "请填写必要的连接信息")
            return
            
        # 验证端口号
        try:
            port = int(config['port'])
            if not (1 <= port <= 65535):
                raise ValueError("端口号必须在1-65535之间")
        except ValueError as e:
            QMessageBox.warning(self, "警告", f"端口号无效: {e}")
            return
            
        # 验证SSH端口（如果启用SSH）
        if config.get('use_ssh') and 'ssh_config' in config:
            try:
                ssh_port = int(config['ssh_config']['port'])
                if not (1 <= ssh_port <= 65535):
                    raise ValueError("SSH端口号必须在1-65535之间")
            except ValueError as e:
                QMessageBox.warning(self, "警告", f"SSH端口号无效: {e}")
                return
        
        # 禁用测试按钮，显示进度条
        self.test_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # 不确定进度
        self.test_status_label.setText("正在测试...")
        
        # 创建测试线程
        self.test_worker = TestConnectionWorker(config)
        self.test_worker.test_result.connect(self.on_test_complete)
        self.test_worker.start()

    def on_test_complete(self, success, message):
        # 恢复界面
        self.test_btn.setEnabled(True)
        self.test_progress.setVisible(False)
        
        if success:
            self.test_status_label.setText(message)
            self.test_status_label.setStyleSheet("color: green;")
        else:
            self.test_status_label.setText(message)
            self.test_status_label.setStyleSheet("color: red;")

    def get_config(self):
        config = {
            'name': self.name_edit.text(),
            'host': self.host_edit.text(),
            'port': int(self.port_edit.text()) if self.port_edit.text().isdigit() else 3306,
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'database': self.database_edit.text(),
            'use_ssh': self.use_ssh_check.isChecked()
        }
        
        if config['use_ssh']:
            config['ssh_config'] = {
                'host': self.ssh_host_edit.text(),
                'port': int(self.ssh_port_edit.text()) if self.ssh_port_edit.text().isdigit() else 22,
                'username': self.ssh_username_edit.text(),
                'password': self.ssh_password_edit.text()
            }
        
        return config

class DatabaseWorker(QThread):
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, connection_info):
        super().__init__()
        self.connection_info = connection_info
        self.connection = None

    def run(self):
        try:
            # 连接数据库
            self.connection = pymysql.connect(
                host=self.connection_info['host'],
                port=self.connection_info['port'],
                user=self.connection_info['username'],
                password=self.connection_info['password'],
                database=self.connection_info.get('database', ''),
                charset='utf8mb4',
                connect_timeout=10
            )

            # 获取数据库列表
            databases = []
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                results = cursor.fetchall()
                for row in results:
                    db_name = row[0]
                    if db_name not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                        databases.append(db_name)

            # 获取每个数据库的表信息
            db_tables = {}
            for db in databases:
                tables = []
                self.connection.select_db(db)
                with self.connection.cursor() as cursor:
                    cursor.execute("SHOW TABLES;")
                    results = cursor.fetchall()
                    for row in results:
                        table_name = row[0]
                        tables.append(table_name)
                db_tables[db] = tables

            self.result_ready.emit({
                'databases': databases,
                'tables': db_tables,
                'connection': self.connection
            })

        except Exception as e:
            self.error_occurred.emit(str(e))

    def close_connection(self):
        if self.connection:
            self.connection.close()

class TableInfoDialog(QDialog):
    def __init__(self, table_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表结构")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(['字段', '类型', '空', '键', '默认', '额外'])
        
        self.table_widget.setRowCount(len(table_info))
        for i, col in enumerate(table_info):
            for j, value in enumerate(col):
                item = QTableWidgetItem(str(value) if value else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, j, item)
        
        layout.addWidget(self.table_widget)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class TableDataBrowser(QDialog):
    """表数据浏览器对话框"""
    def __init__(self, connection, database, table, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"数据浏览 - {database}.{table}")
        self.setGeometry(200, 200, 1000, 600)
        
        self.connection = connection
        self.database = database
        self.table = table
        self.current_page = 0
        self.page_size = 20
        self.total_rows = 0
        self.current_data = []
        
        layout = QVBoxLayout()
        
        # 分页控制
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel("第 1 页")
        self.total_pages_label = QLabel("共 0 页")
        self.page_input = QSpinBox()
        self.page_input.setRange(1, 1)
        self.page_input.setValue(1)
        self.go_btn = QPushButton("跳转")
        
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.go_btn.clicked.connect(self.go_to_page)
        self.page_input.returnPressed.connect(self.go_to_page)
        
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.total_pages_label)
        pagination_layout.addWidget(QLabel("跳转到:"))
        pagination_layout.addWidget(self.page_input)
        pagination_layout.addWidget(self.go_btn)
        pagination_layout.addStretch()
        
        # 数据表格
        self.table_widget = QTableWidget()
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addLayout(pagination_layout)
        layout.addWidget(self.table_widget)
        
        self.setLayout(layout)
        
        # 加载第一页数据
        self.load_data()

    def load_data(self):
        try:
            self.connection.select_db(self.database)
            with self.connection.cursor() as cursor:
                # 获取总行数
                cursor.execute(f"SELECT COUNT(*) FROM `{self.table}`;")
                self.total_rows = cursor.fetchone()[0]
                
                # 计算总页数
                total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
                self.page_input.setMaximum(total_pages)
                self.total_pages_label.setText(f"共 {total_pages} 页")
                
                # 获取当前页数据
                offset = self.current_page * self.page_size
                cursor.execute(f"SELECT * FROM `{self.table}` LIMIT {self.page_size} OFFSET {offset};")
                self.current_data = cursor.fetchall()
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description]
                
                # 更新表格
                self.update_table(columns, self.current_data)
                
                # 更新页码显示
                self.page_label.setText(f"第 {self.current_page + 1} 页")
                self.page_input.setValue(self.current_page + 1)
                
                # 更新按钮状态
                self.prev_btn.setEnabled(self.current_page > 0)
                self.next_btn.setEnabled((self.current_page + 1) * self.page_size < self.total_rows)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")

    def update_table(self, columns, data):
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.setRowCount(len(data))
        
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_widget.setItem(i, j, item)
        
        # 调整列宽
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_data()

    def go_to_page(self):
        target_page = self.page_input.value() - 1
        total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        
        if 0 <= target_page < total_pages:
            self.current_page = target_page
            self.load_data()
        else:
            QMessageBox.warning(self, "警告", f"页码超出范围 (1-{total_pages})")

    def show_context_menu(self, position):
        menu = QMenu()
        rename_action = menu.addAction("重命名表")
        delete_action = menu.addAction("删除表")
        design_action = menu.addAction("设计表")
        
        action = menu.exec(self.table_widget.mapToGlobal(position))
        
        if action == rename_action:
            self.rename_table()
        elif action == delete_action:
            self.delete_table()
        elif action == design_action:
            self.design_table()

    def rename_table(self):
        new_name, ok = QInputDialog.getText(self, "重命名表", "请输入新的表名:", QLineEdit.EchoMode.Normal, self.table)
        if ok and new_name:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"ALTER TABLE `{self.table}` RENAME TO `{new_name}`;")
                    self.connection.commit()
                    QMessageBox.information(self, "成功", f"表已重命名为: {new_name}")
                    self.table = new_name
                    self.setWindowTitle(f"数据浏览 - {self.database}.{self.table}")
                    # 重新加载数据
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")

    def delete_table(self):
        reply = QMessageBox.question(self, "确认删除", f"确定要删除表 '{self.table}' 吗？\n此操作不可撤销！", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE `{self.table}`;")
                    self.connection.commit()
                    QMessageBox.information(self, "成功", f"表 '{self.table}' 已删除")
                    self.close()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def design_table(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{self.table}`;")
                table_info = cursor.fetchall()
                
                dialog = TableInfoDialog(table_info, self)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法获取表结构: {str(e)}")

class ConnectionManager:
    """连接管理器，负责加密保存和加载连接配置"""
    def __init__(self, filename="connections.json"):
        self.filename = filename
        self.connections = {}
        self.password_key = self._generate_key()
        self.load_connections()
    
    def _generate_key(self):
        """生成用于加密/解密的密钥"""
        # 使用固定密码生成密钥（实际应用中应更安全）
        password = b"mysql_client_default_password_2023"
        salt = b"mysql_salt_2023"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _encrypt_password(self, password):
        """加密密码"""
        if not password:
            return ""
        f = Fernet(self.password_key)
        encrypted = f.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_password(self, encrypted_password):
        """解密密码"""
        if not encrypted_password:
            return ""
        try:
            f = Fernet(self.password_key)
            encrypted_bytes = base64.b64decode(encrypted_password.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            return ""
    
    def save_connections(self):
        """保存连接配置到JSON文件（加密密码）"""
        try:
            # 创建备份
            if os.path.exists(self.filename):
                backup_filename = self.filename + ".backup"
                os.rename(self.filename, backup_filename)
            
            # 加密连接信息
            connections_to_save = {}
            for name, config in self.connections.items():
                # 创建副本并加密密码
                config_copy = config.copy()
                config_copy['password'] = self._encrypt_password(config.get('password', ''))
                if 'ssh_config' in config_copy and 'password' in config_copy['ssh_config']:
                    ssh_config = config_copy['ssh_config'].copy()
                    ssh_config['password'] = self._encrypt_password(config_copy['ssh_config'].get('password', ''))
                    config_copy['ssh_config'] = ssh_config
                connections_to_save[name] = config_copy
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(connections_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存连接配置失败: {e}")
    
    def load_connections(self):
        """从JSON文件加载连接配置（解密密码）"""
        if not os.path.exists(self.filename):
            self.connections = {}
            return
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                connections = json.load(f)
            
            # 解密密码
            decrypted_connections = {}
            for name, config in connections.items():
                config_copy = config.copy()
                config_copy['password'] = self._decrypt_password(config.get('password', ''))
                if 'ssh_config' in config_copy and 'password' in config_copy['ssh_config']:
                    ssh_config = config_copy['ssh_config'].copy()
                    ssh_config['password'] = self._decrypt_password(config_copy['ssh_config'].get('password', ''))
                    config_copy['ssh_config'] = ssh_config
                decrypted_connections[name] = config_copy
            
            self.connections = decrypted_connections
        except Exception as e:
            print(f"加载连接配置失败: {e}")
            self.connections = {}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL客户端 - 增强版数据浏览")
        self.setGeometry(100, 100, 1400, 800)
        
        # 连接管理器
        self.conn_manager = ConnectionManager()
        
        # 数据库连接存储
        self.connections = {}
        self.current_connection = None
        self.current_tunnel = None
        
        # 创建主布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧树形视图
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # 连接按钮
        connect_btn = QPushButton("新建连接")
        connect_btn.clicked.connect(self.add_connection)
        left_layout.addWidget(connect_btn)
        
        # 已保存连接列表
        saved_conn_label = QLabel("已保存连接:")
        left_layout.addWidget(saved_conn_label)
        
        self.saved_conn_list = QListWidget()
        self.saved_conn_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_conn_list.customContextMenuRequested.connect(self.show_context_menu)
        self.refresh_saved_connections()
        left_layout.addWidget(self.saved_conn_list)
        
        # 数据库树
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel("数据库")
        self.db_tree.itemDoubleClicked.connect(self.tree_item_clicked)
        self.db_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.db_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        left_layout.addWidget(self.db_tree)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # SQL执行区域
        sql_label = QLabel("SQL查询:")
        right_layout.addWidget(sql_label)
        
        # 使用增强的SQL编辑器
        self.sql_editor = SqlTextEdit()
        self.sql_editor.setPlainText("SELECT * FROM ")
        right_layout.addWidget(self.sql_editor)
        
        execute_btn = QPushButton("执行SQL")
        execute_btn.clicked.connect(self.execute_sql)
        right_layout.addWidget(execute_btn)
        
        # 结果表格
        self.result_table = QTableWidget()
        right_layout.addWidget(self.result_table)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([300, 1100])
        
        self.setCentralWidget(splitter)
        
        # 菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        
        new_conn_action = file_menu.addAction('新建连接')
        new_conn_action.triggered.connect(self.add_connection)
        
        save_conns_action = file_menu.addAction('保存连接配置')
        save_conns_action.triggered.connect(self.save_connections_to_file)

    def refresh_saved_connections(self):
        """刷新已保存连接列表"""
        self.saved_conn_list.clear()
        for name in self.conn_manager.connections.keys():
            item = QListWidgetItem(name)
            self.saved_conn_list.addItem(item)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.saved_conn_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        connect_action = menu.addAction("连接")
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        
        action = menu.exec(self.saved_conn_list.mapToGlobal(position))
        
        if action == connect_action:
            self.connect_to_saved(item.text())
        elif action == edit_action:
            self.edit_saved_connection(item.text())
        elif action == delete_action:
            self.delete_saved_connection(item.text())

    def show_tree_context_menu(self, position):
        """显示树形视图右键菜单"""
        item = self.db_tree.itemAt(position)
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        item_type, item_name = item_data
        
        menu = QMenu()
        
        if item_type == 'table':
            # 表的右键菜单
            view_data_action = menu.addAction("查看数据")
            rename_action = menu.addAction("重命名表")
            delete_action = menu.addAction("删除表")
            design_action = menu.addAction("设计表")
            
            action = menu.exec(self.db_tree.mapToGlobal(position))
            
            if action == view_data_action:
                self.view_table_data(item.parent().text(0), item_name)
            elif action == rename_action:
                self.rename_table(item.parent().text(0), item_name)
            elif action == delete_action:
                self.delete_table(item.parent().text(0), item_name)
            elif action == design_action:
                self.design_table(item.parent().text(0), item_name)
        elif item_type == 'database':
            # 数据库的右键菜单
            create_table_action = menu.addAction("创建表")
            delete_db_action = menu.addAction("删除数据库")
            
            action = menu.exec(self.db_tree.mapToGlobal(position))
            
            if action == create_table_action:
                self.create_table(item_name)
            elif action == delete_db_action:
                self.delete_database(item_name)
        elif item_type == 'connection':
            # 连接的右键菜单
            refresh_action = menu.addAction("刷新")
            disconnect_action = menu.addAction("断开连接")
            
            action = menu.exec(self.db_tree.mapToGlobal(position))
            
            if action == refresh_action:
                self.refresh_connection(item_name)
            elif action == disconnect_action:
                self.disconnect_connection(item_name)

    def connect_to_saved(self, name):
        """连接到已保存的连接"""
        if name in self.conn_manager.connections:
            config = self.conn_manager.connections[name].copy()
            # 直接使用已保存的密码连接
            self.create_connection(config)

    def edit_saved_connection(self, name):
        """编辑已保存的连接"""
        if name in self.conn_manager.connections:
            config = self.conn_manager.connections[name].copy()
            dialog = DBConnectionDialog(self, config)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_config = dialog.get_config()
                
                # 更新配置
                self.conn_manager.connections[name] = updated_config
                self.conn_manager.save_connections()
                self.refresh_saved_connections()

    def delete_saved_connection(self, name):
        """删除已保存的连接"""
        reply = QMessageBox.question(self, "确认删除", f"确定要删除连接 '{name}' 吗？", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.conn_manager.connections[name]
            self.conn_manager.save_connections()
            self.refresh_saved_connections()

    def add_connection(self):
        """添加新连接"""
        dialog = DBConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            # 询问是否保存连接配置
            save_reply = QMessageBox.question(self, "保存连接", "是否保存此连接配置？", 
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if save_reply == QMessageBox.StandardButton.Yes:
                # 保存连接配置（包含加密密码）
                self.conn_manager.connections[config['name']] = config
                self.conn_manager.save_connections()
                self.refresh_saved_connections()
            
            self.create_connection(config)

    def create_connection(self, config):
        """创建数据库连接"""
        # 显示连接进度
        progress = QProgressBar()
        progress.setRange(0, 0)  # 不确定进度
        status_label = QLabel(f"正在连接到 {config['name']}...")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("连接中...")
        msg_box.setText(status_label.text())
        msg_box.setDetailedText(f"主机: {config['host']}:{config['port']}")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg_box.layout().addWidget(progress, 4, 0, 1, msg_box.layout().columnCount())
        msg_box.show()
        
        worker = DatabaseWorker(config)
        worker.result_ready.connect(lambda data: self.on_connection_success(config['name'], data, msg_box))
        worker.error_occurred.connect(lambda error: self.on_connection_error(error, msg_box))
        worker.start()
        
        # 存储worker以便后续管理
        self.connections[config['name']] = {'worker': worker, 'config': config}

    def on_connection_success(self, name, data, msg_box):
        # 关闭进度提示
        msg_box.close()
        
        # 清空之前的树内容
        self.db_tree.clear()
        
        # 添加到树形视图
        conn_item = QTreeWidgetItem(self.db_tree, [f"{name} ({data['connection'].host}:{data['connection'].port})"])
        conn_item.setData(0, Qt.ItemDataRole.UserRole, ('connection', name))
        
        for db_name in data['databases']:
            db_item = QTreeWidgetItem(conn_item, [db_name])
            db_item.setData(0, Qt.ItemDataRole.UserRole, ('database', db_name))
            
            for table_name in data['tables'][db_name]:
                table_item = QTreeWidgetItem(db_item, [table_name])
                table_item.setData(0, Qt.ItemDataRole.UserRole, ('table', table_name))
        
        conn_item.setExpanded(True)
        
        # 更新连接信息
        self.connections[name]['data'] = data
        
        # 记录当前连接
        self.current_connection = data['connection']

    def on_connection_error(self, error_msg, msg_box):
        # 关闭进度提示
        msg_box.close()
        QMessageBox.critical(self, "连接错误", f"连接失败: {error_msg}")

    def tree_item_clicked(self, item, column):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        item_type, item_name = item_data
        
        if item_type == 'connection':
            # 切换到该连接
            conn_name = item_name
            if conn_name in self.connections and 'data' in self.connections[conn_name]:
                conn_data = self.connections[conn_name]['data']
                self.current_connection = conn_data['connection']
                QMessageBox.information(self, "切换连接", f"已切换到连接: {conn_name}")
        
        elif item_type == 'database':
            # 选中数据库时，在SQL编辑器中自动填充
            current_text = self.sql_editor.toPlainText()
            if 'FROM' not in current_text.upper():
                self.sql_editor.insertPlainText(item_name + '.')
        
        elif item_type == 'table':
            # 双击表名时显示表数据
            database_name = item.parent().text(0)
            self.view_table_data(database_name, item_name)

    def view_table_data(self, database, table):
        """查看表数据"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        # 创建数据浏览器对话框
        browser = TableDataBrowser(self.current_connection, database, table, self)
        browser.exec()

    def rename_table(self, database, table):
        """重命名表"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        new_name, ok = QInputDialog.getText(self, "重命名表", "请输入新的表名:", QLineEdit.EchoMode.Normal, table)
        if ok and new_name:
            try:
                self.current_connection.select_db(database)
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"ALTER TABLE `{table}` RENAME TO `{new_name}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表已重命名为: {new_name}")
                    # 刷新树形视图
                    self.refresh_database_node(database)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")

    def delete_table(self, database, table):
        """删除表"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        reply = QMessageBox.question(self, "确认删除", f"确定要删除表 '{table}' 吗？\n此操作不可撤销！", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_connection.select_db(database)
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE `{table}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"表 '{table}' 已删除")
                    # 刷新树形视图
                    self.refresh_database_node(database)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def design_table(self, database, table):
        """设计表（查看表结构）"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        try:
            self.current_connection.select_db(database)
            with self.current_connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table}`;")
                table_info = cursor.fetchall()
                
                dialog = TableInfoDialog(table_info, self)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法获取表结构: {str(e)}")

    def create_table(self, database):
        """创建表"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        table_name, ok = QInputDialog.getText(self, "创建表", "请输入表名:")
        if ok and table_name:
            # 这里可以进一步实现表结构设计
            QMessageBox.information(self, "提示", "表结构设计功能待实现")

    def delete_database(self, database):
        """删除数据库"""
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        reply = QMessageBox.question(self, "确认删除", f"确定要删除数据库 '{database}' 吗？\n此操作不可撤销！", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.current_connection.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE `{database}`;")
                    self.current_connection.commit()
                    QMessageBox.information(self, "成功", f"数据库 '{database}' 已删除")
                    # 刷新树形视图
                    self.refresh_connection_tree()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除数据库失败: {str(e)}")

    def refresh_connection_tree(self):
        """刷新整个连接树"""
        if not self.current_connection:
            return
            
        # 重新加载连接信息
        conn_name = self.get_current_connection_name()
        if conn_name and conn_name in self.connections:
            config = self.connections[conn_name]['config']
            self.create_connection(config)

    def refresh_database_node(self, database):
        """刷新特定数据库节点"""
        for i in range(self.db_tree.topLevelItemCount()):
            conn_item = self.db_tree.topLevelItem(i)
            for j in range(conn_item.childCount()):
                db_item = conn_item.child(j)
                if db_item.text(0) == database:
                    # 清空子节点
                    db_item.takeChildren()
                    # 重新加载表
                    if self.current_connection:
                        try:
                            self.current_connection.select_db(database)
                            with self.current_connection.cursor() as cursor:
                                cursor.execute("SHOW TABLES;")
                                results = cursor.fetchall()
                                for row in results:
                                    table_name = row[0]
                                    table_item = QTreeWidgetItem(db_item, [table_name])
                                    table_item.setData(0, Qt.ItemDataRole.UserRole, ('table', table_name))
                        except Exception as e:
                            print(f"刷新数据库节点失败: {e}")

    def get_current_connection_name(self):
        """获取当前连接名称"""
        for name, info in self.connections.items():
            if 'data' in info and info['data']['connection'] == self.current_connection:
                return name
        return None

    def execute_sql(self):
        if not self.current_connection:
            QMessageBox.warning(self, "警告", "请先选择一个数据库连接")
            return
            
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return
            
        try:
            connection = self.current_connection
            with connection.cursor() as cursor:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    # 查询操作
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    self.result_table.setColumnCount(len(columns))
                    self.result_table.setHorizontalHeaderLabels(columns)
                    self.result_table.setRowCount(len(results))
                    
                    for i, row in enumerate(results):
                        for j, value in enumerate(row):
                            item = QTableWidgetItem(str(value) if value is not None else "")
                            self.result_table.setItem(i, j, item)
                else:
                    # 非查询操作
                    connection.commit()
                    QMessageBox.information(self, "成功", f"执行完成，影响 {cursor.rowcount} 行")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"SQL执行失败: {str(e)}")

    def save_connections_to_file(self):
        """手动保存连接配置到文件"""
        self.conn_manager.save_connections()
        QMessageBox.information(self, "保存成功", "连接配置已保存到文件")

    def closeEvent(self, event):
        """关闭窗口时保存连接配置"""
        self.conn_manager.save_connections()
        event.accept()

if __name__ == "__main__":
    # 检查是否安装了cryptography库
    try:
        import cryptography
    except ImportError:
        print("请安装cryptography库: pip install cryptography")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

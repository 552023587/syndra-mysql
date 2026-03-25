"""
Database Connection Dialog - Dialog for creating/editing database connections.

This module contains the DBConnectionDialog class that provides a UI for
inputting connection parameters and testing the connection.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QCheckBox, QWidget, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QMessageBox, QGroupBox, QVBoxLayout
)
from PyQt6.QtCore import Qt
from core.workers import TestConnectionWorker


class DBConnectionDialog(QDialog):
    """
    Dialog for creating or editing a database connection configuration.

    Provides input fields for connection parameters, SSH tunnel options,
    and connection testing functionality.
    """

    def __init__(self, parent=None, config=None):
        """
        Initialize the connection dialog.

        Args:
            parent: Parent widget
            config: Optional existing configuration to edit
        """
        super().__init__(parent)
        self.setWindowTitle("🔌 新建数据库连接")
        self.setModal(True)
        self.resize(450, 500)
        self.setMinimumWidth(400)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Basic connection settings group
        basic_group = QGroupBox(" 基础连接设置 ")
        basic_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 20, 15, 15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Create input fields
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("给连接起个名字")
        self.host_edit = QLineEdit("localhost")
        self.host_edit.setPlaceholderText("例如 localhost 或 127.0.0.1")
        self.port_edit = QLineEdit("3306")
        self.username_edit = QLineEdit("root")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("输入数据库密码")
        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("可选，连接后自动选择该数据库")
        self.use_ssh_check = QCheckBox("启用SSH隧道")

        # Add fields to layout
        form_layout.addRow("连接名:", self.name_edit)
        form_layout.addRow("主机地址:", self.host_edit)
        form_layout.addRow("端口:", self.port_edit)
        form_layout.addRow("用户名:", self.username_edit)
        form_layout.addRow("密码:", self.password_edit)
        form_layout.addRow("默认数据库:", self.database_edit)
        form_layout.addRow(self.use_ssh_check)

        basic_group.setLayout(form_layout)
        main_layout.addWidget(basic_group)

        # SSH configuration section
        self.ssh_config_widget = QGroupBox(" SSH隧道配置 ")
        self.ssh_config_widget.setStyleSheet("QGroupBox { font-weight: bold; }")
        ssh_layout = QFormLayout()
        ssh_layout.setSpacing(10)
        ssh_layout.setContentsMargins(15, 20, 15, 15)
        ssh_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ssh_host_edit = QLineEdit()
        self.ssh_host_edit.setPlaceholderText("SSH服务器地址")
        self.ssh_port_edit = QLineEdit("22")
        self.ssh_username_edit = QLineEdit()
        self.ssh_username_edit.setPlaceholderText("SSH用户名")
        self.ssh_password_edit = QLineEdit()
        self.ssh_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ssh_password_edit.setPlaceholderText("SSH密码")

        ssh_layout.addRow("SSH主机:", self.ssh_host_edit)
        ssh_layout.addRow("SSH端口:", self.ssh_port_edit)
        ssh_layout.addRow("SSH用户名:", self.ssh_username_edit)
        ssh_layout.addRow("SSH密码:", self.ssh_password_edit)
        self.ssh_config_widget.setLayout(ssh_layout)
        self.ssh_config_widget.setVisible(False)
        main_layout.addWidget(self.ssh_config_widget)

        # Show/hide SSH options based on checkbox
        self.use_ssh_check.stateChanged.connect(self.toggle_ssh_options)

        # Test connection area
        test_group = QGroupBox(" 连接测试 ")
        test_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        test_layout = QHBoxLayout()
        test_layout.setSpacing(10)
        test_layout.setContentsMargins(15, 20, 15, 15)
        self.test_btn = QPushButton(" 🧪 测试连接 ")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #5bc0de;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #31b0d5;
            }
            QPushButton:pressed {
                background-color: #269abc;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.test_btn.clicked.connect(self.test_connection)
        self.test_status_label = QLabel("未测试")
        self.test_status_label.setStyleSheet("color: #666;")
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setTextVisible(False)

        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status_label)
        test_layout.addStretch()
        test_group.setLayout(test_layout)
        main_layout.addWidget(test_group)
        main_layout.addWidget(self.test_progress)

        # OK/Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ok_btn = QPushButton(" ✅ 保存 ")
        cancel_btn = QPushButton(" ❌ 取消 ")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
            QPushButton:pressed {
                background-color: #449d44;
            }
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Fill form if we have an existing configuration
        if config:
            self.fill_form(config)

    def fill_form(self, config: dict):
        """
        Fill the form with existing connection configuration.

        Args:
            config: Connection configuration dictionary
        """
        self.name_edit.setText(config.get('name', ''))
        self.host_edit.setText(config.get('host', ''))
        self.port_edit.setText(str(config.get('port', 3306)))
        self.username_edit.setText(config.get('username', ''))
        self.password_edit.setText(config.get('password', ''))
        self.database_edit.setText(config.get('database', ''))
        self.use_ssh_check.setChecked(config.get('use_ssh', False))

        # Fill SSH config if SSH is enabled
        if config.get('use_ssh') and 'ssh_config' in config:
            ssh_config = config['ssh_config']
            self.ssh_host_edit.setText(ssh_config.get('host', ''))
            self.ssh_port_edit.setText(str(ssh_config.get('port', 22)))
            self.ssh_username_edit.setText(ssh_config.get('username', ''))
            self.ssh_password_edit.setText(ssh_config.get('password', ''))

    def toggle_ssh_options(self, state: int):
        """
        Toggle visibility of SSH configuration options.

        Args:
            state: Checkbox state (Qt.CheckState value)
        """
        self.ssh_config_widget.setVisible(state == Qt.CheckState.Checked.value)

    def test_connection(self):
        """Test the database connection with current input values."""
        config = self.get_config()

        # Basic validation
        if not config['host'] or not config['username']:
            QMessageBox.warning(self, "警告", "请填写主机和用户名")
            return

        # Validate main port number
        try:
            port = int(config['port'])
            if not (1 <= port <= 65535):
                raise ValueError("端口号必须在1-65535之间")
        except ValueError as e:
            QMessageBox.warning(self, "警告", f"端口号无效: {e}")
            return

        # Validate SSH port if SSH is enabled
        if config.get('use_ssh') and 'ssh_config' in config:
            try:
                ssh_port = int(config['ssh_config']['port'])
                if not (1 <= ssh_port <= 65535):
                    raise ValueError("SSH端口号必须在1-65535之间")
            except ValueError as e:
                QMessageBox.warning(self, "警告", f"SSH端口号无效: {e}")
                return

        # Disable button and show progress
        self.test_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        self.test_status_label.setText("正在测试连接...")
        self.test_status_label.setStyleSheet("color: #666;")

        # Create and start background worker
        self.test_worker = TestConnectionWorker(config)
        self.test_worker.test_result.connect(self.on_test_complete)
        self.test_worker.start()

    def on_test_complete(self, success: bool, message: str):
        """
        Handle connection test completion.

        Args:
            success: Whether the connection test succeeded
            message: Result or error message
        """
        # Restore UI state
        self.test_btn.setEnabled(True)
        self.test_progress.setVisible(False)

        # Display result
        if success:
            self.test_status_label.setText("✅ " + message)
            self.test_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.test_status_label.setText("❌ " + message)
            self.test_status_label.setStyleSheet("color: red;")

    def get_config(self) -> dict:
        """
        Get the current connection configuration from the form.

        Returns:
            Dictionary containing all connection parameters
        """
        # Parse port as integer
        port = int(self.port_edit.text()) if self.port_edit.text().isdigit() else 3306

        config = {
            'name': self.name_edit.text(),
            'host': self.host_edit.text(),
            'port': port,
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'database': self.database_edit.text(),
            'use_ssh': self.use_ssh_check.isChecked(),
        }

        # Add SSH configuration if enabled
        if config['use_ssh']:
            ssh_port = int(self.ssh_port_edit.text()) if self.ssh_port_edit.text().isdigit() else 22
            config['ssh_config'] = {
                'host': self.ssh_host_edit.text(),
                'port': ssh_port,
                'username': self.ssh_username_edit.text(),
                'password': self.ssh_password_edit.text(),
            }

        return config

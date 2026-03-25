"""
Connection Manager - Manages saved database connection configurations.

This module handles loading, saving, and encrypting connection configurations.
Passwords are encrypted before being stored to disk.
"""

import json
import os
from typing import Dict
from utils.encryption import EncryptionManager


class ConnectionManager:
    """
    Manages saved database connection configurations with encrypted password storage.

    Loads connections from a JSON file, encrypts passwords before saving,
    and decrypts them when loading.
    """

    def __init__(self, filename: str = "connections.json"):
        """
        Initialize the connection manager.

        Args:
            filename: Path to the JSON file storing connection configurations
        """
        self.filename = filename
        self.connections: Dict[str, dict] = {}
        # Use encryption manager for password encryption/decryption
        self.encryption = EncryptionManager()
        self.load_connections()

    def save_connections(self):
        """
        Save connection configurations to JSON file with encrypted passwords.

        Creates a backup of the existing file before saving.
        """
        try:
            # Create backup if file exists
            if os.path.exists(self.filename):
                backup_filename = self.filename + ".backup"
                # If backup exists, it will be overwritten
                os.replace(self.filename, backup_filename)

            # Encrypt passwords before saving
            connections_to_save = {}
            for name, config in self.connections.items():
                config_copy = config.copy()
                # Encrypt main connection password
                config_copy['password'] = self.encryption.encrypt(config.get('password', ''))
                # Encrypt SSH password if exists
                if 'ssh_config' in config_copy and 'password' in config_copy['ssh_config']:
                    ssh_config = config_copy['ssh_config'].copy()
                    ssh_config['password'] = self.encryption.encrypt(ssh_config.get('password', ''))
                    config_copy['ssh_config'] = ssh_config
                connections_to_save[name] = config_copy

            # Write to file with UTF-8 encoding for Chinese support
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(connections_to_save, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"保存连接配置失败: {e}")

    def load_connections(self):
        """
        Load connection configurations from JSON file and decrypt passwords.

        If the file doesn't exist, initializes with empty connections dict.
        """
        if not os.path.exists(self.filename):
            self.connections = {}
            return

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                connections = json.load(f)

            # Decrypt passwords after loading
            decrypted_connections = {}
            for name, config in connections.items():
                config_copy = config.copy()
                # Decrypt main connection password
                config_copy['password'] = self.encryption.decrypt(config.get('password', ''))
                # Decrypt SSH password if exists
                if 'ssh_config' in config_copy and 'password' in config_copy['ssh_config']:
                    ssh_config = config_copy['ssh_config'].copy()
                    ssh_config['password'] = self.encryption.decrypt(ssh_config.get('password', ''))
                    config_copy['ssh_config'] = ssh_config
                decrypted_connections[name] = config_copy

            self.connections = decrypted_connections
        except Exception as e:
            print(f"加载连接配置失败: {e}")
            self.connections = {}

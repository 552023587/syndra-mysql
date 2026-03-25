"""
Database Worker Threads - Asynchronous database operations.

This module contains QThread-based worker classes for performing database
operations in the background without blocking the UI.
"""

import pymysql
from PyQt6.QtCore import QThread, pyqtSignal


class TestConnectionWorker(QThread):
    """
    Background worker for testing database connectivity.

    Signals:
        test_result: Emitted when test completes with (success, message)
    """

    # Signal emitted when test is done: (success, message)
    test_result = pyqtSignal(bool, str)

    def __init__(self, config: dict):
        """
        Initialize the connection test worker.

        Args:
            config: Dictionary containing connection parameters
                - host: Database host
                - port: Database port
                - username: Database username
                - password: Database password
                - database: Optional database name
        """
        super().__init__()
        self.config = config

    def run(self):
        """Execute the connection test in a background thread."""
        try:
            # Non-SSH mode: Direct connection test
            connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config.get('database', ''),
                charset='utf8mb4',
                connect_timeout=10
            )

            # Verify connection by executing a simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()

            connection.close()

            # Test succeeded
            self.test_result.emit(True, f"连接成功！MySQL版本: {version[0] if version else 'Unknown'}")

        except Exception as e:
            # Test failed
            self.test_result.emit(False, f"连接失败: {str(e)}")


class DatabaseWorker(QThread):
    """
    Background worker for establishing a database connection and loading schema.

    This worker connects to MySQL, retrieves all databases and tables,
    and returns the result to the main thread.

    Signals:
        result_ready: Emitted when connection and schema loading succeeds
        error_occurred: Emitted when an error occurs with error message
    """

    # Signals for communication with main thread
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, connection_info: dict):
        """
        Initialize the database worker.

        Args:
            connection_info: Connection parameters dictionary
        """
        super().__init__()
        self.connection_info = connection_info
        self.connection = None

    def run(self):
        """Execute the database connection and schema loading in background."""
        try:
            # Connect to the database
            self.connection = pymysql.connect(
                host=self.connection_info['host'],
                port=self.connection_info['port'],
                user=self.connection_info['username'],
                password=self.connection_info['password'],
                database=self.connection_info.get('database', ''),
                charset='utf8mb4',
                connect_timeout=10
            )

            # Get list of all databases (excluding system databases)
            databases = []
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                results = cursor.fetchall()
                for row in results:
                    db_name = row[0]
                    # Filter out system databases
                    if db_name not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                        databases.append(db_name)

            # Get tables for each database
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

            # Return the result
            self.result_ready.emit({
                'databases': databases,
                'tables': db_tables,
                'connection': self.connection
            })

        except Exception as e:
            self.error_occurred.emit(str(e))

    def close_connection(self):
        """Close the database connection if it's open."""
        if self.connection:
            self.connection.close()

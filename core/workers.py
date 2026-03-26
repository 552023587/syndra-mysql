"""
Database Worker Threads - Asynchronous database operations.

This module contains QThread-based worker classes for performing database
operations in the background without blocking the UI.
"""

import logging
import pymysql
from sshtunnel import SSHTunnelForwarder
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


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
        tunnel = None
        try:
            if self.config.get('use_ssh') and 'ssh_config' in self.config:
                # SSH tunnel mode
                ssh_config = self.config['ssh_config']

                # Create SSH tunnel
                ssh_host = ssh_config['host']
                ssh_port = int(ssh_config['port'])
                ssh_username = ssh_config['username']
                ssh_password = ssh_config['password']
                mysql_host = self.config['host']
                mysql_port = self.config['port']

                import paramiko
                import time

                # Create SSH tunnel with auto-accept unknown host keys
                tunnel = SSHTunnelForwarder(
                    (ssh_host, ssh_port),
                    ssh_username=ssh_username,
                    ssh_password=ssh_password,
                    remote_bind_address=(mysql_host, mysql_port),
                    local_bind_address=('127.0.0.1', 0),
                    host_pkey_directories=[],
                    allow_agent=False
                )
                # Set daemon mode before starting
                tunnel.daemon_forward_servers = True
                # Automatically accept unknown host keys
                tunnel._server_host_key_policy = paramiko.AutoAddPolicy()

                logger.info(f"Starting SSH tunnel to {ssh_host}:{ssh_port} -> {mysql_host}:{mysql_port}")

                # Start tunnel
                tunnel.start()

                # Wait up to 15 seconds for tunnel to become active
                timeout = 15
                start_wait = time.time()
                while not tunnel.is_active and time.time() - start_wait < timeout:
                    time.sleep(0.1)

                if not tunnel.is_active:
                    logger.error(f"SSH tunnel failed to become active after {timeout} seconds")
                    tunnel.stop()
                    raise Exception(f"SSH隧道启动超时（{timeout}秒），请检查SSH配置、网络和服务器地址")

                local_port = tunnel.local_bind_port
                logger.info(f"SSH tunnel established, local port: {local_port}")

                # Connect through local tunnel
                connection = pymysql.connect(
                    host='127.0.0.1',
                    port=local_port,
                    user=self.config['username'],
                    password=self.config['password'],
                    database=self.config.get('database', ''),
                    charset='utf8mb4',
                    connect_timeout=10
                )

                # Verify connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION();")
                    version = cursor.fetchone()

                connection.close()
                tunnel.stop()

                self.test_result.emit(True, f"连接成功！(SSH隧道) MySQL版本: {version[0] if version else 'Unknown'}")
            else:
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
            # Ensure tunnel is closed on error
            if tunnel:
                tunnel.stop()
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
        self.tunnel = None

    def run(self):
        """Execute the database connection and schema loading in background."""
        try:
            if self.connection_info.get('use_ssh') and 'ssh_config' in self.connection_info:
                # SSH tunnel mode
                ssh_config = self.connection_info['ssh_config']

                # Create SSH tunnel
                ssh_host = ssh_config['host']
                ssh_port = int(ssh_config['port'])
                ssh_username = ssh_config['username']
                ssh_password = ssh_config['password']
                mysql_host = self.connection_info['host']
                mysql_port = self.connection_info['port']

                import paramiko
                import time

                # Create SSH tunnel with auto-accept unknown host keys
                self.tunnel = SSHTunnelForwarder(
                    (ssh_host, ssh_port),
                    ssh_username=ssh_username,
                    ssh_password=ssh_password,
                    remote_bind_address=(mysql_host, mysql_port),
                    local_bind_address=('127.0.0.1', 0),
                    host_pkey_directories=[],
                    allow_agent=False
                )
                # Set daemon mode before starting
                self.tunnel.daemon_forward_servers = True
                # Automatically accept unknown host keys
                self.tunnel._server_host_key_policy = paramiko.AutoAddPolicy()

                logger.info(f"Starting SSH tunnel to {ssh_host}:{ssh_port} -> {mysql_host}:{mysql_port}")

                # Start tunnel
                self.tunnel.start()

                # Wait up to 15 seconds for tunnel to become active
                timeout = 15
                start_wait = time.time()
                while not self.tunnel.is_active and time.time() - start_wait < timeout:
                    time.sleep(0.1)

                if not self.tunnel.is_active:
                    logger.error(f"SSH tunnel failed to become active after {timeout} seconds")
                    if self.tunnel:
                        self.tunnel.stop()
                    raise Exception(f"SSH隧道启动超时（{timeout}秒），请检查SSH配置、网络和服务器地址")

                local_port = self.tunnel.local_bind_port
                logger.info(f"SSH tunnel established, local port: {local_port}")

                # Connect through local tunnel
                self.connection = pymysql.connect(
                    host='127.0.0.1',
                    port=local_port,
                    user=self.connection_info['username'],
                    password=self.connection_info['password'],
                    database=self.connection_info.get('database', ''),
                    charset='utf8mb4',
                    connect_timeout=10
                )
            else:
                # Direct connection
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
            logger.info("Getting database list through SSH tunnel")
            databases = []
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                results = cursor.fetchall()
                for row in results:
                    db_name = row[0]
                    # Filter out system databases
                    if db_name not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                        databases.append(db_name)
            logger.info(f"Found {len(databases)} user databases")

            # Get tables for each database and collect column names for auto-completion
            db_tables = {}
            all_table_names = []
            all_column_names = []

            # First get all tables from each database
            accessible_databases = []
            for db in databases:
                logger.debug(f"Getting tables for database: {db}")
                tables = []
                try:
                    self.connection.select_db(db)
                    with self.connection.cursor() as cursor:
                        cursor.execute("SHOW TABLES;")
                        results = cursor.fetchall()
                        for row in results:
                            table_name = row[0]
                            tables.append(table_name)
                            # Collect table name for auto-completion
                            if table_name not in all_table_names:
                                all_table_names.append(table_name)
                    db_tables[db] = tables
                    accessible_databases.append(db)
                except Exception as e:
                    logger.warning(f"Failed to access database {db}, skipping: {str(e)}")

            # Update databases list to only include accessible ones
            databases = accessible_databases

            # Get all column names in ONE query from INFORMATION_SCHEMA (much faster over SSH!)
            # This reduces hundreds of round-trips to just one
            try:
                placeholders = ', '.join(['%s'] * len(databases))
                with self.connection.cursor() as cursor:
                    query = f"""
                        SELECT DISTINCT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA IN ({placeholders})
                    """
                    cursor.execute(query, databases)
                    results = cursor.fetchall()
                    for row in results:
                        col_name = row[0]
                        if col_name not in all_column_names:
                            all_column_names.append(col_name)
                logger.info(f"Collected {len(all_table_names)} tables, {len(all_column_names)} columns for auto-completion")
            except Exception as e:
                # Fallback to original method if INFORMATION_SCHEMA is not accessible
                logger.warning(f"Failed to get columns via INFORMATION_SCHEMA ({str(e)}), falling back to per-table query")
                all_column_names = []
                for db in databases:
                    self.connection.select_db(db)
                    with self.connection.cursor() as cursor:
                        for table_name in db_tables[db]:
                            try:
                                cursor.execute(f"DESCRIBE `{table_name}`;")
                                cols = cursor.fetchall()
                                for col in cols:
                                    col_name = col[0]
                                    if col_name not in all_column_names:
                                        all_column_names.append(col_name)
                            except Exception as e2:
                                logger.warning(f"Failed to get columns for {db}.{table_name}: {e2}")
                logger.info(f"Fallback: collected {len(all_table_names)} tables, {len(all_column_names)} columns for auto-completion")

            # Return the result including tunnel reference and auto-completion data
            self.result_ready.emit({
                'databases': databases,
                'tables': db_tables,
                'connection': self.connection,
                'tunnel': self.tunnel,
                'all_table_names': all_table_names,
                'all_column_names': all_column_names
            })

        except Exception as e:
            # Ensure tunnel is closed on error
            if self.tunnel:
                self.tunnel.stop()
            self.error_occurred.emit(str(e))

    def close_tunnel(self):
        """Close the SSH tunnel if it's open."""
        if self.tunnel:
            self.tunnel.stop()
            self.tunnel = None

    def close_connection(self):
        """Close the database connection if it's open."""
        if self.connection:
            self.connection.close()
        # Also close the tunnel if exists
        self.close_tunnel()

"""
SQL Syntax Highlighter - Provides syntax highlighting for SQL code.

This module contains the SqlHighlighter class that highlights SQL keywords,
functions, strings, comments, and numbers in the SQL editor.
"""

import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class SqlHighlighter(QSyntaxHighlighter):
    """
    SQL syntax highlighter for the SQL editor.

    Provides different coloring for SQL keywords, functions, strings,
    comments, and numbers. Also provides keyword lists for auto-completion.
    """

    # SQL keywords for highlighting and auto-completion
    KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE',
        'DROP', 'ALTER', 'TABLE', 'DATABASE', 'INDEX', 'PRIMARY', 'KEY',
        'FOREIGN', 'REFERENCES', 'ON', 'SET', 'VALUES', 'INTO', 'JOIN',
        'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ORDER', 'BY', 'GROUP', 'HAVING',
        'LIMIT', 'OFFSET', 'DISTINCT', 'UNION', 'ALL', 'AS', 'IS', 'NULL',
        'NOT', 'AND', 'OR', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'CASE',
        'WHEN', 'THEN', 'ELSE', 'END', 'IF', 'FOR', 'DO', 'BEGIN', 'COMMIT',
        'ROLLBACK', 'TRUNCATE', 'USE', 'SHOW', 'DESCRIBE', 'EXPLAIN',
        'PROCEDURE', 'FUNCTION', 'VIEW', 'TRIGGER', 'EVENT', 'LOGFILE',
        'MASTER', 'SLAVE', 'REPLICATE', 'START', 'STOP', 'RESET', 'PURGE',
        'CHANGE', 'GRANT', 'REVOKE', 'USER', 'PASSWORD', 'WITH', 'GRANT',
        'OPTION', 'REPLACE', 'IGNORE', 'DUPLICATE', 'KEY', 'AUTO_INCREMENT',
        'ENGINE', 'CHARSET', 'COLLATE', 'COMMENT', 'DEFAULT',
        'CURRENT_TIMESTAMP', 'NOW', 'CURDATE', 'CURTIME', 'DATE', 'TIME',
        'DATETIME', 'TIMESTAMP', 'YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE',
        'SECOND', 'MICROSECOND', 'TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT',
        'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
        'BIT', 'BOOLEAN', 'BOOL', 'SERIAL', 'DATE', 'TIME', 'DATETIME',
        'TIMESTAMP', 'YEAR', 'CHAR', 'VARCHAR', 'BINARY', 'VARBINARY',
        'TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB', 'TINYTEXT', 'TEXT',
        'MEDIUMTEXT', 'LONGTEXT', 'ENUM', 'SET', 'GEOMETRY', 'POINT',
        'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING',
        'MULTIPOLYGON', 'GEOMETRYCOLLECTION'
    ]

    # SQL functions for highlighting and auto-completion
    FUNCTIONS = [
        'ABS', 'ACOS', 'ADDDATE', 'ADDTIME', 'AES_DECRYPT', 'AES_ENCRYPT',
        'ASCII', 'ASIN', 'ATAN', 'ATAN2', 'AVG', 'BENCHMARK', 'BIN',
        'BIT_AND', 'BIT_COUNT', 'BIT_LENGTH', 'BIT_OR', 'BIT_XOR', 'CAST',
        'CEIL', 'CEILING', 'CHAR_LENGTH', 'CHARACTER_LENGTH', 'CHARSET',
        'COALESCE', 'COERCIBILITY', 'COLLATION', 'COMPRESS', 'CONCAT',
        'CONCAT_WS', 'CONNECTION_ID', 'CONV', 'CONVERT_TZ', 'COS', 'COT',
        'COUNT', 'CRC32', 'CURDATE', 'CURRENT_DATE', 'CURRENT_TIME',
        'CURRENT_TIMESTAMP', 'CURRENT_USER', 'CURTIME', 'DATABASE',
        'DATE_ADD', 'DATE_FORMAT', 'DATE_SUB', 'DATEDIFF', 'DAY', 'DAYNAME',
        'DAYOFMONTH', 'DAYOFWEEK', 'DAYOFYEAR', 'DECODE', 'DEGREES',
        'DES_DECRYPT', 'DES_ENCRYPT', 'ELT', 'ENCODE', 'ENCRYPT', 'EXP',
        'EXPORT_SET', 'EXTRACT', 'FIELD', 'FIND_IN_TABLE', 'FLOOR', 'FORMAT',
        'FOUND_ROWS', 'FROM_DAYS', 'FROM_UNIXTIME', 'GET_FORMAT', 'GET_LOCK',
        'GREATEST', 'GROUP_CONCAT', 'HEX', 'HOUR', 'IF', 'IFNULL',
        'INET_ATON', 'INET_NTOA', 'INSERT', 'INSTR', 'INTERVAL', 'IS_FREE_LOCK',
        'IS_USED_LOCK', 'LAST_DAY', 'LAST_INSERT_ID', 'LCASE', 'LEAST',
        'LEFT', 'LENGTH', 'LN', 'LOAD_FILE', 'LOCALTIME', 'LOCALTIMESTAMP',
        'LOCATE', 'LOG', 'LOG10', 'LOG2', 'LOWER', 'LPAD', 'LTRIM', 'MAKE_SET',
        'MAKEDATE', 'MAKETIME', 'MASTER_POS_WAIT', 'MAX', 'MD5', 'MICROSECOND',
        'MIN', 'MINUTE', 'MOD', 'MONTH', 'MONTHNAME', 'NAME_CONST', 'NOW',
        'NULLIF', 'OCT', 'OCTET_LENGTH', 'OLD_PASSWORD', 'ORD', 'PASSWORD',
        'PERIOD_ADD', 'PERIOD_DIFF', 'PI', 'POSITION', 'POW', 'POWER',
        'QUARTER', 'RADIANS', 'RAND', 'RELEASE_LOCK', 'REPEAT', 'REPLACE',
        'REVERSE', 'RIGHT', 'ROUND', 'ROW_COUNT', 'RTRIM', 'SEC_TO_TIME',
        'SECOND', 'SESSION_USER', 'SHA', 'SHA1', 'SIGN', 'SIN', 'SLEEP',
        'SOUNDEX', 'SPACE', 'SQRT', 'STD', 'STDDEV', 'STDDEV_POP', 'STDDEV_SAMP',
        'STR_TO_DATE', 'STRCMP', 'SUBDATE', 'SUBSTRING', 'SUBSTRING_INDEX',
        'SUBTIME', 'SUM', 'SYSDATE', 'SYSTEM_USER', 'TAN', 'TIME',
        'TIME_FORMAT', 'TIME_TO_SEC', 'TIMEDIFF', 'TIMESTAMP', 'TIMESTAMPADD',
        'TIMESTAMPDIFF', 'TO_DAYS', 'TRIM', 'TRUNCATE', 'UCASE', 'UNCOMPRESS',
        'UNCOMPRESSED_LENGTH', 'UNHEX', 'UNIX_TIMESTAMP', 'UPPER', 'USER',
        'UTC_DATE', 'UTC_TIME', 'UTC_TIMESTAMP', 'UUID', 'VALUES', 'VAR_POP',
        'VAR_SAMP', 'VARIANCE', 'VERSION', 'WEEK', 'WEEKDAY', 'WEEKOFYEAR',
        'YEAR', 'YEARWEEK'
    ]

    def __init__(self, parent=None):
        """
        Initialize the SQL highlighter with formatting rules.

        Args:
            parent: Parent text document
        """
        super().__init__(parent)

        # Define formatting styles for different token types
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#800080"))
        function_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF0000"))

        # Compile regex rules for highlighting
        keywords_pattern = '\\b(' + '|'.join(self.KEYWORDS) + ')\\b'
        functions_pattern = '\\b(' + '|'.join(self.FUNCTIONS) + ')\\b'

        self.rules = [
            # Keywords
            (keywords_pattern, keyword_format),
            # Functions
            (functions_pattern, function_format),
            # Single-quoted strings
            (r"'(?:[^'\\]|\\.)*'", string_format),
            # Double-quoted strings
            (r'"(?:[^"\\]|\\.)*"', string_format),
            # Single-line comments (--)
            (r'--.*', comment_format),
            # Multi-line comments /* ... */
            (r'/\*.*?\*/', comment_format),
            # Numbers (integers and decimals)
            (r'\b\d+\.?\d*\b', number_format),
        ]

    @property
    def keywords(self) -> list:
        """Get the list of SQL keywords for auto-completion."""
        return self.KEYWORDS

    @property
    def functions(self) -> list:
        """Get the list of SQL functions for auto-completion."""
        return self.FUNCTIONS

    def highlightBlock(self, text: str):
        """
        Apply highlighting to the given text block.

        This method is called by Qt for each text block that needs highlighting.

        Args:
            text: Text block to highlight
        """
        for pattern, fmt in self.rules:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

"""
Chain of Responsibility Logging System
Implements different loggers that can be chained together
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, Union
from app.core.singleton import DatabaseManager


class LogMessage:
    """Represents a log message that can be passed through the chain"""

    def __init__(self, level: str, message: str, user_id: Optional[str] = None,
                 action: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.level = level
        self.message = message
        self.user_id = user_id
        self.action = action
        self.details = details or {}
        self.timestamp = datetime.now(datetime.timezone.utc)


class Logger(ABC):
    """Base logger class in the Chain of Responsibility pattern"""

    def __init__(self, next_logger: Optional['Logger'] = None):
        self.next_logger = next_logger

    def log(self, log_message: LogMessage) -> None:
        """Process the log message and optionally pass to next logger"""
        self._log_message(log_message)

        # Pass to next logger in chain
        if self.next_logger:
            self.next_logger.log(log_message)

    @abstractmethod
    def _log_message(self, log_message: LogMessage) -> None:
        """Abstract method to implement specific logging behavior"""
        pass


class ConsoleLogger(Logger):
    """Logger that outputs to console"""

    def _log_message(self, log_message: LogMessage) -> None:
        """Log message to console with formatted output"""
        level_colors = {
            'DEBUG': '\033[36m',  # Cyan
            'INFO': '\033[32m',   # Green
            'WARNING': '\033[33m', # Yellow
            'ERROR': '\033[31m',  # Red
            'CRITICAL': '\033[35m' # Magenta
        }

        reset_color = '\033[0m'
        color = level_colors.get(log_message.level, '')

        formatted_message = f"[{log_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {color}{log_message.level}{reset_color}: {log_message.message}"

        if log_message.user_id:
            formatted_message += f" | User: {log_message.user_id}"

        if log_message.action:
            formatted_message += f" | Action: {log_message.action}"

        print(formatted_message)


class FileLogger(Logger):
    """Logger that writes to a file"""

    def __init__(self, file_path: str = "app.log", next_logger: Optional[Logger] = None):
        super().__init__(next_logger)
        self.file_path = file_path

    def _log_message(self, log_message: LogMessage) -> None:
        """Log message to file with JSON format"""
        try:
            log_entry = {
                "timestamp": log_message.timestamp.isoformat(),
                "level": log_message.level,
                "message": log_message.message,
                "user_id": log_message.user_id,
                "action": log_message.action,
                "details": log_message.details
            }

            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        except Exception as e:
            # Fallback to console if file logging fails
            print(f"FileLogger error: {e}")


class DatabaseLogger(Logger):
    """Logger that stores logs in the Supabase database"""

    def __init__(self, next_logger: Optional[Logger] = None):
        super().__init__(next_logger)
        self.db_manager = None

    def _get_db_connection(self):
        """Lazy initialization of database connection"""
        if self.db_manager is None:
            self.db_manager = DatabaseManager.get_instance()
        return self.db_manager.get_connection()

    def _log_message(self, log_message: LogMessage) -> None:
        """Log message to database"""
        try:
            supabase = self._get_db_connection()

            log_data = {
                "level": log_message.level,
                "message": log_message.message,
                "user_id": log_message.user_id,
                "action": log_message.action,
                "details": json.dumps(log_message.details) if log_message.details else None
            }

            supabase.table("logs").insert(log_data).execute()

        except Exception as e:
            # Fallback to console if database logging fails
            print(f"DatabaseLogger error: {e}")


class LoggerManager:
    """Manages the logger chain and provides easy access to logging methods"""

    _instance = None

    def __init__(self):
        self.root_logger = None
        self._initialize_chain()

    def _initialize_chain(self):
        """Initialize the chain of responsibility: Console -> File -> Database"""
        # Create loggers in reverse order (Database -> File -> Console)
        database_logger = DatabaseLogger()
        file_logger = FileLogger("app.log", database_logger)
        console_logger = ConsoleLogger(file_logger)

        self.root_logger = console_logger

    @classmethod
    def get_instance(cls) -> 'LoggerManager':
        """Singleton pattern for LoggerManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log(self, level: str, message: str, user_id: Optional[str] = None,
            action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a message through the chain"""
        log_message = LogMessage(level, message, user_id, action, details)
        if self.root_logger:
            self.root_logger.log(log_message)

    def debug(self, message: str, user_id: Optional[str] = None,
              action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message"""
        self.log("DEBUG", message, user_id, action, details)

    def info(self, message: str, user_id: Optional[str] = None,
             action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log info message"""
        self.log("INFO", message, user_id, action, details)

    def warning(self, message: str, user_id: Optional[str] = None,
                action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message"""
        self.log("WARNING", message, user_id, action, details)

    def error(self, message: str, user_id: Optional[str] = None,
              action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log error message"""
        self.log("ERROR", message, user_id, action, details)

    def critical(self, message: str, user_id: Optional[str] = None,
                 action: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message"""
        self.log("CRITICAL", message, user_id, action, details)


# Global logger instance for easy access
logger_manager = LoggerManager.get_instance()

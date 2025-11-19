"""로깅 시스템 설정 및 관리."""

import json
import logging
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path

from bzero.core.settings import Settings


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class JsonFormatter(logging.Formatter):
    """JSON 형식으로 로그를 포맷팅하는 클래스."""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 포맷팅합니다.

        Args:
            record: 로그 레코드

        Returns:
            str: JSON 형식의 로그 문자열
        """
        log_data = {
            "timestamp": self.formatTime(record, DATETIME_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        # extra fields 추가
        if hasattr(record, "extras"):
            log_data.update(record.extras)

        # request 관련 정보가 있다면 추가
        request_attrs = ("request_id", "method", "path", "client_host", "request_body")
        for attr in request_attrs:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        # exception 정보가 있다면 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class LoggerType(str, Enum):
    """로거의 타입을 나타내는 enum."""

    APP = "app"
    ACCESS = "access"
    BACKGROUND = "background"
    ERROR = "error"


def setup_loggers(settings: Settings) -> None:
    """전체 로거를 초기화하는 함수.

    Args:
        settings: 애플리케이션 설정
    """
    log_dir = Path(settings.log_dir)
    for logger_type in (LoggerType.APP, LoggerType.ACCESS, LoggerType.BACKGROUND, LoggerType.ERROR):
        log_file_path = _get_log_path(logger_type, log_dir)
        logger = logging.getLogger(logger_type.value)
        _setup_logger(
            logger=logger,
            log_level=settings.log_level,
            log_file_path=log_file_path,
            log_file_max_bytes=settings.log_file_max_bytes,
            log_file_backup_count=settings.log_file_backup_count,
        )


def app_logger() -> logging.Logger:
    """app 타입으로 설정한 로거를 반환합니다.

    Returns:
        logging.Logger: app 로거
    """
    return logging.getLogger(LoggerType.APP.value)


def access_logger() -> logging.Logger:
    """access 타입으로 설정한 로거를 반환합니다.

    Returns:
        logging.Logger: access 로거
    """
    return logging.getLogger(LoggerType.ACCESS.value)


def background_logger() -> logging.Logger:
    """access 타입으로 설정한 로거를 반환합니다.

    Returns:
        logging.Logger: access 로거
    """
    return logging.getLogger(LoggerType.BACKGROUND.value)


def error_logger() -> logging.Logger:
    """error 타입으로 설정한 로거를 반환합니다.

    Returns:
        logging.Logger: error 로거
    """
    return logging.getLogger(LoggerType.ERROR.value)


def _get_log_path(logger_type: LoggerType, log_dir: Path) -> Path:
    """로그 파일의 전체 경로를 반환합니다.

    Args:
        logger_type: 로거 타입
        log_dir: 로그 디렉토리 경로

    Returns:
        Path: 로그 파일 경로
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{logger_type.value}.log"


def _setup_logger(
    logger: logging.Logger,
    log_level: str,
    log_file_path: Path,
    log_file_max_bytes: int,
    log_file_backup_count: int,
) -> None:
    """로거를 설정합니다 (콘솔 및 파일).

    Args:
        logger: 설정할 로거 인스턴스
        log_level: 로그 레벨
        log_file_path: 로그 파일 경로
        log_file_max_bytes: 각 로그 파일의 최대 크기
        log_file_backup_count: 보관할 백업 파일 수
    """
    logger.setLevel(log_level)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s] %(message)s",
        datefmt=DATETIME_FORMAT,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=log_file_max_bytes,
        backupCount=log_file_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

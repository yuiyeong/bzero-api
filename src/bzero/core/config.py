"""
B0 API 설정 모듈

환경 변수를 기반으로 애플리케이션 설정을 관리합니다.
"""

import os
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # ======================
    # Application Settings
    # ======================
    app_name: str = "B0 API"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "local"  # local, production

    # ======================
    # CORS Settings
    # ======================
    # CORS 허용 출처 (origins)
    # 개발 환경: http://localhost:5173
    # 배포 환경: https://app.basementzero.cloud
    # 여러 개를 설정할 경우 쉼표로 구분 (예: "http://localhost:5173,https://app.basementzero.cloud")
    cors_origins: str = "http://localhost:5173"

    # CORS 허용 메서드 (쉼표로 구분)
    cors_allow_methods: str = "*"

    # CORS 허용 헤더 (쉼표로 구분)
    cors_allow_headers: str = "*"

    # 자격 증명(쿠키, 인증 헤더 등) 허용 여부
    # True로 설정 시, credentials를 포함한 요청 허용
    cors_allow_credentials: bool = True

    def get_cors_origins(self) -> list[str]:
        """
        CORS 허용 출처 리스트 반환

        환경 변수에서 쉼표로 구분된 문자열을 파싱하여
        리스트로 변환합니다.

        Returns:
            허용된 출처(origin) URL 리스트
        """
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_cors_allow_methods(self) -> list[str]:
        """
        CORS 허용 메서드 리스트 반환

        Returns:
            허용된 HTTP 메서드 리스트 또는 ["*"]
        """
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]

    def get_cors_allow_headers(self) -> list[str]:
        """
        CORS 허용 헤더 리스트 반환

        Returns:
            허용된 HTTP 헤더 리스트 또는 ["*"]
        """
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]


# 전역 설정 인스턴스
settings = Settings()

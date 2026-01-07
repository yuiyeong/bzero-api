from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_update_user_duplicate_nickname(
    client: AsyncClient,
    test_session: AsyncSession,
    auth_headers_factory: Any,
):
    # Given: 사용자 A와 사용자 B가 존재함

    # 1. 사용자 A 생성 및 닉네임 설정 (이미 존재하는 닉네임 소유자)
    existing_nickname = "중복닉네임"
    headers_user_a = auth_headers_factory(
        provider_user_id="user-a",
        email="a@test.com",
    )

    # User A 생성
    resp_create_a = await client.post("/api/v1/users/me", headers=headers_user_a)
    assert resp_create_a.status_code == 201

    # User A 닉네임 설정
    resp_update_a = await client.patch(
        "/api/v1/users/me",
        headers=headers_user_a,
        json={"nickname": existing_nickname, "profile_emoji": "😎"},
    )
    assert resp_update_a.status_code == 200

    # 2. 사용자 B 생성 (로그인한 사용자)
    headers_user_b = auth_headers_factory(
        provider_user_id="user-b",
        email="b@test.com",
    )

    # User B 생성
    resp_create_b = await client.post("/api/v1/users/me", headers=headers_user_b)
    assert resp_create_b.status_code == 201

    # When: 사용자 B가 "중복닉네임"으로 변경 시도
    response = await client.patch(
        "/api/v1/users/me", json={"nickname": existing_nickname, "profile_emoji": "😊"}, headers=headers_user_b
    )

    # Then: 409 Conflict 반환 및 에러 코드 확인
    assert response.status_code == 409, f"Expected 409, got {response.status_code}. Response: {response.text}"
    error_data = response.json()
    assert error_data["error"]["code"] == "DUPLICATED_NICKNAME"

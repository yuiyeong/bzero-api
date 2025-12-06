"""User API e2e 테스트."""

from typing import Any

from httpx import AsyncClient


class TestCreateUser:
    """POST /api/v1/api/v1/users/me 테스트."""

    async def test_create_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """신규 사용자를 성공적으로 생성합니다."""
        # When
        response = await client.post("/api/v1/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 201

        data = response.json()["data"]
        assert data["email"] == "test@example.com"
        assert data["nickname"] is None
        assert data["profile_emoji"] is None
        assert data["current_points"] == 1000  # 초기 포인트
        assert data["is_profile_complete"] is False
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_user_duplicate_error(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """이미 존재하는 사용자를 생성하면 409 에러를 반환합니다."""
        # Given: 사용자 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 201

        # When: 동일한 사용자로 다시 생성 시도
        response = await client.post("/api/v1/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 409

    async def test_create_user_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 401 에러를 반환합니다."""
        # When
        response = await client.post("/api/v1/users/me")

        # Then
        assert response.status_code == 403  # HTTPBearer는 401이 아닌 403 반환


class TestGetMe:
    """GET /api/v1/users/me 테스트."""

    async def test_get_me_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """로그인한 사용자 정보를 조회합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["email"] == "test@example.com"
        assert data["current_points"] == 1000

    async def test_get_me_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 사용자를 조회하면 404 에러를 반환합니다."""
        # When: 사용자 생성 없이 조회
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_me_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 403 에러를 반환합니다."""
        # When
        response = await client.get("/api/v1/users/me")

        # Then
        assert response.status_code == 403


class TestUpdateUser:
    """PATCH /api/v1/users/me 테스트."""

    async def test_update_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자 프로필을 성공적으로 업데이트합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["nickname"] == "테스터"
        assert data["profile_emoji"] == "😊"
        assert data["is_profile_complete"] is True

    async def test_update_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """존재하지 않는 사용자를 업데이트하면 404 에러를 반환합니다."""
        # When
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 404

    async def test_update_user_invalid_nickname_too_short(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """닉네임이 너무 짧으면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "짧", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_nickname_special_chars(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """닉네임에 특수문자가 있으면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "테스터!", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_emoji_not_emoji(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """이모지가 아닌 문자를 입력하면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 일반 문자 입력
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "A"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_invalid_emoji_multiple(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """여러 개의 이모지를 입력하면 422 에러를 반환합니다."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When: 여러 이모지 입력
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "테스터", "profile_emoji": "😀😀"},
        )

        # Then
        assert response.status_code == 422

    async def test_update_user_unauthorized(
        self,
        client: AsyncClient,
    ):
        """인증 없이 요청하면 403 에러를 반환합니다."""
        # When
        response = await client.patch(
            "/api/v1/users/me",
            json={"nickname": "테스터", "profile_emoji": "😊"},
        )

        # Then
        assert response.status_code == 403


class TestUserFlow:
    """사용자 플로우 통합 테스트."""

    async def test_full_user_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """전체 사용자 플로우를 테스트합니다: 생성 -> 조회 -> 온보딩 완료."""
        # 1. 신규 사용자 등록
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["data"]["is_profile_complete"] is False
        assert response.json()["data"]["current_points"] == 1000

        # 2. 사용자 정보 조회
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["nickname"] is None

        # 3. 온보딩 완료 (프로필 설정)
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "여행자", "profile_emoji": "🚀"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["is_profile_complete"] is True
        assert response.json()["data"]["nickname"] == "여행자"
        assert response.json()["data"]["profile_emoji"] == "🚀"

        # 4. 업데이트된 정보 조회
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["nickname"] == "여행자"

    async def test_multiple_users_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
    ):
        """다른 사용자의 데이터는 서로 격리됩니다."""
        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )

        # When: 각각 사용자 생성 및 프로필 설정
        create_resp1 = await client.post("/api/v1/users/me", headers=headers_user1)
        assert create_resp1.status_code == 201

        create_resp2 = await client.post("/api/v1/users/me", headers=headers_user2)
        assert create_resp2.status_code == 201

        update_resp1 = await client.patch(
            "/api/v1/users/me",
            headers=headers_user1,
            json={"nickname": "유저원", "profile_emoji": "😊"},
        )
        assert update_resp1.status_code == 200
        assert update_resp1.json()["data"]["nickname"] == "유저원"

        update_resp2 = await client.patch(
            "/api/v1/users/me",
            headers=headers_user2,
            json={"nickname": "유저투", "profile_emoji": "🌟"},
        )
        assert update_resp2.status_code == 200
        assert update_resp2.json()["data"]["nickname"] == "유저투"

        # Then: 각 사용자는 자신의 정보만 조회
        response1 = await client.get("/api/v1/users/me", headers=headers_user1)
        response2 = await client.get("/api/v1/users/me", headers=headers_user2)

        assert response1.json()["data"]["nickname"] == "유저원"
        assert response1.json()["data"]["email"] == "user1@example.com"

        assert response2.json()["data"]["nickname"] == "유저투"
        assert response2.json()["data"]["email"] == "user2@example.com"

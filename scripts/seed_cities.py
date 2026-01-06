import asyncio

import httpx


# 설정
API_URL = "http://localhost:8000/api/v1/cities"
ADMIN_KEY = "test-key-for-local-dev"

# Coming Soon 도시 데이터 (10개)
CITIES = [
    {
        "name": "엠마시아",
        "theme": "희망",
        "emoji": "🌾",
        "color": "#84CC16",
        "description": "새벽빛이 스며드는 초원에서 희망을 심다",
    },
    {
        "name": "다마린",
        "theme": "고요",
        "emoji": "🌫️",
        "color": "#64748B",
        "description": "물안개 사이로 들리는 고요한 파도 소리",
    },
    {
        "name": "갈리시아",
        "theme": "성찰",
        "emoji": "🌇",
        "color": "#F59E0B",
        "description": "붉은 노을 아래, 나를 만나는 순례의 끝",
    },
    {
        "name": "벨라모어",
        "theme": "용서",
        "emoji": "🏔️",
        "color": "#E0F2FE",
        "description": "하얀 눈처럼 마음의 짐을 내려놓는 곳",
    },
    {
        "name": "아르카디아",
        "theme": "용기",
        "emoji": "🌊",
        "color": "#3B82F6",
        "description": "거센 물줄기 앞에서 두려움을 마주하다",
    },
    {
        "name": "루미나",
        "theme": "연결",
        "emoji": "✨",
        "color": "#A855F7",
        "description": "별빛 아래 잊혀진 인연을 되찾다",
    },
    {
        "name": "테라노바",
        "theme": "감사",
        "emoji": "🌻",
        "color": "#EAB308",
        "description": "황금빛 들판에서 작은 것에 감사하다",
    },
    {
        "name": "노크테르",
        "theme": "꿈",
        "emoji": "🌙",
        "color": "#6366F1",
        "description": "달빛 호수에 비친 진정한 꿈을 찾다",
    },
    {
        "name": "코르디아",
        "theme": "사랑",
        "emoji": "🌸",
        "color": "#EC4899",
        "description": "만개한 꽃들 사이에서 사랑을 배우다",
    },
    {
        "name": "에피스테마",
        "theme": "지혜",
        "emoji": "📚",
        "color": "#78716C",
        "description": "천년의 지혜가 잠든 책장 사이를 거닐다",
    },
]


async def seed_cities():
    async with httpx.AsyncClient() as client:
        # 1. 기존 도시 확인 (중복 방지)
        # API 키 없이도 조회 가능
        try:
            resp = await client.get(API_URL, params={"include_inactive": True})
            resp.raise_for_status()
            existing_names = {city["name"] for city in resp.json()["list"]}
            print(f"📋 기존 도시: {existing_names}")
        except Exception as e:
            print(f"❌ API 연결 실패 또는 조회 오류: {e}")
            print("💡 서버가 실행 중인지 확인해주세요 (uv run dev)")
            return

        headers = {"X-Admin-Key": ADMIN_KEY}

        for i, city_data in enumerate(CITIES):
            if city_data["name"] in existing_names:
                print(f"⏭️  Skip: {city_data['name']} (이미 존재)")
                continue

            payload = {
                "name": city_data["name"],
                "theme": city_data["theme"],
                "description": city_data["description"],
                "image_url": None,  # 이미지는 추후 추가
                "base_cost_points": 300,
                "base_duration_hours": 3,
                "is_active": False,  # Coming Soon
                "display_order": 10 + i,  # 기존 도시 뒤에 순차 배치
            }

            try:
                resp = await client.post(API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                print(f"✅ 생성 완료: {city_data['name']}")
            except httpx.HTTPStatusError as e:
                print(f"❌ 생성 실패 ({city_data['name']}): {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"❌ 오류 발생 ({city_data['name']}): {e}")


if __name__ == "__main__":
    asyncio.run(seed_cities())

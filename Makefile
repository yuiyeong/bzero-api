.PHONY: help up down logs ps restart clean exec-postgres exec-redis

# Docker Compose 파일
COMPOSE_FILE := docker-compose.dev.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

# 기본 타겟
help: ## 사용 가능한 명령어 목록 표시
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Docker 컨테이너 시작 (백그라운드)
	$(COMPOSE) up -d
	@echo "✓ 컨테이너가 시작되었습니다."
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis: localhost:6379"

down: ## Docker 컨테이너 중지 및 제거
	$(COMPOSE) down
	@echo "✓ 컨테이너가 중지되었습니다."

logs: ## 컨테이너 로그 확인 (실시간)
	$(COMPOSE) logs -f

ps: ## 실행 중인 컨테이너 상태 확인
	$(COMPOSE) ps

restart: ## 컨테이너 재시작
	$(COMPOSE) restart
	@echo "✓ 컨테이너가 재시작되었습니다."

clean: ## 컨테이너 중지 및 볼륨 삭제 (데이터 삭제 주의!)
	@echo "⚠️  경고: 모든 데이터베이스 데이터가 삭제됩니다!"
	@read -p "계속하시겠습니까? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(COMPOSE) down -v
	@echo "✓ 컨테이너와 볼륨이 삭제되었습니다."

exec-postgres: ## PostgreSQL 접속 (psql)
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-bezero} -d $${POSTGRES_DB:-bezero_dev}

exec-redis: ## Redis 접속 (redis-cli)
	$(COMPOSE) exec redis redis-cli

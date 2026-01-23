from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.notification import Notification
from bzero.domain.value_objects import Id, NotificationType
from bzero.infrastructure.db.notification_model import NotificationModel


class NotificationRepositoryCore:
    """Notification Repository 핵심 로직 (SQLAlchemy).

    동기/비동기 리포지토리에서 공통으로 사용합니다.
    """

    @staticmethod
    def create(session: Session, notification: Notification) -> Notification:
        validation_model = NotificationRepositoryCore._to_model(notification)
        session.add(validation_model)
        session.flush()
        session.refresh(validation_model)
        return NotificationRepositoryCore._to_entity(validation_model)

    @staticmethod
    def find_all_by_user_id(
        session: Session,
        user_id: Id,
        offset: int,
        limit: int,
    ) -> tuple[list[Notification], int]:
        # 1. Total Count
        count_stmt = (
            select(func.count()).select_from(NotificationModel).where(NotificationModel.user_id == user_id.value)
        )
        total = session.execute(count_stmt).scalar_one()

        # 2. List
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id.value)
            .order_by(NotificationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        models = session.execute(stmt).scalars().all()

        return [NotificationRepositoryCore._to_entity(m) for m in models], total

    @staticmethod
    def count_unread_by_user_id(session: Session, user_id: Id) -> int:
        stmt = (
            select(func.count())
            .select_from(NotificationModel)
            .where(
                NotificationModel.user_id == user_id.value,
                NotificationModel.is_read.is_(False),
            )
        )
        return session.execute(stmt).scalar_one()

    @staticmethod
    def find_by_id(session: Session, notification_id: Id) -> Notification | None:
        stmt = select(NotificationModel).where(NotificationModel.notification_id == notification_id.value)
        model = session.execute(stmt).scalar_one_or_none()
        return NotificationRepositoryCore._to_entity(model) if model else None

    @staticmethod
    def update(session: Session, notification: Notification) -> Notification:
        # Dirty check or full update
        # 여기서는 간단히 모든 필드 업데이트 (혹은 필요한 것만)
        # 이미 로드된 객체라면 session.commit() 시점에 반영되지만,
        # 명시적 update 쿼리가 필요하거나 Stateless한 경우를 위해 update 구문 사용 가능.
        # 하지만 보통 ORM 객체를 수정하고 flush 하는 방식을 사용.
        # 여기서는 객체 변경 후 flush 하는 방식을 가정 (호출 측에서 변경된 엔티티 전달 시 모델 매핑 필요할 수 있음)
        # 하지만 Notification 엔티티 -> 모델 변환 후 merge 방식이 안전할 수 있음.

        # 간단히 merge 사용
        model = NotificationRepositoryCore._to_model(notification)
        merged_model = session.merge(model)
        session.flush()
        return NotificationRepositoryCore._to_entity(merged_model)

    @staticmethod
    def mark_all_as_read(session: Session, user_id: Id) -> int:
        stmt = (
            update(NotificationModel)
            .where(
                NotificationModel.user_id == user_id.value,
                NotificationModel.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = session.execute(stmt)
        return result.rowcount

    @staticmethod
    def _to_model(entity: Notification) -> NotificationModel:
        return NotificationModel(
            notification_id=entity.notification_id.value,
            user_id=entity.user_id.value,
            type=entity.type.value,
            title=entity.title,
            message=entity.message,
            is_read=entity.is_read,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: NotificationModel) -> Notification:
        return Notification(
            notification_id=Id(model.notification_id),
            user_id=Id(model.user_id),
            type=NotificationType(model.type),
            title=model.title,
            message=model.message,
            is_read=model.is_read,
            created_at=model.created_at,
        )

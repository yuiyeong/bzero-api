from sqlalchemy.orm import Session

from bzero.infrastructure.db.task_failure_log_model import TaskFailureLogModel


class SqlAlchemyTaskFailureLogRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, model: TaskFailureLogModel) -> TaskFailureLogModel:
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return model

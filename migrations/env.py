from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

from bzero.core.settings import get_settings

# Import all models here for autogenerate to detect them
from bzero.infrastructure.db.airship_model import AirshipModel  # noqa: F401
from bzero.infrastructure.db.base import Base
from bzero.infrastructure.db.city_model import CityModel  # noqa: F401
from bzero.infrastructure.db.diary_model import DiaryModel  # noqa: F401
from bzero.infrastructure.db.point_transaction_model import PointTransactionModel  # noqa: F401
from bzero.infrastructure.db.ticket_model import TicketModel  # noqa: F401
from bzero.infrastructure.db.user_identity_model import UserIdentityModel  # noqa: F401
from bzero.infrastructure.db.user_model import UserModel  # noqa: F401


load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Override sqlalchemy.url from settings (alembic uses sync engine)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.sync_url)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(
        settings.database.sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

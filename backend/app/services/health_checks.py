from dataclasses import dataclass

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DatabaseReadinessResult:
    database_reachable: bool
    migrations_current: bool
    current_revisions: tuple[str, ...]
    expected_revisions: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.database_reachable and self.migrations_current


def get_expected_alembic_revisions(
    alembic_config_path: str = "alembic.ini",
) -> tuple[str, ...]:
    config = Config(alembic_config_path)
    script = ScriptDirectory.from_config(config)

    return tuple(sorted(script.get_heads()))


def check_database_readiness(
    db: Session,
    *,
    alembic_config_path: str = "alembic.ini",
) -> DatabaseReadinessResult:
    db.execute(text("SELECT 1"))

    connection = db.connection()
    migration_context = MigrationContext.configure(connection)

    current_revisions = tuple(sorted(migration_context.get_current_heads()))
    expected_revisions = get_expected_alembic_revisions(
        alembic_config_path,
    )

    return DatabaseReadinessResult(
        database_reachable=True,
        migrations_current=(current_revisions == expected_revisions),
        current_revisions=current_revisions,
        expected_revisions=expected_revisions,
    )

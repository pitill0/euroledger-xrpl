from unittest.mock import Mock, patch

from sqlalchemy import text

from app.services.health_checks import (
    check_database_readiness,
    get_expected_alembic_revisions,
)


def test_get_expected_alembic_revisions() -> None:
    script = Mock()
    script.get_heads.return_value = [
        "revision-b",
        "revision-a",
    ]

    with (
        patch(
            "app.services.health_checks.Config",
        ) as config_class,
        patch(
            "app.services.health_checks.ScriptDirectory.from_config",
            return_value=script,
        ) as from_config,
    ):
        result = get_expected_alembic_revisions(
            "custom-alembic.ini",
        )

    config_class.assert_called_once_with(
        "custom-alembic.ini",
    )
    from_config.assert_called_once_with(
        config_class.return_value,
    )

    assert result == (
        "revision-a",
        "revision-b",
    )


def test_database_readiness_when_migrations_are_current() -> None:
    db = Mock()
    connection = Mock()
    db.connection.return_value = connection

    migration_context = Mock()
    migration_context.get_current_heads.return_value = [
        "current-head",
    ]

    with (
        patch(
            "app.services.health_checks.MigrationContext.configure",
            return_value=migration_context,
        ) as configure_context,
        patch(
            "app.services.health_checks.get_expected_alembic_revisions",
            return_value=("current-head",),
        ),
    ):
        result = check_database_readiness(db)

    db.execute.assert_called_once()

    executed_statement = db.execute.call_args.args[0]
    assert str(executed_statement) == str(text("SELECT 1"))

    db.connection.assert_called_once_with()
    configure_context.assert_called_once_with(connection)

    assert result.database_reachable is True
    assert result.migrations_current is True
    assert result.ready is True
    assert result.current_revisions == ("current-head",)
    assert result.expected_revisions == ("current-head",)


def test_database_readiness_when_migrations_are_outdated() -> None:
    db = Mock()
    connection = Mock()
    db.connection.return_value = connection

    migration_context = Mock()
    migration_context.get_current_heads.return_value = [
        "previous-head",
    ]

    with (
        patch(
            "app.services.health_checks.MigrationContext.configure",
            return_value=migration_context,
        ),
        patch(
            "app.services.health_checks.get_expected_alembic_revisions",
            return_value=("current-head",),
        ),
    ):
        result = check_database_readiness(db)

    assert result.database_reachable is True
    assert result.migrations_current is False
    assert result.ready is False
    assert result.current_revisions == ("previous-head",)
    assert result.expected_revisions == ("current-head",)

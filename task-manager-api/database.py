from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def commit():
    """Confirma a transação atual; desfaz tudo se o commit falhar."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def enable_sqlite_foreign_keys(engine):
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

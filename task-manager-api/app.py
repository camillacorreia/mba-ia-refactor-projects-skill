from app_factory import create_app
from config.settings import Settings
from database import db  # noqa: F401  mantido para quem importava "from app import app, db"

settings = Settings.from_env()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)

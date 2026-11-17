from app_factory import create_app
from config.settings import settings
from database import db  # noqa: F401  seed.py importa "from app import app, db"

app = create_app(settings)

if __name__ == '__main__':
    app.run(debug=settings.debug, host=settings.host, port=settings.port)

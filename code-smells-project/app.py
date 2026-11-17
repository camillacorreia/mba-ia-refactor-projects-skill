"""Entry point: `python app.py` ou `flask --app app run`."""
from src.app import create_app
from src.config.settings import Settings

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    app.logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)

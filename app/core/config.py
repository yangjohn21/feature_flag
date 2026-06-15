from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "ScalableFastAPIProject"
    debug: bool = False

    # Full connection string — DigitalOcean injects DATABASE_URL automatically
    database_url: str | None = None

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "app"

    @staticmethod
    def _normalize_postgres_url(url: str) -> str:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self._normalize_postgres_url(self.database_url)

        # Default to a local SQLite database for developer convenience
        # Use a file-based DB at ./<db_name>.db so the app state persists locally
        return f"sqlite:///./{self.db_name}.db"


config = Config()

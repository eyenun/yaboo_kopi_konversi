from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Yaboo Kopi AI Cashflow & Inventory API"
    APP_ENV: str = "development"
    GEMINI_API_KEY: str = "BELUM_DIISI"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_gemini_ready(self) -> bool:
        return bool(self.GEMINI_API_KEY) and self.GEMINI_API_KEY != "BELUM_DIISI"


settings = Settings()

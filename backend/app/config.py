from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    csi_udp_host: str = "0.0.0.0"
    csi_udp_port: int = 5005

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    cors_origins: str = "http://localhost:3000"

    breathing_min_bpm: float = 8.0
    breathing_max_bpm: float = 30.0
    wetbulb_heat_stress_c: float = 28.0
    motion_still_seconds: float = 5.0

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    supervisor_phone_number: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

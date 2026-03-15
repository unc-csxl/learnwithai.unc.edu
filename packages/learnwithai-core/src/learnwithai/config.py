from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "learnwithai"
    environment: str = "development"

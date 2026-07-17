"""DTO для регистрации, входа и JWT."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    """Данные для регистрации нового пользователя."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"email": "manager@autocrm.ru", "password": "SecurePass123"}]
        }
    )

    email: str = Field(
        min_length=3,
        max_length=255,
        title="Email",
        description="Email пользователя. Используется как логин.",
        examples=["manager@autocrm.ru"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        title="Пароль",
        description="Пароль пользователя. От 8 до 72 символов.",
        examples=["SecurePass123"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Некорректный email")
        return normalized


class LoginRequest(BaseModel):
    """Данные для входа в систему."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"email": "manager@autocrm.ru", "password": "SecurePass123"}]
        }
    )

    email: str = Field(
        min_length=3,
        max_length=255,
        title="Email",
        description="Email, указанный при регистрации.",
        examples=["manager@autocrm.ru"],
    )
    password: str = Field(
        min_length=1,
        max_length=72,
        title="Пароль",
        description="Пароль от учётной записи.",
        examples=["SecurePass123"],
    )


class TokenResponse(BaseModel):
    """JWT-токен доступа."""

    access_token: str = Field(
        title="Токен доступа",
        description="JWT-токен. Вставьте его в окно Authorize без слова Bearer.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        title="Тип токена",
        description="Тип токена авторизации.",
        examples=["bearer"],
    )

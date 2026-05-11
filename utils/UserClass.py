from dataclasses import dataclass


@dataclass
class User:
    name: str = "Пользователь"
    username: str = "user"
    priority: str = "default"
    role: str | None = None
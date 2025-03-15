# crud/user.py
from models.user import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Настройка контекста хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_username(db: Session, username: str):
    """
    Получает пользователя по имени пользователя (username).
    :param db: Сессия базы данных
    :param username: Имя пользователя
    :return: Объект пользователя (User) или None
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """
    Получает пользователя по email.
    :param db: Сессия базы данных
    :param email: Email пользователя
    :return: Объект пользователя (User) или None
    """
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    age: int,
    country: str,
    fullname: str,
):
    """
    Создаёт нового пользователя в базе данных.
    :param db: Сессия базы данных
    :param username: Имя пользователя
    :param email: Email пользователя
    :param password: Пароль пользователя
    :return: Объект созданного пользователя (User)
    """
    hashed_password = pwd_context.hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        age=age,
        country=country,
        fullname=fullname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    """
    Проверяет, существует ли пользователь с заданным username и совпадает ли пароль.
    :param db: Сессия базы данных
    :param username: Имя пользователя
    :param password: Пароль
    :return: Объект пользователя (User), если аутентификация прошла успешно, иначе None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def verify_password(plain_password, hashed_password):
    """
    Проверяет, совпадает ли хэш пароля с введённым паролем.
    :param plain_password: Пароль в открытом виде
    :param hashed_password: Хэш пароля
    :return: True, если пароли совпадают, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)

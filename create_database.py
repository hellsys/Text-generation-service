# create_tables.py
from db import Base, engine

# Создание таблиц
Base.metadata.create_all(bind=engine)

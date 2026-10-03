from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 切れた接続を使わないよう、使う前に繋がるか確かめる
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    # リクエストごとにセッションを作り、終わったら閉じる
    with SessionLocal() as db:
        yield db

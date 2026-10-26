"""公式のお題の登録(seed/seed_cards.py)のテスト。

確認していること:
- ファイル名が種類になって、お題が登録される
- 2回実行しても、お題が増えない
- すでにある同じ内容の公式のお題は、新しく作らずに種類と補足を合わせる
- 自分で作ったお題は、同じ内容でも変えない
- 知らない種類のファイルや、同じ内容の重複はエラーにする
- 実際の seed/decks のファイルが、3種類とも正しく読める

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
"""
import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Card
from seed.seed_cards import DECKS_DIR, load_decks, seed_official_cards

USER_A = uuid.uuid4()


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, autoflush=False)() as session:
        yield session


def write_deck(decks_dir, category, cards):
    path = decks_dir / f"{category}.json"
    path.write_text(json.dumps(cards, ensure_ascii=False), encoding="utf-8")


def official_cards(db):
    cards = db.query(Card).filter(Card.create_user_id.is_(None))
    return {c.content: (c.description, c.category) for c in cards}


def test_adds_cards_with_category(db, tmp_path):
    write_deck(tmp_path, "interview", [{"content": "志望動機は?"}])
    write_deck(
        tmp_path,
        "small_talk",
        [{"content": "休日は?", "description": "答えやすい話題"}],
    )

    assert seed_official_cards(db, tmp_path)["added"] == 2
    assert official_cards(db) == {
        "志望動機は?": (None, "interview"),
        "休日は?": ("答えやすい話題", "small_talk"),
    }


def test_running_twice_does_not_add(db, tmp_path):
    write_deck(tmp_path, "interview", [{"content": "志望動機は?"}])
    seed_official_cards(db, tmp_path)

    counts = seed_official_cards(db, tmp_path)
    assert counts == {"added": 0, "updated": 0, "unchanged": 1}
    assert len(official_cards(db)) == 1


def test_existing_official_card_gets_category(db, tmp_path):
    db.add(Card(content="休日は?"))  # 種類が無いころに登録したお題
    db.commit()
    write_deck(tmp_path, "small_talk", [{"content": "休日は?"}])

    assert seed_official_cards(db, tmp_path)["updated"] == 1
    assert official_cards(db) == {"休日は?": (None, "small_talk")}


def test_user_card_is_not_changed(db, tmp_path):
    db.add(Card(content="休日は?", create_user_id=USER_A))
    db.commit()
    write_deck(tmp_path, "small_talk", [{"content": "休日は?"}])

    seed_official_cards(db, tmp_path)
    user_card = db.query(Card).filter(Card.create_user_id == USER_A).one()
    assert user_card.category is None
    # 公式のお題は、別に1件作られる
    assert official_cards(db) == {"休日は?": (None, "small_talk")}


def test_rejects_unknown_category_file(db, tmp_path):
    write_deck(tmp_path, "unknown", [{"content": "x"}])
    with pytest.raises(ValueError):
        seed_official_cards(db, tmp_path)


def test_rejects_duplicate_content(db, tmp_path):
    write_deck(tmp_path, "interview", [{"content": "x"}])
    write_deck(tmp_path, "small_talk", [{"content": "x"}])
    with pytest.raises(ValueError):
        seed_official_cards(db, tmp_path)


def test_real_deck_files_are_valid():
    cards = load_decks(DECKS_DIR)
    assert {c["category"] for c in cards} == {
        "interview",
        "reverse_question",
        "small_talk",
    }

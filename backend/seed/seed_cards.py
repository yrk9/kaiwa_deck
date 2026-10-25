"""公式のお題(作成者なし)を、デッキの種類ごとにDBへ登録するスクリプト。

実行方法: python -m seed.seed_cards
seed/decks/ のファイル名が、お題の種類(category)になる。
すでに同じ内容の公式のお題があれば、新しく作らずに種類と補足を合わせる
(何度実行しても、件数が増えないようにするため)。
"""
import json
from pathlib import Path
from typing import get_args

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Card
from app.schemas.card import CardCategory

DECKS_DIR = Path(__file__).parent / "decks"


def load_decks(decks_dir: Path) -> list[dict]:
    """すべてのファイルのお題を、種類つきの1つのリストにする。"""
    cards = []
    for path in sorted(decks_dir.glob("*.json")):
        category = path.stem
        if category not in get_args(CardCategory):
            raise ValueError(f"unknown category file: {path.name}")
        for card in json.loads(path.read_text(encoding="utf-8")):
            cards.append({**card, "category": category})

    # 同じ内容が2つあると、どちらの種類にするか決められない
    contents = [card["content"] for card in cards]
    if len(contents) != len(set(contents)):
        raise ValueError("the same content appears more than once")
    return cards


def seed_official_cards(
    db: Session, decks_dir: Path = DECKS_DIR
) -> dict[str, int]:
    existing = {
        card.content: card
        for card in db.query(Card).filter(Card.create_user_id.is_(None))
    }
    counts = {"added": 0, "updated": 0, "unchanged": 0}
    for data in load_decks(decks_dir):
        content = data["content"]
        description = data.get("description")
        category = data["category"]
        card = existing.get(content)
        if card is None:
            db.add(
                Card(
                    content=content,
                    description=description,
                    category=category,
                )
            )
            counts["added"] += 1
        elif (card.description, card.category) != (description, category):
            card.description = description
            card.category = category
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
    db.commit()
    return counts


def main() -> None:
    with SessionLocal() as db:
        print(seed_official_cards(db))


if __name__ == "__main__":
    main()

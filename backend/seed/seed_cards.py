"""公式のお題(作成者なし)をDBに投入するスクリプト。

実行方法: python -m seed.seed_cards
既に同じcontentの公式カードがあれば、重複登録せずスキップする
(何度実行しても件数が増えすぎないようにするため)。
"""
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models import Card

DATA_PATH = Path(__file__).parent / "official_cards.json"


def seed_official_cards() -> None:
    cards = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    with SessionLocal() as db:
        existing = {
            content
            for (content,) in db.query(Card.content).filter(
                Card.create_user_id.is_(None)
            )
        }
        added = 0
        for card in cards:
            if card["content"] in existing:
                continue
            db.add(Card(**card))
            added += 1
        db.commit()

    print(f"added {added} card(s), skipped {len(cards) - added}")


if __name__ == "__main__":
    seed_official_cards()

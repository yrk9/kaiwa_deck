from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    cards,
    deck_cards,
    decks,
    drawn,
    room_state,
    room_users,
    rooms,
)

app = FastAPI(title="kaiwa_deck API")

# ログインはCookieではなくAuthorizationヘッダーで行うので、credentialsは不要
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(cards.router)
app.include_router(decks.router)
app.include_router(deck_cards.router)
app.include_router(rooms.router)
app.include_router(room_users.router)
app.include_router(drawn.router)
app.include_router(room_state.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

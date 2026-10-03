from fastapi import FastAPI

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

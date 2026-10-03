from fastapi import FastAPI

from app.routers import cards, decks

app = FastAPI(title="kaiwa_deck API")
app.include_router(cards.router)
app.include_router(decks.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

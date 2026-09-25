from fastapi import FastAPI

from app.routers import cards

app = FastAPI(title="kaiwa_deck API")
app.include_router(cards.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

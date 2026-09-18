from fastapi import FastAPI

app = FastAPI(title="kaiwa_deck API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

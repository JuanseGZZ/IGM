from fastapi import FastAPI
from api import users_router, products_router

def create_app() -> FastAPI:
    app = FastAPI(title="App Template")

    # El server compone las APIs
    app.include_router(users_router)
    app.include_router(products_router)

    @app.get("/")
    def root():
        return {"status": "running"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
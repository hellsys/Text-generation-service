from fastapi import FastAPI
from routers import auth, generate, synonyms
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Datasets Generation Service",
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)

app.include_router(generate.router)
app.include_router(synonyms.router)
app.include_router(auth.router, prefix="/auth")

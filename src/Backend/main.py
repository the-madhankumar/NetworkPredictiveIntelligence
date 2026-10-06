from fastapi import FastAPI
from routes.network import network_router
from routes.assistant import assistant_router
from database import Base, engine

from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(
    bind=engine
)

app = FastAPI()

origins = [
   "http://localhost:5173",
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins, 
        allow_credentials=True,
        allow_methods=["*"], 
        allow_headers=["*"], 
    )

app.include_router(
    router=network_router
)

app.include_router(
    router=assistant_router
)


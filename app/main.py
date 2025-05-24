# app/main.py

from fastapi import FastAPI
from app.api.routes import user, auth, hymnbook, hymn, mapping
from app.db.session import engine
from app.db.base_class import Base
app = FastAPI(title="Hymnal App API")


Base.metadata.create_all(bind=engine)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(hymnbook.router)
app.include_router(hymn.router)
app.include_router(mapping.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hymnal API"}

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.database import Base, engine
from user_management.controller.api.v1 import user
from hymnal.controllers.api.v1 import hymn

app = FastAPI(
    title="Hymnal API",
    description="A FastAPI-based API for managing hymn books and hymns, with admin user management and search functionality.",
    version="1.0.0",
)

# Serve media files
app.mount("/media", StaticFiles(directory="media"), name="media")



# Include routers
app.include_router(user.router)
app.include_router(hymn.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hymnal API"}
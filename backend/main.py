"""
FastAPI Hauptanwendung für Excel zu Berechnungsvorschriften
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import berechnungsvorschriften
import os
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.info("Starte FastAPI Middleware...")

# FastAPI App erstellen
app = FastAPI(
    title="Excel zu Berechnungsvorschriften API",
    description="API zur Generierung und Verwaltung von Berechnungsvorschriften aus Excel-Formeln",
    version="1.0.0"
)

# CORS-Middleware für Frontend-Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion sollte dies eingeschränkt werden
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes registrieren
logger.info("Registriere API-Routes...")
app.include_router(
    berechnungsvorschriften.router,
    prefix="/api/berechnungsvorschriften",
    tags=["Berechnungsvorschriften"]
)
logger.info("FastAPI Middleware erfolgreich gestartet")


@app.get("/")
async def root():
    """Root-Endpunkt"""
    return {
        "message": "Excel zu Berechnungsvorschriften API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health-Check Endpunkt"""
    return {"status": "healthy"}

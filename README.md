# Excel zu Berechnungsvorschriften

Ein Python-Web-Projekt zur automatischen Generierung von menschenlesbaren Berechnungsvorschriften aus Excel-Formeln mit Hilfe von LLM (OpenAI GPT-5-nano).

## Features

- **LLM-basierte Generierung**: Excel-Formeln werden automatisch in menschenlesbaren Pseudocode umgewandelt
- **Programmatische Verlinkung**: Variablen werden automatisch mit bestehenden Berechnungsvorschriften verlinkt
- **Metadaten-basierte Suche**: Berechnungsvorschriften sind über alle Metadaten-Felder auffindbar
- **Abhängigkeitsvisualisierung**: Für jede Berechnungsvorschrift werden Abhängigkeiten angezeigt
- **Anklickbare Navigation**: Variablen im Pseudocode sind anklickbar und führen zu referenzierten Berechnungsvorschriften
- **Versionierung**: Jede Änderung erstellt eine neue Version

## Voraussetzungen

- Docker und Docker Compose
- OpenAI API Key (für GPT-5-nano)

## Installation

1. Repository klonen oder Dateien kopieren

2. Umgebungsvariablen konfigurieren:
   ```bash
   cp .env.example .env
   # .env bearbeiten und OPENAI_API_KEY eintragen
   ```

3. Docker Compose starten:
   ```bash
   docker compose up -d
   ```

## Verwendung

1. **Frontend öffnen**: http://localhost
2. **Neue Berechnungsvorschrift erstellen**:
   - Tabellenidentifikator, Tabellenblatt, Zellenidentifikator, Beschreibung und Formel eingeben
   - "Berechnungsvorschrift generieren" klicken
   - Das System generiert automatisch eine strukturierte Berechnungsvorschrift

3. **Berechnungsvorschriften verwalten**:
   - Alle Berechnungsvorschriften anzeigen: http://localhost/berechnungsvorschriften.html
   - Details anzeigen: Klick auf eine Berechnungsvorschrift
   - Bearbeiten: "Bearbeiten"-Button in der Detailansicht
   - Suchen: Metadaten-Filter in der Übersicht

## API-Dokumentation

Die API-Dokumentation ist verfügbar unter:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Projektstruktur

```
/
├── docker-compose.yml          # Docker Compose Konfiguration
├── nginx.conf                  # Nginx Konfiguration
├── fuseki-config.ttl          # Fuseki Konfiguration
├── backend/                    # FastAPI Backend
│   ├── main.py                # FastAPI App
│   ├── models/                # Pydantic Models
│   ├── services/              # Business Logic
│   ├── api/routes/            # API Endpunkte
│   └── prompts/               # LLM Prompts und Beispiele
└── frontend/                   # HTML/JS Frontend
    ├── index.html             # Eingabeformular
    ├── berechnungsvorschriften.html  # Übersicht
    └── berechnungsvorschrift.html   # Detailansicht
```

## Technologie-Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/JavaScript mit Bootstrap 5
- **Datenbank**: Apache Jena Fuseki (RDF-Triplestore)
- **LLM**: OpenAI GPT-5-nano API
- **Container**: Docker Compose

## Entwicklung

Für Entwicklung mit Hot-Reload:

```bash
docker compose up
```

Die Services sind verfügbar unter:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- Fuseki Admin: http://localhost:3030

## Hinweise

- Die OpenAI API Key muss in der `.env` Datei gesetzt werden
- Bei ersten Start kann Fuseki etwas Zeit zum Initialisieren benötigen
- GPT-5-nano wird verwendet (falls nicht verfügbar, wird auf gpt-4o-mini zurückgegriffen)

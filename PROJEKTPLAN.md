# Projektarchitektur: Excel zu Berechnungsvorschriften

## Übersicht

Ein Python-Web-Projekt, das manuell eingegebene Excel-Zellendaten (Tabellenidentifikator, Tabellenblatt, Beschreibung, Formel) über ein Bootstrap-basiertes Web-Frontend entgegennimmt und daraus mit Hilfe von OpenAI GPT-5-nano strukturierte Berechnungsvorschriften mit Metadaten erzeugt. 

**Kernfunktionalität:**
- **LLM-basierte Generierung**: Excel-Formeln werden in menschenlesbaren Pseudocode umgewandelt, Excel-Funktionen werden vereinfacht dargestellt
- **Programmatische Verlinkung**: Variablen werden automatisch mit bestehenden Berechnungsvorschriften verlinkt, basierend auf Metadaten-Vergleich (Name, Symbol, Kategorie, Datentyp, Einheit)
- **Metadaten-basierte Suche**: Berechnungsvorschriften sind über alle Metadaten-Felder auffindbar
- **Abhängigkeitsvisualisierung**: Für jede Berechnungsvorschrift werden zwei Listen angezeigt: "Wird verwendet in" (wer referenziert diese) und "Verwendet folgende Berechnungsvorschriften" (was wird referenziert)
- **Anklickbare Navigation**: Variablen im Pseudocode sind anklickbar und führen zu den referenzierten Berechnungsvorschriften

**Technische Architektur:**
- **Frontend**: Vanilla HTML/JavaScript mit Bootstrap 5, JSON-basierte Kommunikation
- **Backend**: FastAPI (Python) als Middleware
- **Datenbank**: Apache Jena Fuseki (RDF-Triplestore) für persistente Speicherung
- **Datenformat**: JSON in der Webanwendung, RDF-Konvertierung in der Middleware
- **Container**: Docker Compose mit drei Services (Frontend/Nginx, Middleware/FastAPI, Fuseki)

**Besonderheiten:**
- Zellendaten werden nicht gespeichert, nur als Quelle-Information in der Berechnungsvorschrift referenziert
- Keine Validierungen (keine Prüfungen auf leere Zellen, keine Division-durch-0-Checks)
- Fehler in Excel-Formeln werden nicht korrigiert, sondern 1:1 übernommen
- Prompt- und Beispiel-Dateien für konsistente LLM-Ergebnisse (Few-Shot Learning)

## Technologie-Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/JavaScript mit Bootstrap (JSON-basiert)
- **Frontend-Bibliotheken**: Bootstrap 5 (CSS/JS), für einfache und hilfreiche UI-Komponenten
- **Datenbank**: Apache Jena Fuseki (RDF-Triplestore)
- **LLM**: OpenAI GPT-5-nano API
- **Middleware**: JSON-zu-RDF Konvertierung
- **Container**: Docker Compose

## Datenmodell

### JSON-Struktur (Webanwendung):

#### Zelleneingabe (nur Input, wird nicht gespeichert)

```json
{
  "tabellenidentifikator": "Tabelle1",
  "tabellenblatt": "Sheet1",
  "zellenidentifikator": "A1",  // Z.B. "A1", "B5", etc. - für Matching erforderlich
  "beschreibung": "Gesamtkosten berechnen",
  "formel": "=A1+B1*C1"
}
```

#### Berechnungsvorschrift (strukturiert, wird gespeichert)

```json
{
  "id": "uuid",
  "name": "monatliches Nettogehalt",
  "formel": "Jahresnettogehalt/12",  // Menschenlesbarer Pseudocode (keine Excel-Syntax, keine Kommentare)
  "variablen": [
    {
      "name": "Jahresnettogehalt",  // Gut lesbarer Variablenname
      "referenz_berechnungsvorschrift_id": "uuid-xyz",  // optional, wenn Variable eine andere BV ist
      "ist_primitive": false  // true wenn es keine Referenz zu einer anderen BV gibt
    }
  ],
  "metadaten": {
    "kategorie": "Gehalt",
    "symbol": "MNG",
    "datentyp": "decimal",
    "einheit": "EUR"
  },
  "quelle": {  // Optional: Referenz zur ursprünglichen Zelle (für Matching)
    "tabellenidentifikator": "Tabelle1",
    "tabellenblatt": "Sheet1",
    "zellenidentifikator": "A1",  // Z.B. "A1" oder "B5" - für Matching erforderlich
    "beschreibung": "Gesamtkosten berechnen"  // Alternative für Matching
  },
  "version": 1,  // Versionsnummer
  "erstellt_am": "2026-01-23T10:00:00Z",
  "geaendert_am": "2026-01-23T10:00:00Z"
}
```

### RDF-Ontologie (nach Konvertierung):

Die JSON-Struktur wird in der Middleware zu RDF konvertiert. Nur Berechnungsvorschriften werden gespeichert:

```
Berechnungsvorschrift
  - hatName (string)                    # Suchbar
  - hatFormel (string)
  - hatKategorie (string)                # Suchbar
  - hatSymbol (string)                   # Suchbar
  - hatDatentyp (string)                 # Suchbar
  - hatEinheit (string)                  # Suchbar
  - hatVariable (Variable)
  - hatQuelleTabellenidentifikator (string, optional)  # Für Matching
  - hatQuelleTabellenblatt (string, optional)          # Für Matching
  - hatQuelleZellenidentifikator (string, optional)    # Für Matching (neu)
  - hatQuelleBeschreibung (string, optional)           # Für Matching
  - hatVersion (integer)                 # Versionsnummer
  - hatErstelltAm (timestamp)            # Erstellungszeitpunkt
  - hatGeaendertAm (timestamp)           # Letzte Änderung

Variable
  - hatName (string)
  - referenziertBerechnungsvorschrift (Berechnungsvorschrift, optional)
  - istPrimitive (boolean)
```

## Projektstruktur

```
/
├── docker-compose.yml          # Docker Compose Konfiguration
├── .env.example                # Beispiel-Umgebungsvariablen
├── nginx.conf                  # Nginx Konfiguration für Frontend
├── fuseki-config.ttl          # Fuseki Konfigurationsdatei
├── backend/
│   ├── Dockerfile              # Dockerfile für Middleware
│   ├── requirements.txt       # Python Dependencies
│   ├── main.py                 # FastAPI Hauptanwendung
│   ├── models/
│   │   ├── __init__.py
│   │   ├── zelleneingabe.py   # Pydantic Model für Input (wird nicht gespeichert)
│   │   └── berechnungsvorschrift.py  # Pydantic Model für Berechnungsvorschrift
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py     # OpenAI GPT-5-nano Integration
│   │   ├── rdf_service.py     # Jena Fuseki SPARQL Client
│   │   ├── json_rdf_converter.py  # JSON-zu-RDF Konvertierung (Middleware)
│   │   └── berechnungsvorschrift_matcher.py  # Programmatische Prüfung auf bestehende Berechnungsvorschriften anhand Metadaten
│   ├── prompts/
│   │   ├── berechnungsvorschrift_prompt.txt  # Prompt für LLM zur Generierung von Berechnungsvorschriften
│   │   └── berechnungsvorschrift_beispiel.txt  # Beispiel für Few-Shot Learning (Text mit Beispieleingabe und gewünschtem JSON)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── berechnungsvorschriften.py  # CRUD für Berechnungsvorschriften + Suche
│   └── utils/
│       ├── __init__.py
│       └── rdf_helper.py      # RDF-URI Generierung, SPARQL Templates
└── frontend/
    ├── index.html              # Hauptseite mit Eingabeformular
    ├── berechnungsvorschriften.html  # Übersicht aller Vorschriften
    ├── berechnungsvorschrift.html  # Detailansicht/Editor für einzelne Vorschrift
    ├── css/
    │   └── style.css          # Zusätzliche Custom-Styles (Bootstrap wird via CDN geladen)
    └── js/
        ├── api.js             # API-Client
        └── berechnungsvorschriften.js  # Berechnungsvorschriften-Verwaltung und Suche
    # Bootstrap 5 wird via CDN eingebunden (CSS + JS Bundle)
└── fuseki-data/               # Persistente Fuseki-Datenbank (wird von Docker erstellt)
```

## Funktionsweise

### 1. Zelleneingabe

- Benutzer gibt im Frontend ein:
  - Tabellenidentifikator (z.B. "Tabelle1")
  - Tabellenblatt (z.B. "Sheet1")
  - Zellenidentifikator (z.B. "A1", "B5") - für Matching erforderlich
  - Beschreibung (z.B. "Gesamtkosten berechnen") - Alternative für Matching
  - Formel (z.B. "=A1+B1*C1")
- Frontend sendet POST-Request an `/api/berechnungsvorschriften` mit Zellendaten

### 2. LLM-Verarbeitung

#### Prompt-Datei (`prompts/berechnungsvorschrift_prompt.txt`)
- Enthält die Anweisungen für das LLM
- Beschreibt das gewünschte JSON-Format für die Berechnungsvorschrift
- Erklärt die Struktur von Variablen und Metadaten
- Gibt Anweisungen zur Extraktion von Variablen aus Formeln
- Beschreibt die Zuordnung von Metadaten (Kategorie, Symbol, Datentyp, Einheit)
- **Excel-Formel-Verarbeitung**:
  - Keine Prüfungen auf leere Zellen oder Division durch 0
  - Excel-Funktionen in Pseudocode umwandeln (z.B. SUMME → Addition, WENN → einfache Bedingung)
  - Sehr einfach halten, keine Edge-Cases abprüfen
- **Pseudocode-Anforderungen**:
  - Menschenlesbare Formel (keine Excel-Syntax)
  - Variablen sollen gut lesbar sein (sprechende Namen)
  - Keine Kommentare im Pseudocode
  - Fehler in der Excel-Formel sollen NICHT korrigiert werden (Original beibehalten)

#### Beispiel-Datei (`prompts/berechnungsvorschrift_beispiel.txt`)
- Enthält eine Beispieleingabe (Zellendaten) und das gewünschte JSON-Output
- Dient als Few-Shot Learning Beispiel für konsistente Ergebnisse
- Format: Text mit Beispieleingabe (Tabellenidentifikator, Tabellenblatt, Zellenidentifikator, Beschreibung, Formel) und dem entsprechenden gewünschten JSON-Output
- Zeigt die korrekte Struktur mit Variablen, Metadaten und optionalen Quell-Informationen
- Beispiel sollte typische Anwendungsfälle abdecken

- Backend analysiert die Formel und extrahiert Variablen/Referenzen
- LLM-Service (OpenAI GPT-5-nano) lädt:
  - Prompt aus `prompts/berechnungsvorschrift_prompt.txt`
  - Beispiel aus `prompts/berechnungsvorschrift_beispiel.txt` (Few-Shot Learning mit Beispieleingabe und gewünschtem JSON)
- Kombiniert Prompt, Beispiel und Zellendaten zu einem vollständigen LLM-Request
- LLM erstellt strukturierte Berechnungsvorschrift basierend auf Prompt und Beispiel:
  - Name (z.B. "monatliches Nettogehalt")
  - Menschenlesbare Formel/Pseudocode (z.B. "Jahresnettogehalt/12") - keine Excel-Syntax, gut lesbare Variablen, keine Kommentare
  - Excel-Funktionen werden in einfachen Pseudocode umgewandelt (z.B. SUMME(A1:A10) → "Wert1 + Wert2 + ... + Wert10")
  - Keine Validierungen (keine Prüfungen auf leere Zellen, keine Division-durch-0-Checks)
  - Fehler in der Excel-Formel werden nicht korrigiert, sondern 1:1 übernommen
  - Variablen-Liste (ohne Referenzen - diese werden programmatisch zugeordnet)
  - Metadaten: Kategorie, Symbol, Datentyp, Einheit
- **Programmatische Prüfung auf bestehende Berechnungsvorschriften** (Backend-Code, `berechnungsvorschrift_matcher.py`):
  - Sucht in der Datenbank nach bestehenden Berechnungsvorschriften anhand der Matching-Kriterien:
    - **Kriterium 1**: Tabellenidentifikator, Tabellenblatt und Zellenidentifikator müssen identisch sein (aus Quelle-Information)
    - **ODER Kriterium 2**: Beschreibung ist identisch
  - Wenn **genau eine** passende Berechnungsvorschrift gefunden wird, verlinkt Variablen automatisch (setzt `referenz_berechnungsvorschrift_id` und `ist_primitive=false`)
  - Wenn **mehrere** passende gefunden werden, werden alle Optionen zurückgegeben - Benutzer wird im Frontend gefragt (nicht automatisch verlinken)
  - Wenn **keine** passende gefunden wird, bleibt Variable als primitiv markiert (`ist_primitive=true`)
  - **Zirkuläre Abhängigkeiten**: Prüfung verhindert zirkuläre Referenzen (z.B. A verwendet B, B verwendet A)
- Erstellt neue Berechnungsvorschrift als JSON-Objekt (Zellendaten werden nur als Quelle-Information gespeichert)

### 3. JSON-zu-RDF Konvertierung (Middleware)

- Konvertiert JSON-Struktur zu RDF-Triples:
  - Neue Berechnungsvorschrift mit Metadaten (alle Metadaten-Felder werden indiziert für Suche)
  - Variablen mit Verlinkungen zu anderen Berechnungsvorschriften
  - Optionale Quelle-Information (Tabellenidentifikator, Tabellenblatt, Beschreibung)
- Speichert in Jena Fuseki über SPARQL UPDATE

### 4. UI-Darstellung

- Berechnungsvorschriften werden strukturiert angezeigt (Bootstrap Cards oder Tables) - Name = Formel
- Variablen in der Formel sind anklickbar (Bootstrap Badges oder Links) - z.B. "Jahresnettogehalt" in "monatliches Nettogehalt=Jahresnettogehalt/12"
- Klick auf Variable öffnet die referenzierte Berechnungsvorschrift zum Bearbeiten (Bootstrap Modal)
- Beispiel: "monatliches Nettogehalt=Jahresnettogehalt/12" → "Jahresnettogehalt" ist anklickbar
- **Für jede Berechnungsvorschrift werden zwei Listen angezeigt**:
  - **"Wird verwendet in"**: Liste aller Berechnungsvorschriften, die diese Berechnungsvorschrift referenzieren (anklickbar)
  - **"Verwendet folgende Berechnungsvorschriften"**: Liste aller Berechnungsvorschriften, die im Pseudocode dieser Berechnungsvorschrift vorkommen (anklickbar)
- Diese Listen bieten eine übersichtliche Navigation und zeigen die Abhängigkeiten zwischen Berechnungsvorschriften
- Verwendung von Bootstrap-Komponenten für moderne, responsive UI: Forms, Cards, Tables, Modals, Buttons, Badges, Input Groups, List Groups

## API-Endpunkte

### Berechnungsvorschriften

- `POST /api/berechnungsvorschriften` - Neue Berechnungsvorschrift erstellen (mit Zelleneingabe-Daten)
- `GET /api/berechnungsvorschriften` - Alle Vorschriften (JSON)
- `GET /api/berechnungsvorschriften/{id}` - Vorschrift abrufen (JSON)
- `GET /api/berechnungsvorschriften/{id}/verwendet-in` - Liste aller Berechnungsvorschriften, die diese Vorschrift referenzieren
- `GET /api/berechnungsvorschriften/{id}/verwendet` - Liste aller Berechnungsvorschriften, die im Pseudocode dieser Vorschrift vorkommen
- `PUT /api/berechnungsvorschriften/{id}` - Vorschrift bearbeiten (JSON)
- `DELETE /api/berechnungsvorschriften/{id}` - Vorschrift löschen (nur wenn keine Referenzen existieren)
- `POST /api/berechnungsvorschriften/{id}/generieren` - Neu generieren mit LLM

### Suche über Metadaten

- `GET /api/berechnungsvorschriften/suche?name={name}` - Nach Name suchen
- `GET /api/berechnungsvorschriften/suche?kategorie={kategorie}` - Nach Kategorie suchen
- `GET /api/berechnungsvorschriften/suche?symbol={symbol}` - Nach Symbol suchen
- `GET /api/berechnungsvorschriften/suche?datentyp={datentyp}` - Nach Datentyp suchen
- `GET /api/berechnungsvorschriften/suche?einheit={einheit}` - Nach Einheit suchen
- `GET /api/berechnungsvorschriften/suche?name={name}&kategorie={kategorie}&...` - Kombinierte Suche über mehrere Metadaten-Felder

## Docker-Setup

### Services:

1. **frontend**: Nginx-Container für statische Frontend-Dateien (Port 80)
2. **middleware**: FastAPI-Anwendung als Middleware (Port 8000)
3. **fuseki**: Apache Jena Fuseki (Port 3030)

### Docker Compose Konfiguration:

```yaml
version: '3.8'

services:
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - middleware
    restart: unless-stopped

  middleware:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FUSEKI_URL=http://fuseki:3030
      - FUSEKI_DATASET=berechnungsvorschriften
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - fuseki
    restart: unless-stopped

  fuseki:
    image: apache/jena-fuseki:latest
    ports:
      - "3030:3030"
    volumes:
      - ./fuseki-data:/fuseki/databases
      - ./fuseki-config.ttl:/fuseki/config.ttl:ro
    environment:
      - FUSEKI_DEFAULT=berechnungsvorschriften
    restart: unless-stopped
```

### Volumes:

- `./backend` → `/app` (Middleware Code, Hot-Reload für Entwicklung)
- `./frontend` → `/usr/share/nginx/html` (Statische Frontend-Dateien)
- `./fuseki-data` → `/fuseki/databases` (Persistente RDF-Daten)
- `./fuseki-config.ttl` → `/fuseki/config.ttl` (Fuseki Konfiguration)

### Netzwerk:

- Alle Services sind im gleichen Docker-Netzwerk
- Frontend kommuniziert mit Middleware über `http://middleware:8000`
- Middleware kommuniziert mit Fuseki über `http://fuseki:3030`
- Externe Zugriffe:
  - Frontend: `http://localhost`
  - Middleware API: `http://localhost:8000`
  - Fuseki Admin: `http://localhost:3030`

### Umgebungsvariablen:

- `.env` Datei für lokale Konfiguration:
  ```
  OPENAI_API_KEY=sk-...
  FUSEKI_DATASET=berechnungsvorschriften
  ```

## Implementierungsschritte

1. **Docker Setup**: docker-compose.yml, Dockerfiles, Nginx-Konfiguration, Fuseki-Konfiguration
2. **Grundstruktur**: Projektordner, Requirements
3. **JSON-Modelle**: Pydantic Models für Zelleneingabe (Input) und Berechnungsvorschrift (mit Variablen und Metadaten)
4. **LLM-Service**: OpenAI GPT-5-nano Integration für strukturierte Berechnungsvorschrift-Generierung - Prompt-Datei (mit Anweisungen zur Excel-Formel-Umwandlung und Pseudocode-Regeln) und Beispiel-Text-Datei (mit Beispieleingabe und gewünschtem JSON) für Few-Shot Learning
5. **Berechnungsvorschrift-Matcher**: Programmatische Prüfung auf bestehende Berechnungsvorschriften (Tabellenidentifikator+Tabellenblatt+Zellenidentifikator ODER Beschreibung), Verlinkung von Variablen, Prüfung auf zirkuläre Abhängigkeiten
6. **Versionierung**: Versionsverwaltung für Berechnungsvorschriften (jede Änderung erstellt neue Version)
7. **JSON-zu-RDF Converter**: Middleware zur Konvertierung von JSON zu RDF-Triples (nur Berechnungsvorschriften, mit Versionsinformationen)
8. **RDF-Service**: Jena Fuseki Client mit SPARQL-Operationen und Metadaten-Indizierung für Suche
9. **API-Routes**: REST-Endpunkte für Berechnungsvorschriften (CRUD mit Versionsverwaltung), Metadaten-Suche, Abhängigkeitsabfragen (verwendet-in, verwendet), Löschen mit Referenz-Prüfung
9. **Frontend**: HTML/JS mit Bootstrap 5 für Eingabe (Zellendaten) und strukturierte Anzeige - Verwendung von Bootstrap-Komponenten (Forms, Cards, Tables, Modals, Buttons)
10. **Variable-Verlinkung**: Klickbare Variablen im Frontend (Bootstrap Badges/Links), die zu referenzierten Berechnungsvorschriften führen
11. **Abhängigkeitslisten**: UI-Anzeige für jede Berechnungsvorschrift: "Wird verwendet in" und "Verwendet folgende Berechnungsvorschriften" (Bootstrap List Groups)
12. **Metadaten-Suche**: Suchfunktion im Frontend über Metadaten-Filter (Bootstrap Form Controls) - Name, Kategorie, Symbol, Datentyp, Einheit

## Todos

1. Docker Compose Setup: docker-compose.yml mit Frontend (Nginx), Middleware (FastAPI) und Fuseki Services, Dockerfiles, Nginx- und Fuseki-Konfiguration
2. Python Backend-Grundstruktur: FastAPI App, Requirements, Models (Berechnungsvorschrift mit Variablen und Metadaten, Zelleneingabe nur als Input-Modell)
3. RDF-Service implementieren: JSON-zu-RDF Konverter (Middleware), SPARQL Client für Jena Fuseki, CRUD-Operationen
4. LLM-Service implementieren: OpenAI GPT-5-nano Integration, Prompt-Datei (mit Excel-Formel-Umwandlungsregeln und Pseudocode-Anforderungen) und Beispiel-Text-Datei (mit Beispieleingabe und gewünschtem JSON) erstellen, Formel-Analyse, strukturierte Berechnungsvorschrift-Generierung mit Few-Shot Learning
5. Berechnungsvorschrift-Matcher implementieren: Programmatische Prüfung auf bestehende Berechnungsvorschriften (Tabellenidentifikator+Tabellenblatt+Zellenidentifikator ODER Beschreibung), Verlinkung von Variablen, Prüfung auf zirkuläre Abhängigkeiten, UI für mehrere Treffer
6. Versionierung implementieren: Versionsverwaltung für Berechnungsvorschriften (jede Änderung erstellt neue Version)
7. API-Routes: Berechnungsvorschriften-Endpunkte mit LLM-Integration, Metadaten-Suche und Versionsverwaltung
8. API-Routes: Suchfunktion für Berechnungsvorschriften über Metadaten (Name, Kategorie, Symbol, Datentyp, Einheit)
9. API-Routes: Löschen mit Referenz-Prüfung (verhindert Löschen wenn referenziert)
10. Frontend: Eingabeformular für Zellendaten (Bootstrap Forms) - Tabellenidentifikator, Tabellenblatt, Zellenidentifikator, Beschreibung, Formel - erzeugt direkt Berechnungsvorschrift
11. Frontend: Anzeige der Berechnungsvorschriften mit Bootstrap Cards/Tables und anklickbaren Variablen-Referenzen (Bootstrap Badges/Links) - zu anderen Berechnungsvorschriften
12. Frontend: Abhängigkeitslisten für jede Berechnungsvorschrift - "Wird verwendet in" und "Verwendet folgende Berechnungsvorschriften" (Bootstrap List Groups)
13. Frontend: UI für mehrere Matching-Treffer (Auswahl-Dialog wenn mehrere passende Berechnungsvorschriften gefunden werden)
14. Frontend: Berechnungsvorschrift-Editor (Bootstrap Modals/Forms) zum Bearbeiten von Vorschriften und Metadaten, mit manueller Korrektur bei LLM-Fehlern
15. Frontend: Versionsanzeige und Versionsverwaltung für Berechnungsvorschriften
16. Frontend: Suchfunktion für Berechnungsvorschriften über Metadaten-Filter (Bootstrap Form Controls, Input Groups)

## Entscheidungen / Anforderungen

### Matching-Strategie für bestehende Berechnungsvorschriften
- **Kriterien**: Tabellenidentifikator, Tabellenblatt und Zellenidentifikator müssen identisch sein **ODER** die Beschreibung ist identisch
- **Bei mehreren Treffern**: Benutzer wird gefragt (nicht automatisch verlinken) - UI zeigt alle passenden Optionen zur Auswahl
- **Implementierung**: `berechnungsvorschrift_matcher.py` prüft beide Bedingungen (Quelle-Information ODER Beschreibung)

### Zirkuläre Abhängigkeiten
- **Behandlung**: Verhindern - System erkennt zirkuläre Referenzen und verhindert deren Erstellung (Warnung/Fehler)
- **Implementierung**: Prüfung beim Erstellen/Bearbeiten von Berechnungsvorschriften

### Excel-Funktionen
- **Unterstützung**: Alle Excel-Funktionen (generische Umwandlung)
- **Implementierung**: LLM wandelt alle Funktionen in einfachen Pseudocode um, keine explizite Liste erforderlich

### Fehlerbehandlung bei LLM-Output
- **Strategie**: Manuelle Korrektur durch Benutzer ermöglichen
- **Implementierung**: Ungültiger Output wird gespeichert, Benutzer kann im Editor korrigieren (kein automatischer Retry)

### Validierung
- **Umfang**: Keine Validierung (nur grundlegende Typ-Prüfung durch Pydantic Models)
- **Implementierung**: Pydantic Models prüfen nur Datentypen, keine Geschäftslogik-Validierung

### Authentifizierung
- **Status**: Keine Authentifizierung - öffentlicher Zugriff
- **Implementierung**: Keine Auth-Middleware erforderlich

### Versionierung
- **Status**: Ja, Versionierung wird implementiert
- **Implementierung**: Jede Änderung erstellt neue Version, alte Versionen bleiben erhalten (RDF-basiert mit Versionsnummer/Timestamp)

### Löschen-Verhalten
- **Strategie**: Löschen verhindern, wenn Berechnungsvorschrift von anderen referenziert wird
- **Implementierung**: Prüfung vor DELETE-Operation, Fehlermeldung wenn Referenzen existieren

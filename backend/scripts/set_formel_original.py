#!/usr/bin/env python3
"""
Einmal-Skript: Setzt formel_original für eine bestehende Berechnungsvorschrift.
Verwendung: Aus Projekt-Root mit laufendem Docker:
  docker compose exec middleware python scripts/set_formel_original.py

Oder lokal (FUSEKI_URL=http://localhost:3030 erforderlich):
  cd backend && python scripts/set_formel_original.py
"""
import sys
from pathlib import Path

# Backend-Verzeichnis für Imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rdf_service import RDFService


BV_ID = "cad15b12-1a60-4272-978c-caeb953d0677"
FORMEL_ORIGINAL = "=IFS(_1_Wert>=J26,K26,_1_Wert>J27,L27*_1_Wert+M27,_1_Wert>=J28,L28*_1_Wert+M28,_1_Wert<J29,K29)"


def main():
    rdf_service = RDFService()
    bv = rdf_service.lade_berechnungsvorschrift(BV_ID)
    if not bv:
        print(f"Fehler: Berechnungsvorschrift {BV_ID} nicht gefunden.")
        sys.exit(1)

    bv.formel_original = FORMEL_ORIGINAL
    rdf_service.speichere_berechnungsvorschrift(bv)
    print(f"formel_original erfolgreich gesetzt für {BV_ID}: {bv.name}")


if __name__ == "__main__":
    main()

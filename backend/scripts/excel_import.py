#!/usr/bin/env python3
"""
Halb-automatisierter Excel-Import für Berechnungsvorschriften.

Liest eine Excel-Datei gemäß YAML-Config, extrahiert Formelzellen aus den
konfigurierten Tabellenbereichen und erzeugt Zelleneingaben. Diese können
als Dry-Run (JSON/CSV) ausgegeben oder per API importiert werden.

Verwendung:
  # Dry-Run (Vorschau, keine API-Aufrufe):
  python scripts/excel_import.py --config config/excel_import_config.yaml --excel datei.xlsx

  # Import (API-Aufrufe):
  python scripts/excel_import.py --config config/excel_import_config.yaml --excel datei.xlsx --import

  # API-URL (Standard: http://localhost:8000):
  API_URL=http://localhost:8000 python scripts/excel_import.py ...
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Backend-Verzeichnis für Imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_range(bereich: str) -> tuple:
    """
    Parst Bereich wie 'A5:F16' in (min_row, min_col, max_row, max_col).
    openpyxl verwendet 1-basierte Indizes.
    """
    try:
        min_col, min_row, max_col, max_row = range_boundaries(bereich)
        return min_row, min_col, max_row, max_col
    except Exception:
        raise ValueError(f"Ungültiger Bereich: {bereich}")


def zelle_zu_ref(row: int, col: int) -> str:
    """Wandelt (row, col) in Excel-Referenz um (z.B. D7)."""
    return f"{get_column_letter(col)}{row}"


def beschreibung_aus_zellen_ermitteln(
    ws,
    formel_row: int,
    formel_col: int,
    min_row: int,
    min_col: int,
    config: dict,
) -> str:
    """
    Ermittelt die Beschreibung aus konfigurierten Zellen relativ zum Tabellenbereich.
    config: beschreibung_aus_zellen mit erste_spalte_gleiche_zeile, gleiche_spalte_erste_n_zeilen, trennzeichen
    """
    teile = []
    trennzeichen = config.get("trennzeichen", " – ")

    # gleiche_spalte_erste_n_zeilen: Werte aus gleicher Spalte, erste n Zeilen
    n_zeilen = config.get("gleiche_spalte_erste_n_zeilen", 0)
    if n_zeilen and n_zeilen > 0:
        for r in range(min_row, min(min_row + n_zeilen, formel_row)):
            cell = ws.cell(row=r, column=formel_col)
            val = cell.value
            if val is not None and str(val).strip():
                teile.append(str(val).strip())

    # erste_spalte_gleiche_zeile: Wert aus erster Spalte, gleiche Zeile
    if config.get("erste_spalte_gleiche_zeile") and formel_col > min_col:
        cell = ws.cell(row=formel_row, column=min_col)
        val = cell.value
        if val is not None and str(val).strip():
            teile.append(str(val).strip())

    return trennzeichen.join(teile) if teile else ""


def beschreibung_ermitteln(
    ws, cell, formel_row: int, formel_col: int, min_row: int, min_col: int, tabelle_config: dict
) -> str:
    """Ermittelt die Beschreibung gemäß beschreibung_quelle der Tabelle."""
    quelle = tabelle_config.get("beschreibung_quelle", "formel")

    if quelle == "zellen":
        aus_zellen = tabelle_config.get("beschreibung_aus_zellen", {})
        if aus_zellen:
            return beschreibung_aus_zellen_ermitteln(
                ws, formel_row, formel_col, min_row, min_col, aus_zellen
            )

    if quelle == "kommentar":
        if hasattr(cell, "comment") and cell.comment:
            return (cell.comment.text or "").strip().replace("\n", " ")

    if quelle == "links" and formel_col > 1:
        left_cell = ws.cell(row=formel_row, column=formel_col - 1)
        if left_cell.value is not None:
            return str(left_cell.value).strip()

    if quelle == "oben" and formel_row > 1:
        top_cell = ws.cell(row=formel_row - 1, column=formel_col)
        if top_cell.value is not None:
            return str(top_cell.value).strip()

    # Fallback: formel oder leere Beschreibung (formel als Hinweis)
    if quelle == "formel":
        formel = cell.value or ""
        return str(formel).strip()[:200]  # Begrenzen für Lesbarkeit

    return ""


def zelleneingaben_aus_excel(config_path: str, excel_path: str) -> list:
    """
    Liest die Config und Excel-Datei und erzeugt eine Liste von Zelleneingabe-Dicts.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    excel_datei_config = config.get("excel_datei")
    # Übersteuern, falls expliziter Pfad angegeben
    pfad = excel_path or excel_datei_config
    if not pfad or not Path(pfad).exists():
        raise FileNotFoundError(f"Excel-Datei nicht gefunden: {pfad}")

    wb = load_workbook(pfad, read_only=False, data_only=False)
    zelleneingaben = []

    for blatt in config.get("tabellenblaetter", []):
        blatt_name = blatt.get("name")
        if not blatt_name:
            logger.warning("Tabellenblatt ohne Namen übersprungen")
            continue

        ws = wb[blatt_name] if blatt_name in wb.sheetnames else None
        if not ws:
            logger.warning(f"Tabellenblatt '{blatt_name}' nicht gefunden, übersprungen")
            continue

        for tabelle in blatt.get("tabellen", []):
            t_id = tabelle.get("id", "Tabelle1")
            bereich = tabelle.get("bereich")
            wichtige_zellen = set(tabelle.get("wichtige_zellen") or [])

            if not bereich:
                logger.warning(f"Tabelle {t_id} ohne Bereich übersprungen")
                continue

            try:
                min_row, min_col, max_row, max_col = parse_range(bereich)
            except ValueError as e:
                logger.warning(f"Tabelle {t_id}: {e}")
                continue

            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    cell = ws.cell(row=row, column=col)
                    val = cell.value
                    if not val or not str(val).strip().startswith("="):
                        continue
                    formel = str(val).strip()
                    zellen_ref = zelle_zu_ref(row, col)
                    beschreibung = beschreibung_ermitteln(
                        ws, cell, row, col, min_row, min_col, tabelle
                    )
                    wichtig = zellen_ref in wichtige_zellen

                    ze = {
                        "tabellenidentifikator": t_id,
                        "tabellenblatt": blatt_name,
                        "zellenidentifikator": zellen_ref,
                        "beschreibung": beschreibung or formel[:50],
                        "formel": formel,
                        "wichtig": wichtig,
                    }
                    zelleneingaben.append(ze)
                    logger.debug(f"Zelleneingabe: {zellen_ref} ({t_id}, {blatt_name})")

    wb.close()
    return zelleneingaben


def dry_run(zelleneingaben: list, output_json: bool = True) -> None:
    """Gibt Zelleneingaben als JSON oder CSV zur Prüfung aus."""
    if output_json:
        print(json.dumps(zelleneingaben, indent=2, ensure_ascii=False))
    else:
        if not zelleneingaben:
            print("Keine Zelleneingaben")
            return
        headers = list(zelleneingaben[0].keys())
        print(",".join(headers))
        for ze in zelleneingaben:
            print(",".join(str(ze.get(h, "")).replace(",", ";") for h in headers))


def importiere_per_api(zelleneingaben: list, api_url: str) -> None:
    """Sendet jede Zelleneingabe per POST an die API."""
    import urllib.request
    import urllib.error

    base = api_url.rstrip("/")
    endpoint = f"{base}/api/berechnungsvorschriften"
    erstellt = 0
    fehler = 0

    for i, ze in enumerate(zelleneingaben):
        payload = json.dumps({"zelleneingabe": ze}).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if 200 <= resp.getcode() < 300:
                    erstellt += 1
                    logger.info(f"({i + 1}/{len(zelleneingaben)}) Erstellt: {ze['zellenidentifikator']} ({ze['tabellenblatt']})")
                else:
                    fehler += 1
                    logger.warning(f"({i + 1}/{len(zelleneingaben)}) HTTP {resp.getcode()}: {ze['zellenidentifikator']}")
        except urllib.error.HTTPError as e:
            fehler += 1
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            logger.error(f"({i + 1}/{len(zelleneingaben)}) Fehler {ze['zellenidentifikator']}: {e.code} {body[:200]}")
        except Exception as e:
            fehler += 1
            logger.error(f"({i + 1}/{len(zelleneingaben)}) Fehler {ze['zellenidentifikator']}: {e}")

    logger.info(f"Import abgeschlossen: {erstellt} erstellt, {fehler} Fehler")


def main():
    parser = argparse.ArgumentParser(description="Excel-Import für Berechnungsvorschriften")
    parser.add_argument("--config", "-c", required=True, help="Pfad zur YAML-Config")
    parser.add_argument("--excel", "-e", default=None, help="Pfad zur Excel-Datei (überschreibt Config)")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Import per API ausführen")
    parser.add_argument("--csv", action="store_true", help="Dry-Run als CSV statt JSON")
    parser.add_argument("--api-url", default=None, help="API-Basis-URL (default: API_URL oder localhost:8000)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent.parent / config_path
    if not config_path.exists():
        logger.error(f"Config nicht gefunden: {config_path}")
        sys.exit(1)

    excel_path = args.excel
    if excel_path and not Path(excel_path).is_absolute():
        # Relativ zum Projekt-Root oder CWD
        excel_path = str(Path(excel_path).resolve())

    try:
        zelleneingaben = zelleneingaben_aus_excel(str(config_path), excel_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fehler beim Lesen: {e}")
        sys.exit(1)

    logger.info(f"{len(zelleneingaben)} Zelleneingaben extrahiert")

    if args.do_import:
        api_url = args.api_url or os.environ.get("API_URL", "http://localhost:8000")
        importiere_per_api(zelleneingaben, api_url)
    else:
        dry_run(zelleneingaben, output_json=not args.csv)


if __name__ == "__main__":
    main()

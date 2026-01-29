"""
Pydantic Models für Berechnungsvorschrift
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class Variable(BaseModel):
    """
    Eine Variable in einer Berechnungsvorschrift.
    Jede Wertquelle, die in die Formel einfließt, wird als Variable abgebildet:
    - Zellreferenz (z.B. A9) oder Tabellenspalte (z.B. MAJahr1[Arbeitsstunden/ Jahr]) → je eine Variable.
    Semantisch ist jede Variable ein Verweis auf eine Berechnungsvorschrift bzw. Eingabe:
    - Mit referenz_berechnungsvorschrift_id: Verweis auf eine konkrete BV (ist_primitive=False).
    - Ohne Referenz (ist_primitive=True): impliziter Verweis auf einen Wert/Eingabe (Zelle oder Spalte);
      keine eigene BV-Entität erforderlich.
    Der name muss exakt mit dem Variablennamen im formel-String übereinstimmen (Verlinkbarkeit, Auswertung).
    """
    
    name: str = Field(..., description="Gut lesbarer Variablenname; muss im formel-String vorkommen")
    referenz_berechnungsvorschrift_id: Optional[str] = Field(
        None, 
        description="ID der referenzierten Berechnungsvorschrift (optional; wird vom Matcher gesetzt)"
    )
    ist_primitive: bool = Field(
        True, 
        description="True wenn keine Referenz zu einer anderen Berechnungsvorschrift (einfacher Wert)"
    )


class Metadaten(BaseModel):
    """Metadaten einer Berechnungsvorschrift"""
    
    kategorie: str = Field(..., description="Kategorie der Berechnungsvorschrift")
    symbol: str = Field(..., description="Symbol/Kürzel")
    datentyp: str = Field(..., description="Datentyp (z.B. 'decimal', 'integer', 'string')")
    einheit: str = Field(..., description="Einheit (z.B. 'EUR', 'kg', 'm')")


class Quelle(BaseModel):
    """Quelle-Information zur ursprünglichen Zelle (optional, für Matching)"""
    
    tabellenidentifikator: Optional[str] = Field(None, description="Tabellenidentifikator")
    tabellenblatt: Optional[str] = Field(None, description="Tabellenblatt")
    zellenidentifikator: Optional[str] = Field(None, description="Zellenidentifikator")
    beschreibung: Optional[str] = Field(None, description="Beschreibung")


class Berechnungsvorschrift(BaseModel):
    """Strukturierte Berechnungsvorschrift"""
    
    id: Optional[str] = Field(None, description="UUID der Berechnungsvorschrift")
    name: str = Field(..., description="Name der Berechnungsvorschrift")
    formel: str = Field(
        ..., 
        description="Menschenlesbarer Pseudocode (keine Excel-Syntax, keine Kommentare)"
    )
    variablen: List[Variable] = Field(default_factory=list, description="Liste der Variablen")
    metadaten: Metadaten = Field(..., description="Metadaten")
    quelle: Optional[Quelle] = Field(None, description="Quelle-Information zur ursprünglichen Zelle")
    version: int = Field(1, description="Versionsnummer")
    erstellt_am: Optional[datetime] = Field(None, description="Erstellungszeitpunkt")
    geaendert_am: Optional[datetime] = Field(None, description="Letzte Änderung")
    # Optional: Auswertungstyp für spätere Berechnung mit echten Werten
    operation: Optional[str] = Field(
        None,
        description="Auswertungstyp: 'ausdruck' (Default) = Formel als Ausdruck; 'index_lookup' = 2D-Tabellenlookup (Tabelle, Zeilenkey, Spaltenkey)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid",
                "name": "monatliches Nettogehalt",
                "formel": "Jahresnettogehalt/12",
                "variablen": [
                    {
                        "name": "Jahresnettogehalt",
                        "referenz_berechnungsvorschrift_id": "uuid-xyz",
                        "ist_primitive": False
                    }
                ],
                "metadaten": {
                    "kategorie": "Gehalt",
                    "symbol": "MNG",
                    "datentyp": "decimal",
                    "einheit": "EUR"
                },
                "quelle": {
                    "tabellenidentifikator": "Tabelle1",
                    "tabellenblatt": "Sheet1",
                    "zellenidentifikator": "A1",
                    "beschreibung": "Gesamtkosten berechnen"
                },
                "version": 1,
                "erstellt_am": "2026-01-23T10:00:00Z",
                "geaendert_am": "2026-01-23T10:00:00Z"
            }
        }


class BerechnungsvorschriftErstellen(BaseModel):
    """Request-Model zum Erstellen einer neuen Berechnungsvorschrift"""
    
    zelleneingabe: "Zelleneingabe" = Field(..., description="Zelleneingabe-Daten")
    
    class Config:
        from_attributes = True


class BerechnungsvorschriftCreateResponse(Berechnungsvorschrift):
    """
    Response-Model für POST /api/berechnungsvorschriften.
    Enthält die erstellte Berechnungsvorschrift plus optionale Zusatzinfos:
    - aktualisierte_verlinkungen: BVs, die durch Rückwärts-Verlinkung aktualisiert wurden
    - mehrere_treffer: Variablen mit mehreren Match-Optionen (Benutzer muss wählen)
    """
    aktualisierte_verlinkungen: Optional[List[dict]] = Field(
        None,
        description="Liste von {bv_id, name} – BVs, die durch Rückwärts-Verlinkung aktualisiert wurden"
    )
    mehrere_treffer: Optional[List[dict]] = Field(
        None,
        description="Liste von {variablenname, optionen} – Variablen mit mehreren Treffern zur Auswahl"
    )


# Forward reference auflösen
from .zelleneingabe import Zelleneingabe
BerechnungsvorschriftErstellen.model_rebuild()

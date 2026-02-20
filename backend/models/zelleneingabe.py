"""
Pydantic Model für Zelleneingabe (nur Input, wird nicht gespeichert)
"""
from typing import Optional
from pydantic import BaseModel, Field


class Zelleneingabe(BaseModel):
    """Model für die Eingabe von Zellendaten - wird nicht in der Datenbank gespeichert"""
    
    tabellenidentifikator: str = Field(..., description="Identifikator der Tabelle (z.B. 'Tabelle1')")
    tabellenblatt: str = Field(..., description="Name des Tabellenblatts (z.B. 'Sheet1')")
    zellenidentifikator: str = Field(..., description="Zellenidentifikator (z.B. 'A1', 'B5') - für Matching erforderlich")
    beschreibung: str = Field(..., description="Beschreibung der Zelle - Alternative für Matching (wird unverändert übernommen)")
    formel: str = Field(..., description="Excel-Formel (z.B. '=A1+B1*C1')")
    # Optional: Wenn Nutzer Kategorie eingibt, wird sie verwendet; sonst erzeugt das LLM sie.
    kategorie: Optional[str] = Field(None, description="Kategorie (optional) – wenn gesetzt, wird LLM angewiesen diese zu nutzen; sonst LLM generiert")
    # Optional: Excel-Identifikator der Zelle (z.B. _1_Wert) – aus Excel, nicht aus der Datenbank.
    excel_identifikator: Optional[str] = Field(
        None,
        description="Excel-Identifikator der Zelle (optional, z.B. _1_Wert). Stammt aus Excel."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tabellenidentifikator": "Tabelle1",
                "tabellenblatt": "Sheet1",
                "zellenidentifikator": "A1",
                "beschreibung": "Gesamtkosten berechnen",
                "formel": "=A1+B1*C1"
            }
        }

"""
Pydantic Model für Zelleneingabe (nur Input, wird nicht gespeichert)
"""
from pydantic import BaseModel, Field


class Zelleneingabe(BaseModel):
    """Model für die Eingabe von Zellendaten - wird nicht in der Datenbank gespeichert"""
    
    tabellenidentifikator: str = Field(..., description="Identifikator der Tabelle (z.B. 'Tabelle1')")
    tabellenblatt: str = Field(..., description="Name des Tabellenblatts (z.B. 'Sheet1')")
    zellenidentifikator: str = Field(..., description="Zellenidentifikator (z.B. 'A1', 'B5') - für Matching erforderlich")
    beschreibung: str = Field(..., description="Beschreibung der Zelle - Alternative für Matching")
    formel: str = Field(..., description="Excel-Formel (z.B. '=A1+B1*C1')")
    
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

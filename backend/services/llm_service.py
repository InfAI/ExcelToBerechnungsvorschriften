"""
LLM-Service für die Generierung von Berechnungsvorschriften mit OpenAI GPT-5-nano
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from openai import OpenAI
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.zelleneingabe import Zelleneingabe
from models.berechnungsvorschrift import Berechnungsvorschrift, Metadaten, Variable

logger = logging.getLogger(__name__)


class LLMService:
    """Service für die LLM-basierte Generierung von Berechnungsvorschriften"""
    
    def __init__(self):
        """Initialisiert den LLM-Service"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY Umgebungsvariable nicht gesetzt")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-nano"
        logger.info(f"LLMService initialisiert: {self.model}")
        
        # Prompt und Beispiel laden
        self.prompt_path = Path(__file__).parent.parent / "prompts" / "berechnungsvorschrift_prompt.txt"
        self.beispiel_path = Path(__file__).parent.parent / "prompts" / "berechnungsvorschrift_beispiel.txt"
        self.prompt = self._load_prompt()
        self.beispiel_text = self._load_beispiel()
    
    def _load_prompt(self) -> str:
        """Lädt den Prompt aus der Datei"""
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt-Datei nicht gefunden: {self.prompt_path}")
            raise FileNotFoundError(f"Prompt-Datei nicht gefunden: {self.prompt_path}")
    
    def _load_beispiel(self) -> str:
        """Lädt das Beispiel aus der Text-Datei"""
        try:
            with open(self.beispiel_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Beispiel-Datei nicht gefunden: {self.beispiel_path}")
            raise FileNotFoundError(f"Beispiel-Datei nicht gefunden: {self.beispiel_path}")
    
    def generiere_berechnungsvorschrift(self, zelleneingabe: Zelleneingabe) -> Berechnungsvorschrift:
        """
        Generiert eine Berechnungsvorschrift aus Zelleneingabe-Daten
        
        Args:
            zelleneingabe: Zelleneingabe-Daten
            
        Returns:
            Generierte Berechnungsvorschrift
        """
        logger.info(f"Generiere Berechnungsvorschrift: {zelleneingabe.zellenidentifikator} ({zelleneingabe.beschreibung or 'ohne Beschreibung'})")
        
        # System-Prompt erstellen
        system_prompt = self.prompt
        
        # User-Prompt mit Zellendaten erstellen
        # Hinweis: Beschreibung wird unverändert übernommen (quelle.beschreibung).
        # Kategorie: Nur angeben, wenn Nutzer sie eingegeben hat; sonst LLM generiert.
        kategorie_hinweis = (
            f"\nKategorie (vom Nutzer vorgegeben): {zelleneingabe.kategorie}\n"
            "→ Verwende diese Kategorie in metadaten.kategorie."
            if getattr(zelleneingabe, "kategorie", None) and str(zelleneingabe.kategorie).strip()
            else ""
        )
        user_prompt = f"""Bitte wandle folgende Excel-Zelle in eine Berechnungsvorschrift um:

Tabellenidentifikator: {zelleneingabe.tabellenidentifikator}
Tabellenblatt: {zelleneingabe.tabellenblatt}
Zellenidentifikator: {zelleneingabe.zellenidentifikator}
Beschreibung: {zelleneingabe.beschreibung}
Formel: {zelleneingabe.formel}
{kategorie_hinweis}

Beispiel für das gewünschte Format:
{self.beispiel_text}

Bitte generiere die Berechnungsvorschrift im JSON-Format wie im Beispiel gezeigt."""
        
        try:
            logger.debug(f"Sende Request an OpenAI API ({self.model})")
            # LLM-Request
            # Hinweis: GPT-5-nano unterstützt keine benutzerdefinierte Temperatur, daher wird der Standardwert (1) verwendet
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}  # JSON-Format erzwingen
            )
            
            # Antwort parsen
            content = response.choices[0].message.content
            berechnungsvorschrift_dict = json.loads(content)
            logger.debug(
                f"LLM-Response: {len(content)} Zeichen, "
                f"geparst: Name={berechnungsvorschrift_dict.get('name')}, "
                f"{len(berechnungsvorschrift_dict.get('variablen', []))} Variablen"
            )
            
            # In Berechnungsvorschrift-Model konvertieren
            berechnungsvorschrift = self._dict_to_berechnungsvorschrift(
                berechnungsvorschrift_dict,
                zelleneingabe
            )
            
            logger.info(f"Berechnungsvorschrift generiert: {berechnungsvorschrift.name} ({len(berechnungsvorschrift.variablen)} Variablen)")
            return berechnungsvorschrift
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM hat ungültiges JSON zurückgegeben: {e}")
            raise ValueError(f"LLM hat ungültiges JSON zurückgegeben: {e}")
        except Exception as e:
            logger.error(f"Fehler bei LLM-Generierung: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Fehler bei LLM-Generierung: {e}")
    
    def _dict_to_berechnungsvorschrift(
        self, 
        data: Dict[str, Any], 
        zelleneingabe: Zelleneingabe
    ) -> Berechnungsvorschrift:
        """Konvertiert ein Dictionary in ein Berechnungsvorschrift-Model"""
        from datetime import datetime
        
        # Variablen konvertieren (inkl. zellenidentifikator, tabellenblatt_referenz für Matching)
        variablen = [
            Variable(
                name=var["name"],
                referenz_berechnungsvorschrift_id=None,  # Wird später vom Matcher gesetzt
                ist_primitive=var.get("ist_primitive", True),
                zellenidentifikator=var.get("zellenidentifikator"),  # D7, A9 etc. – für Matching
                tabellenblatt_referenz=var.get("tabellenblatt_referenz")  # Fremd-Blatt bei Cross-Sheet-Referenzen
            )
            for var in data.get("variablen", [])
        ]
        
        # Metadaten konvertieren
        metadaten = Metadaten(**data["metadaten"])
        # Wenn Nutzer Kategorie eingegeben hat, diese verwenden (LLM-Ausgabe überschreiben)
        if getattr(zelleneingabe, "kategorie", None) and str(zelleneingabe.kategorie).strip():
            metadaten.kategorie = zelleneingabe.kategorie.strip()
        
        # Quelle-Information erstellen
        from models.berechnungsvorschrift import Quelle
        quelle = Quelle(
            tabellenidentifikator=zelleneingabe.tabellenidentifikator,
            tabellenblatt=zelleneingabe.tabellenblatt,
            zellenidentifikator=zelleneingabe.zellenidentifikator,
            beschreibung=zelleneingabe.beschreibung
        )
        
        # Operation (optional) – z.B. "index_lookup" bei INDEX/MATCH; für Auswertung mit echten Werten
        operation = data.get("operation")
        
        # Name: Immer die vom Benutzer im UI eingegebene Beschreibung verwenden.
        # Das LLM muss den Namen nicht mehr erzeugen – spart Tokens und gibt dem Nutzer Kontrolle.
        name = (zelleneingabe.beschreibung or "").strip() or data.get("name", "")
        
        # Excel-Identifikator aus Zelleneingabe übernehmen (stammt aus Excel, nicht aus der Datenbank)
        excel_identifikator = None
        if getattr(zelleneingabe, "excel_identifikator", None) and str(zelleneingabe.excel_identifikator).strip():
            excel_identifikator = zelleneingabe.excel_identifikator.strip()
        
        # Berechnungsvorschrift erstellen.
        # formel_original: originale Excel-Formel aus der Eingabe – nur zur Information, nicht bearbeitbar
        berechnungsvorschrift = Berechnungsvorschrift(
            name=name,
            formel=data["formel"],
            formel_original=zelleneingabe.formel,
            variablen=variablen,
            metadaten=metadaten,
            quelle=quelle,
            version=1,
            erstellt_am=datetime.now(),
            geaendert_am=datetime.now(),
            operation=operation,
            excel_identifikator=excel_identifikator
        )
        
        return berechnungsvorschrift

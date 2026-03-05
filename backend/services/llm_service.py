"""
LLM-Service für die Generierung von Berechnungsvorschriften mit OpenAI gpt-4o-mini
"""
import os
import re
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
from utils.formel_utils import zellreferenzen_aus_formel, tabellenspalten_aus_formel

logger = logging.getLogger(__name__)


class LLMService:
    """Service für die LLM-basierte Generierung von Berechnungsvorschriften"""
    
    def __init__(self):
        """Initialisiert den LLM-Service"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY Umgebungsvariable nicht gesetzt")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        # Niedrige Temperatur für konsistentere Extraktion von Zellreferenzen und Variablen
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        logger.info(f"LLMService initialisiert: {self.model} (Temperatur: {self.temperature})")
        
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
        # Vorab-Extraktion: Zellreferenzen und Tabellenspalten als Hinweis für das LLM
        zellref_hinweis = ""
        tabellen_hinweis = ""
        try:
            zellrefs = zellreferenzen_aus_formel(zelleneingabe.formel)
            if zellrefs:
                zellref_hinweis = "\n\nWICHTIG – Zellreferenzen (müssen als Variable mit zellenidentifikator/tabellenblatt_referenz, Namensschema Blatt_Zelle):\n"
                for r in zellrefs:
                    blatt_info = f" (Blatt: {r['blatt']})" if r.get("blatt") else " (gleiches Blatt)"
                    # Vorschlag: Blatt_Zelle (z.B. Intern_Bezüge_D3 für INTERN BEZÜGE!D3)
                    vorschlag = ""
                    if r.get("blatt"):
                        blatt_safe = r["blatt"].replace(" ", "_").replace("'", "")
                        vorschlag = f" → z.B. {blatt_safe}_{r['zelle']}"
                    zellref_hinweis += f"  - {r['zelle']}{blatt_info}{vorschlag}\n"
        except Exception as e:
            logger.debug(f"Zellreferenz-Extraktion fehlgeschlagen (wird ignoriert): {e}")
        try:
            tabellen = tabellenspalten_aus_formel(zelleneingabe.formel)
            if tabellen:
                # Bei COUNTIFS/SUMIFS: Tabellenspalten sind KEINE Variablen (Kriterienbereiche).
                # Nur Kriterienzellen (Zellreferenzen) = Variablen. Tabellen dienen der Filterlogik.
                tabellen_hinweis = "\n\nHINWEIS – Tabellenspalten in Formel (bei COUNTIFS/SUMIFS KEINE Variablen, nur Kriterienzellen):\n"
                tabellen_namen = sorted(set(t["tabelle"] for t in tabellen))
                tabellen_hinweis += f"  Tabellen: {', '.join(tabellen_namen)}\n"
                for t in tabellen:
                    tabellen_hinweis += f"  - {t['tabelle']}[{t['spalte']}] (Kriterienbereich, keine Variable)\n"
        except Exception as e:
            logger.debug(f"Tabellenspalten-Extraktion fehlgeschlagen (wird ignoriert): {e}")
        # Aufgelöste Tabellenspalten aus Excel (referenz_bereiche) als Hinweis
        referenz_hinweis = ""
        if getattr(zelleneingabe, "referenz_bereiche", None) and zelleneingabe.referenz_bereiche:
            referenz_hinweis = "\n\nAufgelöste Tabellenspalten (Blatt+Bereich aus Excel):\n"
            for rb in zelleneingabe.referenz_bereiche:
                ref_str = f"  {rb.get('tabelle', '?')}[{rb.get('spalte', '?')}]"
                if rb.get("blatt"):
                    ref_str += f" = '{rb['blatt']}'!{rb.get('bereich', '?')}"
                referenz_hinweis += ref_str + "\n"
        user_prompt = f"""Bitte wandle folgende Excel-Zelle in eine Berechnungsvorschrift um:

Tabellenidentifikator: {zelleneingabe.tabellenidentifikator}
Tabellenblatt: {zelleneingabe.tabellenblatt}
Zellenidentifikator: {zelleneingabe.zellenidentifikator}
Beschreibung: {zelleneingabe.beschreibung}
Formel: {zelleneingabe.formel}
{kategorie_hinweis}{zellref_hinweis}{tabellen_hinweis}{referenz_hinweis}

Beispiel für das gewünschte Format:
{self.beispiel_text}

Bitte generiere die Berechnungsvorschrift im JSON-Format wie im Beispiel gezeigt."""
        
        try:
            logger.debug(f"Sende Request an OpenAI API ({self.model}, Temperatur: {self.temperature})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
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
        
        # Variablen konvertieren (inkl. zellenidentifikator, tabellenblatt_referenz, erweiterte Felder)
        variablen = [
            Variable(
                name=var["name"],
                referenz_berechnungsvorschrift_id=None,  # Wird später vom Matcher gesetzt
                ist_primitive=var.get("ist_primitive", True),
                zellenidentifikator=var.get("zellenidentifikator"),
                tabellenblatt_referenz=var.get("tabellenblatt_referenz"),
                quelle_typ=var.get("quelle_typ"),
                kriterienbereich=var.get("kriterienbereich"),
                vergleichsoperator=var.get("vergleichsoperator"),
                tabellenreferenz=var.get("tabellenreferenz"),
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
        
        # Operation (optional) – z.B. "index_lookup" bei INDEX/MATCH, "count_filter" bei COUNTIFS
        operation = data.get("operation")
        operation_parameter = data.get("operation_parameter")
        
        # Name: Immer die vom Benutzer im UI eingegebene Beschreibung verwenden.
        # Das LLM muss den Namen nicht mehr erzeugen – spart Tokens und gibt dem Nutzer Kontrolle.
        name = (zelleneingabe.beschreibung or "").strip() or data.get("name", "")
        
        # Excel-Identifikator aus Zelleneingabe übernehmen (stammt aus Excel, nicht aus der Datenbank)
        excel_identifikator = None
        if getattr(zelleneingabe, "excel_identifikator", None) and str(zelleneingabe.excel_identifikator).strip():
            excel_identifikator = zelleneingabe.excel_identifikator.strip()
        
        # Wichtig-Flag (z.B. aus Excel-Import-Config) – nur übergeben wenn gesetzt
        wichtig = getattr(zelleneingabe, "wichtig", None) if hasattr(zelleneingabe, "wichtig") else None
        bv_kwargs = {}
        if wichtig is True:
            bv_kwargs["wichtig"] = True
        
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
            operation_parameter=operation_parameter,
            excel_identifikator=excel_identifikator,
            **bv_kwargs
        )
        
        # Post-Processing: referenz_bereiche nutzen für kriterienbereich_blatt/bereich und tabellen_bereiche
        if getattr(zelleneingabe, "referenz_bereiche", None) and zelleneingabe.referenz_bereiche:
            berechnungsvorschrift = self._anreichern_aus_referenz_bereichen(
                berechnungsvorschrift, zelleneingabe.referenz_bereiche
            )
        
        return berechnungsvorschrift
    
    def _anreichern_aus_referenz_bereichen(
        self, bv: Berechnungsvorschrift, referenz_bereiche: list
    ) -> Berechnungsvorschrift:
        """
        Reichert BV mit aufgelösten Bereichen aus referenz_bereiche an.
        - Variable.kriterienbereich_blatt, kriterienbereich_bereich: aus erstem passenden Eintrag
        - operation_parameter.tabellen_bereiche: pro Tabelle Blatt+Bereich (erster Spalteneintrag)
        """
        ref_by_spalte = {}  # spalte -> [{"tabelle", "spalte", "blatt", "bereich"}, ...]
        ref_by_tabelle = {}  # tabelle -> {"blatt", "bereich"} (erster Eintrag)
        for rb in referenz_bereiche:
            spalte = rb.get("spalte")
            tabelle = rb.get("tabelle")
            if spalte:
                ref_by_spalte.setdefault(spalte, []).append(rb)
            if tabelle and "blatt" in rb and "bereich" in rb and tabelle not in ref_by_tabelle:
                ref_by_tabelle[tabelle] = {"blatt": rb["blatt"], "bereich": rb["bereich"]}
        
        # Variablen: kriterienbereich_blatt, kriterienbereich_bereich
        for var in bv.variablen:
            kb = var.kriterienbereich
            if kb and kb in ref_by_spalte and ref_by_spalte[kb]:
                first = ref_by_spalte[kb][0]
                var.kriterienbereich_blatt = first.get("blatt")
                var.kriterienbereich_bereich = first.get("bereich")
        
        # operation_parameter.tabellen_bereiche
        if bv.operation_parameter and "tabellen" in bv.operation_parameter:
            tabellen_bereiche = {}
            for t in bv.operation_parameter["tabellen"]:
                if t in ref_by_tabelle:
                    tabellen_bereiche[t] = ref_by_tabelle[t]
            if tabellen_bereiche:
                bv.operation_parameter = dict(bv.operation_parameter)
                bv.operation_parameter["tabellen_bereiche"] = tabellen_bereiche
        
        return bv

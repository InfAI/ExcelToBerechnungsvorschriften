"""
API-Routes für Berechnungsvorschriften
"""
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

from models.zelleneingabe import Zelleneingabe
from models.berechnungsvorschrift import Berechnungsvorschrift, BerechnungsvorschriftErstellen
from services.llm_service import LLMService
from services.rdf_service import RDFService
from services.berechnungsvorschrift_matcher import BerechnungsvorschriftMatcher
from services.versionierung_service import VersionierungService

router = APIRouter()

# Services initialisieren
rdf_service = RDFService()
llm_service = LLMService()
matcher = BerechnungsvorschriftMatcher(rdf_service)
versionierung = VersionierungService(rdf_service)


@router.post("", response_model=Berechnungsvorschrift, status_code=201)
async def erstelle_berechnungsvorschrift(request: BerechnungsvorschriftErstellen) -> Berechnungsvorschrift:
    """
    Erstellt eine neue Berechnungsvorschrift aus Zelleneingabe-Daten
    
    - Generiert Berechnungsvorschrift mit LLM
    - Verlinkt Variablen zu bestehenden Berechnungsvorschriften
    - Speichert in Fuseki
    """
    logger.info(f"Erstelle neue Berechnungsvorschrift aus Zelleneingabe: "
                f"Tabellenidentifikator={request.zelleneingabe.tabellenidentifikator}, "
                f"Tabellenblatt={request.zelleneingabe.tabellenblatt}, "
                f"Zellenidentifikator={request.zelleneingabe.zellenidentifikator}")
    try:
        # LLM generiert Berechnungsvorschrift
        logger.debug("Generiere Berechnungsvorschrift mit LLM...")
        berechnungsvorschrift = llm_service.generiere_berechnungsvorschrift(request.zelleneingabe)
        logger.info(f"LLM hat Berechnungsvorschrift generiert: Name={berechnungsvorschrift.name}, "
                   f"Variablen={len(berechnungsvorschrift.variablen)}")
        
        # ID generieren
        berechnungsvorschrift.id = str(uuid.uuid4())
        logger.debug(f"Generierte ID für Berechnungsvorschrift: {berechnungsvorschrift.id}")
        
        # Variablen verlinken
        logger.debug("Verlinke Variablen zu bestehenden Berechnungsvorschriften...")
        berechnungsvorschrift, mehrere_treffer = matcher.verlinke_variablen(berechnungsvorschrift)
        if mehrere_treffer:
            logger.info(f"Mehrere Treffer gefunden für {len(mehrere_treffer)} Variablen")
        
        # Prüfe auf zirkuläre Abhängigkeiten
        for var in berechnungsvorschrift.variablen:
            if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
                if matcher.pruefe_zirkulaere_abhaengigkeiten(
                    berechnungsvorschrift,
                    var.referenz_berechnungsvorschrift_id
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Zirkuläre Abhängigkeit erkannt: Variable '{var.name}' würde eine zirkuläre Referenz erzeugen"
                    )
        
        # Speichern
        logger.debug(f"Speichere Berechnungsvorschrift {berechnungsvorschrift.id} in Fuseki...")
        rdf_service.speichere_berechnungsvorschrift(berechnungsvorschrift)
        logger.info(f"Berechnungsvorschrift {berechnungsvorschrift.id} erfolgreich gespeichert")
        
        # Wenn mehrere Treffer vorhanden sind, diese in der Response mitgeben
        if mehrere_treffer:
            # Erweiterte Response mit Matching-Informationen
            response_data = berechnungsvorschrift.model_dump()
            response_data["mehrere_treffer"] = [
                {
                    "variablenname": var_name,
                    "optionen": [{"id": bv.id, "name": bv.name, "symbol": bv.metadaten.symbol} for bv in optionen]
                }
                for var_name, optionen in mehrere_treffer
            ]
            return Berechnungsvorschrift(**response_data)
        
        return berechnungsvorschrift
        
    except ValueError as e:
        logger.warning(f"Validierungsfehler bei Erstellung: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Fehler bei Erstellung der Berechnungsvorschrift: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler bei Erstellung: {str(e)}")


@router.get("", response_model=List[Berechnungsvorschrift])
async def liste_berechnungsvorschriften() -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück"""
    logger.info("Lade alle Berechnungsvorschriften...")
    try:
        berechnungsvorschriften = rdf_service.lade_alle_berechnungsvorschriften()
        logger.info(f"Gefunden: {len(berechnungsvorschriften)} Berechnungsvorschrift(en)")
        return berechnungsvorschriften
    except Exception as e:
        logger.error(f"Fehler beim Laden aller Berechnungsvorschriften: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


@router.get("/{bv_id}", response_model=Berechnungsvorschrift)
async def hole_berechnungsvorschrift(bv_id: str) -> Berechnungsvorschrift:
    """Gibt eine spezifische Berechnungsvorschrift zurück"""
    logger.info(f"Lade Berechnungsvorschrift: ID={bv_id}")
    bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich geladen")
    return bv


@router.get("/{bv_id}/verwendet-in", response_model=List[Berechnungsvorschrift])
async def hole_verwendet_in(bv_id: str) -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück, die diese Berechnungsvorschrift referenzieren"""
    try:
        return rdf_service.finde_verwendet_in(bv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


@router.get("/{bv_id}/verwendet", response_model=List[Berechnungsvorschrift])
async def hole_verwendet(bv_id: str) -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück, die im Pseudocode dieser Berechnungsvorschrift vorkommen"""
    try:
        return rdf_service.finde_verwendet(bv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


@router.put("/{bv_id}", response_model=Berechnungsvorschrift)
async def aktualisiere_berechnungsvorschrift(
    bv_id: str,
    berechnungsvorschrift: Berechnungsvorschrift
) -> Berechnungsvorschrift:
    """
    Aktualisiert eine Berechnungsvorschrift (erstellt neue Version)
    """
    logger.info(f"Aktualisiere Berechnungsvorschrift: ID={bv_id}, Name={berechnungsvorschrift.name}")
    # Alte Version laden
    logger.debug(f"Lade alte Version von {bv_id}...")
    alte_bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not alte_bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für Update")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    logger.debug(f"Alte Version geladen: Version {alte_bv.version}")
    # Prüfe auf zirkuläre Abhängigkeiten
    for var in berechnungsvorschrift.variablen:
        if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
            if matcher.pruefe_zirkulaere_abhaengigkeiten(
                berechnungsvorschrift,
                var.referenz_berechnungsvorschrift_id
            ):
                logger.warning(f"Zirkuläre Abhängigkeit erkannt bei Update von {bv_id}: Variable '{var.name}'")
                raise HTTPException(
                    status_code=400,
                    detail=f"Zirkuläre Abhängigkeit erkannt: Variable '{var.name}' würde eine zirkuläre Referenz erzeugen"
                )
    
    # Neue Version erstellen
    logger.debug(f"Erstelle neue Version für {bv_id}...")
    neue_version = versionierung.erstelle_neue_version(alte_bv, berechnungsvorschrift)
    neue_version.id = bv_id  # ID beibehalten
    
    # Speichern (überschreibt alte Version)
    logger.debug(f"Speichere neue Version {neue_version.version} von {bv_id}...")
    rdf_service.speichere_berechnungsvorschrift(neue_version)
    logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich aktualisiert (Version {neue_version.version})")
    
    return neue_version


@router.delete("/{bv_id}", status_code=204)
async def loesche_berechnungsvorschrift(bv_id: str):
    """
    Löscht eine Berechnungsvorschrift (nur wenn keine Referenzen existieren)
    """
    logger.info(f"Lösche Berechnungsvorschrift: ID={bv_id}")
    # Prüfe auf Referenzen
    logger.debug(f"Prüfe Referenzen für {bv_id}...")
    if rdf_service.hat_referenzen(bv_id):
        referenzen = rdf_service.finde_verwendet_in(bv_id)
        logger.warning(f"Löschen von {bv_id} verhindert: {len(referenzen)} Referenz(en) gefunden")
        raise HTTPException(
            status_code=400,
            detail="Berechnungsvorschrift kann nicht gelöscht werden, da sie von anderen Berechnungsvorschriften referenziert wird"
        )
    
    # Löschen
    logger.debug(f"Keine Referenzen gefunden - lösche {bv_id}...")
    try:
        rdf_service.loesche_berechnungsvorschrift(bv_id)
        logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich gelöscht")
    except Exception as e:
        logger.error(f"Fehler beim Löschen von {bv_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen: {str(e)}")


@router.post("/{bv_id}/generieren", response_model=Berechnungsvorschrift)
async def regeneriere_berechnungsvorschrift(
    bv_id: str,
    zelleneingabe: Zelleneingabe
) -> Berechnungsvorschrift:
    """
    Regeneriert eine Berechnungsvorschrift mit LLM
    """
    logger.info(f"Generiere Berechnungsvorschrift erneut: ID={bv_id}")
    # Alte Version laden
    logger.debug(f"Lade alte Version von {bv_id}...")
    alte_bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not alte_bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für erneute Generierung")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    logger.debug(f"Generiere neue Version mit LLM für {bv_id}...")
    # Neue Berechnungsvorschrift generieren
    neue_bv = llm_service.generiere_berechnungsvorschrift(zelleneingabe)
    neue_bv.id = bv_id
    
    # Variablen verlinken
    logger.debug(f"Verlinke Variablen für neue Version von {bv_id}...")
    neue_bv, mehrere_treffer = matcher.verlinke_variablen(neue_bv)
    
    # Prüfe auf zirkuläre Abhängigkeiten
    for var in neue_bv.variablen:
        if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
            if matcher.pruefe_zirkulaere_abhaengigkeiten(
                neue_bv,
                var.referenz_berechnungsvorschrift_id
            ):
                logger.warning(f"Zirkuläre Abhängigkeit erkannt bei Regenerierung von {bv_id}: Variable '{var.name}'")
                raise HTTPException(
                    status_code=400,
                    detail=f"Zirkuläre Abhängigkeit erkannt: Variable '{var.name}' würde eine zirkuläre Referenz erzeugen"
                )
    
    # Neue Version erstellen
    logger.debug(f"Erstelle Version-Objekt für {bv_id}...")
    neue_version = versionierung.erstelle_neue_version(alte_bv, neue_bv)
    
    # Speichern
    logger.debug(f"Speichere neu generierte Version von {bv_id}...")
    rdf_service.speichere_berechnungsvorschrift(neue_version)
    logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich neu generiert (Version {neue_version.version})")
    
    return neue_version


@router.post("/{bv_id}/variablen/{variablenname}/verlinken")
async def verlinke_variable_manuell(
    bv_id: str,
    variablenname: str,
    referenz_id: str = Query(..., description="ID der referenzierten Berechnungsvorschrift")
) -> Berechnungsvorschrift:
    """
    Verlinkt eine Variable manuell zu einer spezifischen Berechnungsvorschrift
    (wird verwendet wenn mehrere Treffer gefunden wurden)
    """
    logger.info(f"Manuelle Verlinkung: Berechnungsvorschrift={bv_id}, Variable={variablenname}, Referenz={referenz_id}")
    logger.debug(f"Lade Berechnungsvorschrift {bv_id} für manuelle Verlinkung...")
    bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für manuelle Verlinkung")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    # Prüfe auf zirkuläre Abhängigkeiten
    logger.debug(f"Prüfe zirkuläre Abhängigkeiten für {bv_id} -> {referenz_id}...")
    if matcher.pruefe_zirkulaere_abhaengigkeiten(bv, referenz_id):
        logger.warning(f"Zirkuläre Abhängigkeit erkannt: {bv_id} -> {referenz_id}")
        raise HTTPException(
            status_code=400,
            detail="Zirkuläre Abhängigkeit erkannt: Diese Verlinkung würde eine zirkuläre Referenz erzeugen"
        )
    
    # Variable verlinken
    logger.debug(f"Verlinke Variable '{variablenname}' in {bv_id} zu {referenz_id}...")
    bv = matcher.verlinke_variable_manuell(bv, variablenname, referenz_id)
    
    # Speichern
    logger.debug(f"Speichere aktualisierte Berechnungsvorschrift {bv_id}...")
    rdf_service.speichere_berechnungsvorschrift(bv)
    logger.info(f"Variable '{variablenname}' in {bv_id} erfolgreich manuell verlinkt zu {referenz_id}")
    
    return bv


@router.get("/suche", response_model=List[Berechnungsvorschrift])
async def suche_berechnungsvorschriften(
    name: Optional[str] = Query(None, description="Nach Name suchen"),
    kategorie: Optional[str] = Query(None, description="Nach Kategorie suchen"),
    symbol: Optional[str] = Query(None, description="Nach Symbol suchen"),
    datentyp: Optional[str] = Query(None, description="Nach Datentyp suchen"),
    einheit: Optional[str] = Query(None, description="Nach Einheit suchen")
) -> List[Berechnungsvorschrift]:
    """
    Sucht Berechnungsvorschriften über Metadaten
    """
    try:
        return rdf_service.suche_nach_metadaten(
            name=name,
            kategorie=kategorie,
            symbol=symbol,
            datentyp=datentyp,
            einheit=einheit
        )
    except Exception as e:
        logger.error(f"Fehler bei Suche: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler bei Suche: {str(e)}")

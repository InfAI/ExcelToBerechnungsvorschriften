"""
API-Routes für Berechnungsvorschriften
"""
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

from models.zelleneingabe import Zelleneingabe
from models.berechnungsvorschrift import Berechnungsvorschrift, BerechnungsvorschriftErstellen, BerechnungsvorschriftCreateResponse
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


@router.post("", response_model=BerechnungsvorschriftCreateResponse, status_code=201)
async def erstelle_berechnungsvorschrift(request: BerechnungsvorschriftErstellen) -> BerechnungsvorschriftCreateResponse:
    """
    Erstellt eine neue Berechnungsvorschrift aus Zelleneingabe-Daten.
    Wenn bereits eine BV mit gleicher Kombination (Tabellenidentifikator, Tabellenblatt,
    Zellenidentifikator) existiert, wird diese aktualisiert statt neu erstellt.

    - Generiert Berechnungsvorschrift mit LLM
    - Verlinkt Variablen zu bestehenden Berechnungsvorschriften
    - Speichert in Fuseki
    """
    ze = request.zelleneingabe
    logger.info(f"Erstelle Berechnungsvorschrift: {ze.zellenidentifikator} ({ze.tabellenblatt})")
    try:
        # Prüfen, ob bereits eine BV mit gleicher Quelle existiert (Tabellen-ID + Blatt + Zelle)
        vorhandene = rdf_service.suche_nach_quelle(
            tabellenidentifikator=ze.tabellenidentifikator,
            tabellenblatt=ze.tabellenblatt,
            zellenidentifikator=ze.zellenidentifikator
        )
        ist_update = bool(vorhandene)

        # LLM generiert Berechnungsvorschrift
        berechnungsvorschrift = llm_service.generiere_berechnungsvorschrift(ze)

        # Wichtig-Flag aus Zelleneingabe übernehmen (z.B. aus Excel-Import Config wichtige_zellen)
        if getattr(ze, "wichtig", None) is True:
            berechnungsvorschrift.wichtig = True

        if ist_update:
            # Bestehende BV aktualisieren: ID übernehmen, Version erhöhen
            alte_bv = vorhandene[0]
            berechnungsvorschrift.id = alte_bv.id
            logger.info(f"Aktualisiere vorhandene Berechnungsvorschrift {alte_bv.id} (statt neu erstellen)")
        else:
            # Neue BV: ID generieren
            berechnungsvorschrift.id = str(uuid.uuid4())

        logger.debug(f"Variablen verlinken für {berechnungsvorschrift.id}")
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

        # Bei Update: Versionierung (neue Version mit geaendert_am, version++)
        if ist_update:
            berechnungsvorschrift = versionierung.erstelle_neue_version(vorhandene[0], berechnungsvorschrift)

        # Speichern
        rdf_service.speichere_berechnungsvorschrift(berechnungsvorschrift)
        logger.info(f"Berechnungsvorschrift {berechnungsvorschrift.id} {'aktualisiert' if ist_update else 'erstellt'}")
        
        # Rückwärts-Verlinkung: Andere BVs, die eine Variable haben, die jetzt auf diese BV verlinkt werden kann
        aktualisierte_verlinkungen = []
        try:
            bvs_mit_passender_var = matcher.finde_bvs_mit_passender_variable(berechnungsvorschrift)
            for andere_bv, variablenname in bvs_mit_passender_var:
                if matcher.pruefe_zirkulaere_abhaengigkeiten(andere_bv, berechnungsvorschrift.id):
                    logger.warning(f"Rückwärts-Verlinkung übersprungen (Zirkularität): {andere_bv.id} -> {berechnungsvorschrift.id}")
                    continue
                andere_bv = matcher.verlinke_variable_manuell(andere_bv, variablenname, berechnungsvorschrift.id)
                # Rückwärts-Verlinkung ist eine Änderung: geaendert_am aktualisieren
                andere_bv.geaendert_am = datetime.now()
                rdf_service.speichere_berechnungsvorschrift(andere_bv)
                aktualisierte_verlinkungen.append({"bv_id": andere_bv.id, "name": andere_bv.name})
                logger.info(f"Rückwärts-Verlinkung: BV {andere_bv.id} Variable '{variablenname}' -> {berechnungsvorschrift.id}")
        except Exception as e:
            logger.warning(f"Rückwärts-Verlinkung fehlgeschlagen (wird ignoriert): {e}")
        
        # Response mit optionalen Zusatzinfos (Rückwärts-Verlinkungen, mehrere Treffer)
        response_data = berechnungsvorschrift.model_dump()
        response_data["aktualisierte_verlinkungen"] = aktualisierte_verlinkungen
        response_data["mehrere_treffer"] = [
            {
                "variablenname": var_name,
                "optionen": [{"id": bv.id, "name": bv.name, "symbol": bv.metadaten.symbol} for bv in optionen]
            }
            for var_name, optionen in mehrere_treffer
        ]
        return BerechnungsvorschriftCreateResponse(**response_data)
        
    except ValueError as e:
        logger.warning(f"Validierungsfehler bei Erstellung: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Fehler bei Erstellung der Berechnungsvorschrift: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler bei Erstellung: {str(e)}")


@router.get("", response_model=List[Berechnungsvorschrift])
async def liste_berechnungsvorschriften() -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück"""
    logger.info("Liste alle Berechnungsvorschriften")
    try:
        berechnungsvorschriften = rdf_service.lade_alle_berechnungsvorschriften()
        logger.debug(f"Liste: {len(berechnungsvorschriften)} Berechnungsvorschriften")
        return berechnungsvorschriften
    except Exception as e:
        logger.error(f"Fehler beim Laden aller Berechnungsvorschriften: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


@router.get("/{bv_id}", response_model=Berechnungsvorschrift)
async def hole_berechnungsvorschrift(bv_id: str) -> Berechnungsvorschrift:
    """Gibt eine spezifische Berechnungsvorschrift zurück"""
    logger.info(f"Hole Berechnungsvorschrift: {bv_id}")
    bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    return bv


@router.get("/{bv_id}/verwendet-in", response_model=List[Berechnungsvorschrift])
async def hole_verwendet_in(bv_id: str) -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück, die diese Berechnungsvorschrift referenzieren"""
    logger.info(f"Hole 'verwendet in' für: {bv_id}")
    try:
        return rdf_service.finde_verwendet_in(bv_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


@router.get("/{bv_id}/verwendet", response_model=List[Berechnungsvorschrift])
async def hole_verwendet(bv_id: str) -> List[Berechnungsvorschrift]:
    """Gibt alle Berechnungsvorschriften zurück, die im Pseudocode dieser Berechnungsvorschrift vorkommen"""
    logger.info(f"Hole 'verwendet' für: {bv_id}")
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
    logger.info(f"Aktualisiere Berechnungsvorschrift: {bv_id}")
    # Alte Version laden
    alte_bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not alte_bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für Update")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
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
    neue_version = versionierung.erstelle_neue_version(alte_bv, berechnungsvorschrift)
    neue_version.id = bv_id  # ID beibehalten
    
    rdf_service.speichere_berechnungsvorschrift(neue_version)
    logger.info(f"Berechnungsvorschrift {bv_id} aktualisiert (Version {neue_version.version})")
    
    return neue_version


@router.delete("/blatt", status_code=200)
async def loesche_berechnungsvorschriften_nach_blatt(
    tabellenidentifikator: str = Query(..., description="Tabellenidentifikator des Blatts"),
    tabellenblatt: str = Query(..., description="Name des Tabellenblatts")
):
    """
    Löscht alle Berechnungsvorschriften für ein Tabellenblatt (Tabellenidentifikator + Tabellenblatt).
    BVs werden in abhängigkeitsrelevanter Reihenfolge gelöscht (zuerst solche ohne Referenzen).
    BVs, die von anderen Blättern referenziert werden, können nicht gelöscht werden.
    """
    logger.info(f"Lösche alle BVs für Blatt: {tabellenidentifikator} / {tabellenblatt}")
    bvs = rdf_service.suche_nach_tabellenblatt(tabellenidentifikator, tabellenblatt)
    if not bvs:
        return {"geloescht": 0, "nicht_loeschbar": [], "meldung": "Keine Berechnungsvorschriften für dieses Blatt gefunden."}

    ids_im_blatt = {bv.id for bv in bvs}
    geloescht = 0
    nicht_loeschbar = []

    while bvs:
        # Finde eine BV, die von niemandem (mehr) referenziert wird – Referencer zuerst löschen
        ids_noch_drin = {b.id for b in bvs}
        gefunden = None
        for bv in bvs:
            referenzen = rdf_service.finde_verwendet_in(bv.id)
            # Löschbar nur wenn keine andere noch zu löschende BV diese referenziert
            ref_noch_drin = [r for r in referenzen if r.id in ids_noch_drin]
            if not ref_noch_drin:
                gefunden = bv
                break

        if not gefunden:
            # Keine weitere BV kann gelöscht werden – Rest hat Referenzen von außerhalb des Blatts
            for bv in bvs:
                nicht_loeschbar.append({"id": bv.id, "name": bv.name})
            break

        # Sicherheitsprüfung: Keine Referenzen von außerhalb des Blatts
        if rdf_service.hat_referenzen(gefunden.id):
            nicht_loeschbar.append({"id": gefunden.id, "name": gefunden.name})
            bvs = [b for b in bvs if b.id != gefunden.id]
            continue

        try:
            rdf_service.loesche_berechnungsvorschrift(gefunden.id)
            geloescht += 1
            ids_im_blatt.discard(gefunden.id)
            bvs = [b for b in bvs if b.id != gefunden.id]
        except Exception as e:
            logger.warning(f"Löschen von {gefunden.id} fehlgeschlagen: {e}")
            nicht_loeschbar.append({"id": gefunden.id, "name": gefunden.name})
            bvs = [b for b in bvs if b.id != gefunden.id]

    return {
        "geloescht": geloescht,
        "nicht_loeschbar": nicht_loeschbar,
        "meldung": f"{geloescht} Berechnungsvorschrift(en) gelöscht."
        + (f" {len(nicht_loeschbar)} konnten nicht gelöscht werden (externe Referenzen)." if nicht_loeschbar else "")
    }


@router.delete("/{bv_id}", status_code=204)
async def loesche_berechnungsvorschrift(bv_id: str):
    """
    Löscht eine Berechnungsvorschrift (nur wenn keine Referenzen existieren)
    """
    logger.info(f"Lösche Berechnungsvorschrift: {bv_id}")
    if rdf_service.hat_referenzen(bv_id):
        referenzen = rdf_service.finde_verwendet_in(bv_id)
        logger.warning(f"Löschen von {bv_id} verhindert: {len(referenzen)} Referenz(en) gefunden")
        raise HTTPException(
            status_code=400,
            detail="Berechnungsvorschrift kann nicht gelöscht werden, da sie von anderen Berechnungsvorschriften referenziert wird"
        )
    
    try:
        rdf_service.loesche_berechnungsvorschrift(bv_id)
        logger.info(f"Berechnungsvorschrift {bv_id} gelöscht")
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
    logger.info(f"Regeneriere Berechnungsvorschrift: {bv_id}")
    alte_bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not alte_bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für Regenerierung")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    neue_bv = llm_service.generiere_berechnungsvorschrift(zelleneingabe)
    neue_bv.id = bv_id
    
    logger.debug(f"Verlinke Variablen für {bv_id}")
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
    
    neue_version = versionierung.erstelle_neue_version(alte_bv, neue_bv)
    rdf_service.speichere_berechnungsvorschrift(neue_version)
    logger.info(f"Berechnungsvorschrift {bv_id} regeneriert (Version {neue_version.version})")
    
    return neue_version


@router.post("/{bv_id}/variablen/{variablenname}/verlinkung-aufheben", response_model=Berechnungsvorschrift)
async def verlinkung_aufheben(bv_id: str, variablenname: str) -> Berechnungsvorschrift:
    """
    Hebt die Verlinkung einer Variable auf (Variable wird wieder primitiv / ohne Referenz).
    """
    logger.info(f"Verlinkung aufheben: {bv_id} / {variablenname}")
    bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    bv = matcher.verlinkung_aufheben(bv, variablenname)
    bv.geaendert_am = datetime.now()
    rdf_service.speichere_berechnungsvorschrift(bv)
    logger.debug(f"Verlinkung aufgehoben: {variablenname} in {bv_id}")
    return bv


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
    logger.info(f"Manuelle Verlinkung: {bv_id} / {variablenname} -> {referenz_id}")
    bv = rdf_service.lade_berechnungsvorschrift(bv_id)
    if not bv:
        logger.warning(f"Berechnungsvorschrift {bv_id} nicht gefunden für manuelle Verlinkung")
        raise HTTPException(status_code=404, detail="Berechnungsvorschrift nicht gefunden")
    
    if matcher.pruefe_zirkulaere_abhaengigkeiten(bv, referenz_id):
        logger.warning(f"Zirkuläre Abhängigkeit erkannt: {bv_id} -> {referenz_id}")
        raise HTTPException(
            status_code=400,
            detail="Zirkuläre Abhängigkeit erkannt: Diese Verlinkung würde eine zirkuläre Referenz erzeugen"
        )
    
    bv = matcher.verlinke_variable_manuell(bv, variablenname, referenz_id)
    bv.geaendert_am = datetime.now()
    rdf_service.speichere_berechnungsvorschrift(bv)
    logger.debug(f"Variable {variablenname} in {bv_id} -> {referenz_id}")
    
    return bv


@router.get("/suche", response_model=List[Berechnungsvorschrift])
async def suche_berechnungsvorschriften(
    name: Optional[str] = Query(None, description="Nach Name suchen"),
    kategorie: Optional[str] = Query(None, description="Nach Kategorie suchen"),
    symbol: Optional[str] = Query(None, description="Nach Symbol suchen"),
    datentyp: Optional[str] = Query(None, description="Nach Datentyp suchen"),
    einheit: Optional[str] = Query(None, description="Nach Einheit suchen"),
    wichtig: Optional[bool] = Query(None, description="Nur wichtige BVs (true = Filter aktiv)")
) -> List[Berechnungsvorschrift]:
    """
    Sucht Berechnungsvorschriften über Metadaten
    """
    logger.info(f"Suche: name={name}, kategorie={kategorie}, symbol={symbol}, wichtig={wichtig}")
    try:
        return rdf_service.suche_nach_metadaten(
            name=name,
            kategorie=kategorie,
            symbol=symbol,
            datentyp=datentyp,
            einheit=einheit,
            wichtig=wichtig
        )
    except Exception as e:
        logger.error(f"Fehler bei Suche: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler bei Suche: {str(e)}")

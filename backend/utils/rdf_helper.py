"""
RDF-Helper-Funktionen für URI-Generierung und SPARQL-Templates
"""
import os
from rdflib import URIRef, Namespace
from rdflib.namespace import RDF as RDF_NS, RDFS as RDFS_NS, XSD as XSD_NS
from typing import Optional
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Namespace aus Umgebungsvariable laden
RDF_NAMESPACE = os.getenv("RDF_NAMESPACE", "http://example.org/berechnungsvorschrift/")
# Sicherstellen, dass Namespace mit / endet
if not RDF_NAMESPACE.endswith("/"):
    RDF_NAMESPACE = RDF_NAMESPACE + "/"

# Namespace-Definitionen
BV = Namespace(RDF_NAMESPACE)
RDF = RDF_NS
RDFS = RDFS_NS
XSD = XSD_NS


def berechnungsvorschrift_uri(bv_id: str) -> URIRef:
    """Erstellt eine URI für eine Berechnungsvorschrift"""
    return URIRef(f"{RDF_NAMESPACE}berechnungsvorschrift/{bv_id}")


def variable_uri(bv_id: str, var_name: str) -> URIRef:
    """Erstellt eine URI für eine Variable"""
    # Variablenname für URI sicher machen
    safe_name = var_name.replace(" ", "_").replace("/", "_").replace("=", "_").replace("+", "_").replace("-", "_")
    return URIRef(f"{RDF_NAMESPACE}berechnungsvorschrift/{bv_id}/variable/{safe_name}")


def get_base_namespace() -> Namespace:
    """Gibt das Basis-Namespace zurück"""
    return BV


def get_namespace_iri() -> str:
    """Gibt den Namespace IRI als String zurück"""
    return RDF_NAMESPACE


def property_uri(property_name: str) -> URIRef:
    """Erstellt eine URI für eine Property (z.B. hatName, hatFormel)"""
    return URIRef(f"{RDF_NAMESPACE}{property_name}")

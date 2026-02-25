# Diagramme (Graphviz DOT)

Die Flussdiagramme liegen als DOT-Quelldateien vor und können mit Graphviz gerendert werden.

## Rendering

```bash
./render.sh
```

Voraussetzung: [Graphviz](https://graphviz.org/) muss installiert sein (z.B. `apt install graphviz` oder `brew install graphviz`).

## Dateien

| DOT (Quelle) | PNG (gerendert) | Verwendung in |
|--------------|-----------------|---------------|
| `erzeugung_ablauf.dot` | `erzeugung_ablauf.png` | 03_wartung.md |
| `versionierung_workflow.dot` | `versionierung_workflow.png` | 02_versionierungskonzept.md |
| `wartung_workflow.dot` | `wartung_workflow.png` | 03_wartung.md |
| `abhaendigkeiten.dot` | `abhaendigkeiten.png` | 01_definition.md |
| `transfer_ablauf.dot` | `transfer_ablauf.png` | 03_wartung.md |
| `formel_syntax.dot` | `formel_syntax.png` | 01_definition.md (Zwei-Ebenen-Modell) |
| `zusammenfuehrung_ablauf.dot` | `zusammenfuehrung_ablauf.png` | 05_zusammenfuehrung.md |

Die PNG-Dateien sind Platzhalter, bis `render.sh` mit installiertem Graphviz ausgeführt wird.

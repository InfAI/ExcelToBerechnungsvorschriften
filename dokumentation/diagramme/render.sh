#!/bin/bash
# Rendert alle DOT-Dateien zu PNG.
# Voraussetzung: Graphviz installiert (z.B. apt install graphviz, brew install graphviz)
cd "$(dirname "$0")"
for f in *.dot; do
  dot -Tpng "$f" -o "${f%.dot}.png" && echo "Gerendert: ${f%.dot}.png"
done

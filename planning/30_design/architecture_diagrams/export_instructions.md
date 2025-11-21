# Diagram Export Instructions

Use PlantUML CLI or any compatible renderer to export `.puml` sources to PNG/SVG before reviews/decks.

Example command (requires `plantuml` on PATH):
```
plantuml delivery_a_sequence.puml delivery_b_components.puml delivery_c_integration.puml
```
Outputs appear as `.png` alongside the sources. Check them into `planning/30_design/architecture_diagrams/` with suffix `*.png` if desired, or share via deck attachments.

If PlantUML is unavailable locally, use the PlantUML server:
```
plantuml -tpng -DPLANTUML_LIMIT_SIZE=16384 delivery_a_sequence.puml
```

Record export date + version in this folder when sharing externally.

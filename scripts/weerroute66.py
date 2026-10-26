name: Route 66 weer

on:
  schedule:
    - cron: "15 5 1-26 11 *"   # 1 t/m 26 november, 05:15 UTC = 06:15 Nederlandse tijd
    - cron: "15 5 27-31 10 *"  # laatste dagen van oktober
  workflow_dispatch:            # handmatig starten via het tabblad Actions

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Voorspelling ophalen
        run: python scripts/weerroute66.py
      - name: Opslaan in de repository
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add weerroute66.json
          git commit -m "Route 66 temperaturen bijgewerkt" || echo "Geen wijzigingen"
          git push

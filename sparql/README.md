# S3 — SPARQL

Cette étape charge les exports N-Triples produits par S2 dans Oxigraph, en
conservant les graphes nommés `buildings`, `measurements` et `weather`. Les
fichiers attendus sont `s2/output/buildings.nt`,
`s2/output/measurements.nt` et `s2/output/weather.nt`. Le chargeur
`sparql/dataset.py` échoue explicitement si un export est absent, vide, invalide
ou si les graphes obtenus ne correspondent pas aux trois graphes attendus.

## Installation et exécution

Depuis la racine du dépôt :

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/test_s3_sparql.py -q
```

Le chargeur peut aussi être appelé depuis Python :

```python
from pathlib import Path

from sparql.dataset import load_s2_exports

store = load_s2_exports(Path("s2/output"))
```

Les quinze requêtes `.rq` sont conservées dans `sparql/queries/`. Les résultats
attendus sont des constantes déclarées indépendamment des requêtes dans
`tests/test_s3_sparql.py`.

## Questions de compétence et résultats attendus

| # | Question | Résultat fixe |
|---|---|---|
| 1 | Quels bâtiments du graphe bâtiments appartiennent au site Robin ? | Les trois bâtiments sélectionnés en S2. |
| 2 | Quelle surface et quel usage sont associés à chacun ? | Carolina : 10984.0/public services ; Dorthy : 5842.9/lodging-residential ; Zenia : 6337.0/education. |
| 3 | Quel compteur électrique est associé à chaque bâtiment ? | Les trois relations compteur-bâtiment de S2. |
| 4 | Combien de relevés typés ont chaque compteur ? | 744 par compteur. |
| 5 | Quelles valeurs ont les compteurs à 2016-01-01 00:00 ? | Carolina 36.438 ; Dorthy 14.3 ; Zenia 52.25. |
| 6 | Quelles valeurs ont-ils à 2016-01-01 12:00 ? | Carolina 101.93799999999999 ; Dorthy 41.5 ; Zenia 136.5. |
| 7 | Quelle est la somme mensuelle par compteur ? | Zenia 102907.5026 ; Dorthy 24945.8 ; Carolina 110441.6953. |
| 8 | Combien d’observations météo typées existent par site ? | Robin : 744. |
| 9 | Quelles températures sont observées au début de la période ? | 3.8 à 00:00 et 3.7 à 01:00, le 1er janvier. |
| 10 | Quels sont les minimum et maximum de `airTemperature` ? | -3.8 et 14.9. |
| 11 | Quels bâtiments n’ont pas de surface ? (`OPTIONAL`) | Aucun résultat : les trois bâtiments ont une surface dans ce jeu S2. |
| 12 | Quels relevés n’ont pas de valeur numérique ? (`NOT EXISTS`) | Aucun résultat : les relevés S2 ont tous une valeur. |
| 13 | Quel relevé du jeu de démonstration a une valeur observée égale à zéro ? | Le relevé synthétique `urn:s3-test:reading-zero`. |
| 14 | Quel relevé du jeu de démonstration ne possède aucun fait de valeur ? (`NOT EXISTS`) | Le relevé synthétique `urn:s3-test:reading-absent`. |
| 15 | Que renvoie `OPTIONAL` pour une valeur présente ou absente ? | Zéro est lié pour `reading-zero` ; la variable est non liée (`None`) pour `reading-absent`. |

Les questions 13 à 15 utilisent uniquement un petit Dataset RDF construit dans
les tests. Ces ressources `urn:s3-test:` sont des exemples pédagogiques : elles
ne sont pas des observations BDG2 et ne modifient aucun export ou fichier source.
Elles démontrent que la valeur numérique zéro est un fait présent, alors que
l’absence produit une solution sans valeur liée (ou aucune ligne lorsqu’un
motif de graphe exige cette valeur).

Toutes les requêtes indiquent leur graphe nommé avec `GRAPH`; les agrégats
comptent ou somment explicitement les relevés et observations typés.

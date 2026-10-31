# S2 — Sérialisations, types et graphes nommés

Cette étape du parcours vise à démontrer les principes suivants :
- les littéraux RDF doivent être typés ; un texte comme `"12"` n’est pas identique à un entier 12
- les graphes nommés permettent de distinguer les sources, les versions ou les autorités
- les exports N-Triples, triés et hachés, sont reproductibles et vérifiables

## Fichiers
- `named_graphs.py` : construit un dataset RDF avec trois graphes nommés : bâtiments, météo et mesures
- `output/buildings.nt` : export N-Triples du graphe des bâtiments
- `output/weather.nt` : export N-Triples du graphe de météo
- `output/measurements.nt` : export N-Triples du graphe des mesures

## Données utilisées

Le parcours utilise les relevés horaires du 1er au 31 janvier 2016 inclus
(744 heures), période couverte par les deux sources. Les trois compteurs
`Robin_public_Carolina`, `Robin_lodging_Dorthy` et `Robin_education_Zenia`
correspondent à des bâtiments de `data/metadata.csv`, tous associés au site
`Robin`. Les valeurs proviennent directement de
`data/meters/cleaned/electricity_cleaned.csv` et la température `airTemperature`
est associée au site et au même horodatage dans `data/weather/weather.csv`.

Les relevés d’électricité et les températures sont des nombres décimaux RDF ;
les horodatages sont typés `xsd:dateTime`. Aucune unité n’est ajoutée, car elle
n’est pas confirmée par ces colonnes ou la documentation du dépôt. Les valeurs
manquantes ne sont ni imputées ni interpolées : une valeur manquante, un
horodatage horaire absent ou un doublon dans la période provoque une erreur
explicite. Les champs descriptifs facultatifs vides des métadonnées sont omis.

## Exécution
```bash
cd /home/naren/ecosystem-training
/home/naren/ecosystem-training/.venv/bin/python s2/named_graphs.py
```

L’export ne crée que les trois fichiers des graphes nommés ; importer le module
ne déclenche pas l’écriture des fichiers.

## Validation
```bash
cd /home/naren/ecosystem-training
/home/naren/ecosystem-training/.venv/bin/pytest tests/test_s2_named_graphs.py -q
```

La sortie attendue est la génération de fichiers `.nt` triés, stables et dotés
d’empreintes SHA-256 identiques après un second export.

Dernière exécution : `5 passed` avec la commande ciblée ci-dessus.

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

## Exécution
```bash
cd /home/naren/ecosystem-training
/home/naren/ecosystem-training/.venv/bin/python s2/named_graphs.py
```

## Validation
```bash
cd /home/naren/ecosystem-training
/home/naren/ecosystem-training/.venv/bin/pytest tests/test_s2_named_graphs.py -q
```

La sortie attendu est la génération de fichiers `.nt` triés, stables et dotés d’empreintes SHA-256 identiques après un second export.

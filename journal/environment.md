# Environment Setup

## Date

2026-09-30

## Objective

Prepare a reproducible Linux-based development environment for the Ecosystem training project.

## Context

The project training path recommends a Linux environment and introduces Docker in later stages. Before working on RDF, SPARQL, and ontology-related tasks, the development environment must be configured and validated.

## Environment Information

### Operating System

Ubuntu 24.04 LTS running on WSL2.

### Python

Python 3.12.3

### Git

Git 2.43.0

### Docker

Docker 29.8.1

### Project Structure

```text
ecosystem-training/
├── journal/
│   ├── environment.md
│   ├── environment.ipynb
│   └── bdg2-exploration.ipynb
├── data/
│   └── metadata.csv
├── rdf/
├── sparql/
├── .venv/
└── .gitignore
```

## Completed Tasks

- Installed WSL2.
- Installed Ubuntu 24.04 LTS.
- Created Linux user account.
- Updated system packages.
- Created project directory structure.
- Installed Git.
- Created a Python virtual environment (`.venv`).
- Verified Python interpreter and version.
- Connected VS Code to WSL.

## Docker Setup

### Date

2026-10-01

### Objective

Prepare a containerized environment for future RDF/Oxigraph/Dagster work.

### Completed

- Installed Docker Desktop.
- Enabled WSL integration.
- Verified Docker CLI from Ubuntu.
- Executed hello-world container.

### Evidence

docker --version

docker run hello-world


## Next Steps

- Explore BDG2 metadata.
- Install RDFLib.
- Build the first RDF graph.
- Learn Turtle serialization.
- Begin SPARQL experimentation.
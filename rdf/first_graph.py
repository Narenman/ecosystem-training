#%% Import libraries
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF
import pandas as pd
from pathlib import Path


#%% Load data
PROJECT_ROOT = Path.cwd()
DATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
df = pd.read_csv(DATA_PATH)
sample = df.head(10)



#%% Create RDF graph
BASE = Namespace("https://ecosystem-training.local/")
g = Graph()
g.bind("eco", BASE)



# %% Entity definitions
# Define entities and properties
Building = BASE["Building"]
Site = BASE["Site"]
PrimarySpaceUsage = BASE["PrimarySpaceUsage"]

belongsToSite = BASE["belongsToSite"]
hasUsage = BASE["hasUsage"]
hasArea = BASE["hasArea"]




# %% Add triples to the graph

# Normalization functions
def normalize_identifier(value: str) -> str:
    """Normalize identifier values to be URI-friendly."""
    return str(value).strip().replace("/", "_").replace(" ", "_").lower()

# Loop through the sample DataFrame and add triples to the graph
for _, row in sample.iterrows():
    building_uri = BASE[f"building/{normalize_identifier(row['building_id'])}"]
    site_uri = BASE[f"site/{normalize_identifier(row['site_id'])}"]
    usage_uri = BASE[f"usage/{normalize_identifier(row['primaryspaceusage'])}"]

    g.add((building_uri, RDF.type, Building))
    g.add((site_uri, RDF.type, Site))
    g.add((usage_uri, RDF.type, PrimarySpaceUsage))
    
    g.add((building_uri, belongsToSite, site_uri))
    g.add((building_uri, hasUsage, usage_uri))
    g.add((building_uri, hasArea, Literal(row['sqm'])))
print(f"Graph has {len(g)} triples.")



# %% Serialize graph to Turtle
OUTPUT_PATH = PROJECT_ROOT / "rdf" / "first_graph.ttl"

g.serialize(destination=str(OUTPUT_PATH), format="turtle")
print(f"Graph written to {OUTPUT_PATH}")
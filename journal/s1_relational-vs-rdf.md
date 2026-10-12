# S1 - Relational Model vs RDF Graph

## Context
Comparison between a relational representation and an RDF graph built from the BDG2 metadata dataset.

## What Becomes Trivial
Queries based on explicit relationships become more natural in RDF.

In the implemented graph, relationships such as:
- Building → Site
- Building → PrimarySpaceUsage
are represented explicitly and can be traversed directly.

## What Becomes Less Advantageous
Non-relational operations become less advantageous. 
Numerical aggregations such as:
- Sum
- Average
- Minimum
- Maximum
do not benefit significantly from the graph structure and remain very natural in a tabular representation.

## Global Resource Identification
RDF uses global identifiers (IRIs) to identify resources.
Unlike local database keys, an IRI can identify the same resource independently of a specific database schema.

## Conclusion
The graph model facilitates navigation through explicit relationships between resources.
The relational model remains well suited for aggregation-oriented analytical tasks.
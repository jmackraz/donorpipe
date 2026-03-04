# SCRATCH.md for snippets and notes for the agent

## Snippet 1 - discover and document relationships

Some relationships among the entities in TransactionStore are established 
at load time in transaction_loader.associate_donation_receipts, others are 
established at runtime by three methods of TransactionStore,
following the comment "associations"

Determine and document the relationships to file docs/relationships.md

## Snippet 2 - improve the implementation of agents and plan for client use
Entity-relationships are documented in docs/relationships.md

The efficiency and maintainability of the relationships is not known good.
Furthermore, soon in this project we will serialize the entity-relationship
graph and deliver it to the front-end client.  

The front-end client will need to deserialize the graph into TypeScript and present the
related entities quickly to the user.

Think deeply about how we might to improve the implementation of relationships, and create a high-level
design proposal for serialization and deserialization.

Before making any changes, append documentation of your recommendations to docs/relationships.md.
Change no other files.
I will review and re-engage later.

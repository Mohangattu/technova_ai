---
document_id: eng_database_001
title: Database Guidelines
department: Engineering
section: Database
document_type: technical
version: 1.3
access_level: EMPLOYEE
---
# Database Guidelines

## Indexing
Indexes should be created for columns frequently used in filtering, joining, or ordering when query analysis demonstrates that the index provides a benefit. Excessive indexes can increase write cost.

## Transactions
Operations that must succeed or fail together should be executed inside a database transaction.

## Connection Management
Applications should use connection pooling rather than opening a new database connection for every request.

## Query Performance
Slow queries should be investigated using execution plans. Developers should avoid selecting unnecessary columns and should paginate large result sets.

## Schema Changes
Production schema changes must be backward compatible when multiple application versions may run concurrently.

## Data Integrity
Primary keys, foreign keys, unique constraints, and appropriate validation should be used to protect data consistency.

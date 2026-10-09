---
document_id: sec_authz_001
title: Authorization Standard
department: Security
section: Authorization
document_type: security
version: 1.2
access_level: MANAGER
---
# Authorization Standard

## Authorization
Authentication establishes who a user is; authorization determines which resources and actions that user is permitted to access.

## Least Privilege
Users and services should receive only the permissions required to perform their responsibilities.

## Role-Based Access
Applications should use approved roles and permissions when access differs between employee groups.

## RAG Retrieval
For internal knowledge systems, authorization must be enforced before retrieval. The language model must never be trusted to decide whether a user is allowed to access a document.

## Audit
Access to restricted resources should generate audit information sufficient for security review.

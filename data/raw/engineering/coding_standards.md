---
document_id: eng_coding_001
title: Coding Standards
department: Engineering
section: Coding Standards
document_type: policy
version: 1.0
access_level: EMPLOYEE
---
# Coding Standards

## Naming
Names should communicate intent. Functions should generally describe an action, while classes should represent a meaningful abstraction.

## Functions
Functions should have a focused responsibility. Large functions should be decomposed when doing so improves readability and testability.

## Error Handling
Exceptions should be handled at an appropriate boundary. Empty catch blocks and silently ignored failures are prohibited.

## Testing
New business-critical functionality should include automated tests. Tests should cover normal behavior and important failure conditions.

## Code Review
Changes to shared production code require peer review before merging. Reviewers should examine correctness, maintainability, security implications, and test coverage.

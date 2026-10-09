---
document_id: dev_docker_001
title: Docker Guidelines
department: DevOps
section: Docker
document_type: technical
version: 1.0
access_level: EMPLOYEE
---
# Docker Guidelines

## Images
Production images should be built from trusted base images and should contain only the dependencies required at runtime.

## Reproducibility
Dependency versions should be pinned where practical so that the same source revision produces a predictable runtime environment.

## Secrets
Secrets must not be copied into Docker images or committed into Dockerfiles.

## Health Checks
Services should define a health check appropriate to their runtime behavior.

## Image Security
Images should be scanned for known vulnerabilities before production deployment.

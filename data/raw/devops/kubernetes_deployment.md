---
document_id: dev_k8s_001
title: Kubernetes Deployment Guidelines
department: DevOps
section: Kubernetes
document_type: technical
version: 1.2
access_level: DEVOPS
---
# Kubernetes Deployment Guidelines

## Deployments
Production services should be deployed using declarative Kubernetes manifests or the approved deployment tooling.

## Readiness
Readiness probes should prevent traffic from reaching an instance until the service is ready to handle requests.

## Liveness
Liveness probes should detect an unhealthy process so that Kubernetes can restart it when appropriate.

## Resource Limits
Production workloads should define CPU and memory requests and limits based on measured workload characteristics.

## Scaling
Horizontal scaling should be configured for services where demand varies significantly over time.

## Secrets
Sensitive configuration must use Kubernetes Secrets or the approved external secret-management integration.

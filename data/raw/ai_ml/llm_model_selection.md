---
document_id: ai_llm_001
title: LLM Model Selection Guide
department: AI & ML
section: LLM Model Selection
document_type: technical
version: 1.0
access_level: AI_ENGINEER
---
# LLM Model Selection Guide

## Selection Criteria
TechNova selects language models based on answer quality, latency, context capacity, reliability, cost, and operational constraints.

## Task Fit
A smaller model may be preferred for classification, routing, or rewriting when its quality is sufficient. More capable models may be reserved for complex generation tasks.

## Prompting
Prompts should clearly define the model's task, permitted evidence, expected output format, and behavior when evidence is insufficient.

## Reliability
Applications must not assume that an LLM call always succeeds. Timeouts, transient provider failures, and malformed responses should be handled by the application.

## Model Tracking
Production systems should record the model identifier and relevant configuration for reproducibility.

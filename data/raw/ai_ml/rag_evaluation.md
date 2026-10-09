---
document_id: ai_rag_eval_001
title: RAG Evaluation Guide
department: AI & ML
section: RAG Evaluation
document_type: technical
version: 1.0
access_level: AI_ENGINEER
---
# RAG Evaluation Guide

## Retrieval Metrics
TechNova evaluates retrieval using Recall@K, Precision@K, Mean Reciprocal Rank (MRR), and nDCG.

## Generation Metrics
Generated answers should be assessed for faithfulness or groundedness, context relevance, answer relevance, and citation correctness.

## Baselines
Every major retrieval improvement should be compared with a baseline system rather than evaluated in isolation.

## Evaluation Dataset
The benchmark should contain questions with known relevant documents and should include semantic, lexical, ambiguous, and unanswerable queries.

## Human Evaluation
Selected difficult cases should be manually reviewed to identify failure modes that automated metrics may miss.

## Reporting
Evaluation results should record the system version, model configuration, retrieval configuration, and dataset version so that experiments are reproducible.

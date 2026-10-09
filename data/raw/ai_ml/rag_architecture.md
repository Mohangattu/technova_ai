---
document_id: ai_rag_arch_001
title: RAG Architecture Guide
department: AI & ML
section: RAG Architecture
document_type: technical
version: 1.2
access_level: AI_ENGINEER
---
# RAG Architecture Guide

## Retrieval-Augmented Generation
TechNova's RAG architecture separates retrieval from generation. The retriever identifies relevant organizational knowledge, and the language model generates an answer using the retrieved evidence.

## Retrieval
The production design supports both dense semantic retrieval and BM25 lexical retrieval. Hybrid retrieval is used when semantic similarity and exact terminology are both important.

## Reranking
Candidate documents may be reranked with a cross-encoder after initial retrieval. The reranker receives the query and candidate text together and produces a relevance score.

## Context
The generation stage should receive only the selected evidence rather than the entire knowledge base.

## Grounding
The language model must be instructed to answer from retrieved TechNova evidence and should not invent organizational facts that are absent from the supplied context.

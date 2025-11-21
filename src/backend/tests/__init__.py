"""
ŠKODA AI Skill Coach - Complete Test Suite
==========================================

This package contains comprehensive tests for the ŠKODA AI Skill Coach backend.

Test Categories:
1. Ingestion Tests - File ingestion (CSV, Excel, JSON, TXT, DOCX)
2. AI Module Tests - LLM integration and fallbacks
3. Database Tests - CRUD, JSONB, queries, migrations
4. API Endpoint Tests - All routes with success/error cases
5. TONE Validation Tests - TONE format handling
6. Pipeline E2E Tests - Complete end-to-end workflows
7. Load Testing - Performance and stress tests
8. Security Tests - PII masking, SQL injection, etc.
9. Documentation Tests - OpenAPI schema validation

Run tests:
    pytest tests/ -v

Generate coverage:
    pytest tests/ --cov=swx_api --cov-report=xml --cov-report=html
"""


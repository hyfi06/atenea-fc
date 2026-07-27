# 0002 — Django REST Framework for the API layer

**Status:** Accepted
**Date:** 2026-07-27

## Context

The React frontend needs to consume a JSON API served by Django. Services will be added incrementally (students, users, and others yet to be defined), so the API layer needs to scale in the number of resources without reinventing common concerns (serialization, pagination, permissions, browsable API for debugging).

## Decision

Use [Django REST Framework](https://www.django-rest-framework.org/) as the API layer for all backend services.

## Consequences

- New services expose their resources as DRF viewsets/serializers, keeping a consistent pattern as integration proceeds incrementally.
- DRF's permission classes are the natural place to enforce per-service authorization once Google OAuth is wired in (see [0003](0003-google-oauth-allauth-jwt.md)).
- Adds a dependency (`djangorestframework`) but it's the de facto standard for this use case and integrates cleanly with `dj-rest-auth`.

## Alternatives considered

- **GraphQL (Graphene/Strawberry):** more flexible query shapes for the frontend, but higher complexity and learning curve not justified for an incrementally-built internal system.
- **Plain Django views returning JSON:** avoids the DRF dependency, but re-implements pagination, content negotiation, and serialization that DRF already provides.

# 0008 — uv para gestión de dependencias y entorno Python

**Status:** Accepted
**Date:** 2026-07-27

## Context

El backend (`/backend`) necesita un gestor de dependencias/entorno Python. El equipo está aprendiendo Django y el proyecto crecerá de forma incremental, por lo que conviene un flujo simple, rápido y con lockfile reproducible desde el primer commit.

## Decision

Usar [uv](https://docs.astral.sh/uv/) (Astral) como gestor de dependencias y entorno virtual para `/backend`. `pyproject.toml` + `uv.lock` son la fuente de verdad de las dependencias; no se usan `requirements*.txt`. `.python-version` fija la versión de Python del proyecto.

## Consequences

- `uv sync` crea el entorno virtual e instala exactamente lo que dice `uv.lock`, tanto en desarrollo local como dentro del `Dockerfile`.
- `uv run <comando>` reemplaza el flujo manual de activar el venv y correr el comando (ej. `uv run manage.py migrate`).
- El `Dockerfile` necesita cuidar que el entorno virtual generado por `uv` no quede oculto por el bind-mount del código fuente en desarrollo (ver notas en `docs/development/getting-started.md`).

## Alternatives considered

- **Poetry:** maduro y ampliamente usado en el ecosistema Django, pero más lento y con más capas (resolver, plugins) que uv para el mismo resultado.
- **pip + `requirements.txt`:** es el flujo "clásico" de Django y explícito paso a paso, pero sin lockfile real (`pip freeze` no resuelve igual de bien conflictos transitivos) y sin la velocidad de instalación de uv.

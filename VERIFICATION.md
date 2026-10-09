# Verification status

## Checked while preparing this project

- All Python files parse successfully.
- Frontend JavaScript passes `node --check`.
- Compose YAML parses successfully and contains exactly two services.
- The backend build context, internal database hostname, shared network, health dependency, and PostgreSQL 17 volume mount were checked.
- Every database credential is read from environment variables; no real password appears in application source or `.env.example`.
- Git ignore rules were checked: `.env` is ignored and `.env.example` can be committed.
- The final ZIP includes the source, guides, environment template, and private local `.env`; it excludes Python caches and Git internals.

## Must be checked on your computer

This preparation environment has no Docker engine, PostgreSQL server, or browser executable. Flask/Psycopg installation was also unavailable. Therefore container startup, real database API operations, persistence across container recreation, and browser behavior have **not** been runtime-tested here.

Before submission:

1. Start Docker Desktop and run `docker compose up`.
2. Open http://localhost:8080 and create, complete, filter, and cancel missions.
3. Run the smoke test from `README.md` against the real running services.
4. Run the persistence demonstration: create and complete a mission, run `docker compose down`, recreate containers, and verify the mission and credits remain.
5. Ensure the public GitHub repository contains `.env.example` but no `.env`.

The smoke test is included for you to run; its inclusion does not mean it has already passed against real PostgreSQL.

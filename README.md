# Mars Mission Control

A small Mars colony mission board built for **Homework #2: Multi-Container Application with Docker Compose**.

Create missions, mark them complete, earn credits, and progress from Cadet to Explorer to Pioneer. PostgreSQL stores every mission and completion. No data is stored only in browser memory.

## Stack and architecture

- **Backend:** Python 3.12, Flask, Gunicorn, Psycopg 3.
- **Database:** PostgreSQL 17.
- **Dashboard:** plain HTML, CSS, JavaScript; served by the backend.
- **Containers:** exactly two services, `backend` and `db`.

Browser → `localhost:8090` → backend container (`8000`) → `db:5432` → PostgreSQL named volume.

The browser talks to the backend. Only the backend connects to PostgreSQL. `db` is the service's DNS name on the Compose network; `localhost` inside the backend would refer to the backend itself.

## 1. Before starting

Install **Docker Desktop** and **Git**. On Windows, use Docker Desktop with **Linux containers** and the WSL 2 engine. Open Docker Desktop and wait until its engine is running.

In VS Code, open this project folder: the folder directly containing `compose.yaml`. Open its terminal. You do not need to install Python, Flask, Node, or PostgreSQL on your computer.

Check:

```powershell
docker --version
docker compose version
git --version
```

## 2. Environment file

The private project download contains a ready-to-use `.env` with a generated local development password. Keep it in the same folder as `compose.yaml`.

**Do not upload `.env` to GitHub.** The included `.gitignore` excludes it, and `.dockerignore` excludes environment files from the backend image build context. The backend gets its database configuration at runtime through Compose.

Someone cloning the public repository will only receive `.env.example`. They must create `.env`:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Replace the password placeholder with your own random local password. Use plain letters and digits if editing manually. No real credentials belong in `.env.example`.

Configuration:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Private local database password |
| `APP_PORT` | Browser-facing port, default `8090` |
| `APP_NAME` | Dashboard heading and browser title |

## 3. Run the entire application

```powershell
docker compose up
```

On the first run, Compose downloads the base images and builds the backend. Wait for `Database ready.` and Gunicorn startup messages.

Open **http://localhost:8080** in your browser.

Three demo missions are added on the first successful startup only. They are not recreated on subsequent restarts. Create and complete your own missions through the dashboard. Completion adds that mission's reward to the colony's total credits. Completing the same mission twice returns HTTP `409`; completed missions stay in history.

To run in the background instead:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

Press Ctrl+C to leave the log view. To rebuild after changing backend files:

```powershell
docker compose up -d --build
```

## 4. Prove database persistence

1. Create a mission called **Persistence proof** with a reward of **150**.
2. Complete it. Note the mission ID and current credits.
3. Stop and remove the containers:

   ```powershell
   docker compose down
   ```

4. Recreate the containers:

   ```powershell
   docker compose up -d --force-recreate
   ```

5. Refresh the browser after both containers are healthy. The mission, completed status, and credits must remain.

`colony_data` is a named volume mounted at `/var/lib/postgresql/data`. Removing containers with ordinary `docker compose down` preserves this volume. With the project name in this file, its Docker name is normally `mars-mission-control_colony_data`.

Inspect it:

```powershell
docker volume ls
docker volume inspect mars-mission-control_colony_data
```

**Do not use `docker compose down -v` for the persistence demonstration: `-v` deletes the database volume and its data.** Removing the volume is only for an intentional complete reset.

## 5. Check the API and database

Open these URLs in a browser:

- http://localhost:8090/api/health
- http://localhost:8090/api/missions
- http://localhost:8090/api/stats

Example health response:

```json
{"status":"ok","database":"connected"}
```

Run the API smoke test against the real backend and PostgreSQL:

```powershell
docker compose exec -T backend python - < tests/smoke_test.py
```

**The command above uses shell input redirection and works in Bash or Windows Command Prompt. In PowerShell, use this instead:**

```powershell
Get-Content -Raw tests/smoke_test.py | docker compose exec -T backend python -
```

The test verifies creation, reading, input validation, completion, duplicate completion protection, credits, and cancellation. It intentionally leaves one completed mission as evidence. Run it when nobody else is changing missions, because it compares statistics before and after.

To see actual stored rows, open a PostgreSQL terminal:

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

If your Windows terminal changes the quotes, use this two-step alternative:

```powershell
docker compose exec db sh
```

Then, inside the container:

```sh
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

In PostgreSQL:

```sql
SELECT id, title, sector, reward, status FROM missions ORDER BY id;
```

Type `\q` to leave PostgreSQL. If you used the two-step alternative, type `exit` to leave the container shell.

### API endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/` | Browser dashboard |
| GET | `/api/health` | Checks database connectivity |
| GET | `/api/missions` | Reads missions from PostgreSQL |
| POST | `/api/missions` | Writes a new mission |
| PATCH | `/api/missions/{id}/complete` | Updates a mission to completed |
| DELETE | `/api/missions/{id}` | Deletes an available mission |
| GET | `/api/stats` | Reads aggregate progress and credits |

Example POST body:

```json
{
  "title": "Find underground water",
  "sector": "Valles Marineris",
  "category": "Exploration",
  "reward": 150
}
```

Allowed categories: `Exploration`, `Engineering`, `Science`. Reward: integer `10–500`. Title: `1–100` characters. Destination: `1–40` characters. Whitespace-only names are rejected.

PowerShell example:

```powershell
$missionBody = @{ title = "Find underground water"; sector = "Valles Marineris"; category = "Exploration"; reward = 150 } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8090/api/missions -Method Post -ContentType "application/json" -Body $missionBody
```





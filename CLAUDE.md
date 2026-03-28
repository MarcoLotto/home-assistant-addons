# CLAUDE.md — AI Assistant Guide for home-assistant-addons

This file provides context for AI coding assistants (e.g., Claude) working in this repository.

---

## Repository Overview

This is a **Home Assistant Add-on Repository** maintained by Marco Lotto. It hosts custom add-ons that can be installed in [Home Assistant](https://www.home-assistant.io/) via the Supervisor Add-on Store.

- **License**: Apache License 2.0
- **Registry**: `ghcr.io/MarcoLotto/`
- **Current add-ons**: 1 (`home-task-scheduler`)

---

## Repository Structure

```
home-assistant-addons/
├── .devcontainer.json              # Dev container config (HA add-on dev image)
├── .github/
│   ├── workflows/
│   │   ├── builder.yaml            # CI: builds Docker images for changed add-ons
│   │   └── lint.yaml               # CI: lints add-ons with frenck/action-addon-linter
│   └── dependabot.yaml             # Auto-updates GitHub Actions (weekly, Wednesdays)
├── .vscode/tasks.json              # VS Code task: "Start Home Assistant"
├── repository.yaml                 # HA add-on repository metadata
├── README.md
├── LICENSE
└── home-task-scheduler/            # Add-on directory (one per add-on)
```

### Add-on Directory Structure (home-task-scheduler as example)

```
home-task-scheduler/
├── config.yaml           # HA add-on metadata: name, version, arch, ports, maps
├── build.yaml            # Docker build config: base images per arch, labels
├── Dockerfile            # Container definition
├── translations/
│   └── en.yaml           # HA configuration schema translations
├── initial_config/
│   ├── tasks.yaml        # Default tasks config (copied to /config on first run)
│   └── users.yaml        # Default users config (copied to /config on first run)
├── rootfs/               # Filesystem overlaid onto container at build time
│   ├── usr/bin/
│   │   ├── run.sh        # Entry point: starts the Python server
│   │   └── server/       # Python application source
│   │       ├── controller.py           # REST API (Bottle framework)
│   │       ├── domain.py               # Domain models and enums
│   │       ├── model.py                # DTOs for API responses
│   │       ├── model_mapper.py         # Domain-to-DTO converters
│   │       ├── common.py               # Constants (BASE_TARGET_PATH)
│   │       ├── requirements.txt        # Python dependencies
│   │       ├── services/
│   │       │   ├── config_loader_service.py   # Loads tasks.yaml / users.yaml
│   │       │   ├── generate_tasks_service.py  # Daily task scheduling logic
│   │       │   ├── notifications_service.py   # Multi-language notifications
│   │       │   └── users_service.py           # User management
│   │       └── repositories/
│   │           ├── database_client.py          # SQLite setup and session context manager
│   │           └── scheduled_task_repository.py # CRUD for scheduled_tasks table
│   └── etc/services.d/home-task-scheduler/
│       ├── run             # s6-overlay service run script
│       └── finish          # s6-overlay graceful shutdown script
├── README.md
├── DOCS.md               # User-facing documentation
└── CHANGELOG.md
```

---

## Add-on: home-task-scheduler

### What It Does

Schedules daily household tasks and distributes them among users based on configurable effort capacity. Exposes a REST API on port 8000 used by Home Assistant automations and sensors.

### Configuration Files (runtime, at `/config/home-task-scheduler/`)

- **`tasks.yaml`** — defines tasks with `id`, `name`, `days_interval`, `effort`, and optional `allowed_days`
- **`users.yaml`** — defines users with `id`, `username`, and `available_daily_effort` per day of week (`mon`–`sun`)
- **`database.db`** — SQLite database created automatically at startup

### REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | All configured tasks |
| GET | `/tasks/<id>` | Single task by ID |
| GET | `/scheduled-tasks/today` | Today's tasks (optional `?status=` filter) |
| GET | `/scheduled-tasks/<id>` | Single scheduled task |
| PUT | `/scheduled-tasks/<id>` | Update a task's status |
| GET | `/notifications/scheduled-tasks` | Notification message (`?language=en` or `es`) |
| PUT | `/users/<user_id>/pending-tasks` | Mark all a user's pending tasks with a status |
| GET | `/users/<user_id>/pending-tasks` | Get all pending tasks for a user |
| POST | `/generate-tasks` | Manually trigger daily task generation |

### Task Status Values

`PENDING` | `COMPLETED` | `INCOMPLETE`

### Scheduling Logic (GenerateTasksService)

1. Runs at startup and daily at **06:00** via APScheduler.
2. Deletes today's non-completed tasks (safe to re-run).
3. Marks previous days' `PENDING` tasks as `INCOMPLETE`.
4. Shuffles tasks randomly, then assigns:
   - **Mandatory tasks** (effort = 0) first, rotating users.
   - **Effort-based tasks** to users with remaining daily capacity.
5. Respects `days_interval` (skips if scheduled too recently) and `allowed_days`.

### Python Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Bottle | 0.12.25 | Minimal REST API framework |
| Waitress | 2.1.2 | Production WSGI server |
| APScheduler | 3.10.4 | Background cron scheduling |
| PyYAML | 6.0.1 | YAML config loading |
| pytz / tzlocal | 2023.3 / 5.1 | Timezone handling |

### Container Details

- **Base image**: Alpine Linux 3.15 (all architectures)
- **Process manager**: s6-overlay (via HA base image)
- **Port**: 8000/tcp
- **Volume map**: `/config` (read/write) — stores user config and database

---

## Development Conventions

### Naming

- Add-on directories: `kebab-case`
- Python modules: `snake_case`
- Classes: `PascalCase`
- Methods and variables: `snake_case`

### Architecture Pattern (Layered)

```
controller.py       ← HTTP layer (routes, request/response)
services/           ← Business logic
repositories/       ← Data access (SQLite)
domain.py           ← Entities and enums
model.py            ← API DTOs (.to_dict() for JSON)
model_mapper.py     ← Domain → DTO conversion
```

### API Response Shape

```json
{ "tasks": [...] }
{ "result": "ok" }
{ "notification_available": true, "notification_message": "..." }
```

### Database

- SQLite file at `/config/home-task-scheduler/database.db`
- Single table: `scheduled_tasks (scheduled_task_id, task_id, scheduled_date, user_id, status)`
- All DB access goes through `open_db_session()` context manager from `database_client.py`
- Date values stored as ISO strings for SQLite compatibility

### Adding a New Add-on

1. Create a new directory at the repo root in `kebab-case`.
2. Add required files: `config.yaml`, `build.yaml`, `Dockerfile`, `rootfs/`, `README.md`, `DOCS.md`, `CHANGELOG.md`.
3. `config.yaml` must declare: `name`, `version`, `slug`, `description`, `arch`, `startup`, and any `ports`/`map` entries.
4. `build.yaml` must declare base images per architecture and container labels.
5. The CI pipeline auto-detects new add-ons when files in `MONITORED_FILES` change.

### Versioning

- Semantic versioning: `MAJOR.MINOR.PATCH` in `config.yaml`
- Update `CHANGELOG.md` with every release.

---

## CI/CD Workflows

### builder.yaml

- Triggers on push/PR to `main`.
- Detects changed add-ons by checking for modifications in: `build.yaml`, `config.yaml`, `Dockerfile`, `rootfs/`.
- Builds all 5 architectures (`aarch64`, `amd64`, `armhf`, `armv7`, `i386`) in a matrix.
- On **PRs**: builds in `--test` mode (no push).
- On **push to main**: publishes images to `ghcr.io/MarcoLotto/<addon-slug>`.

### lint.yaml

- Triggers on push/PR to `main` and daily at 00:00 UTC.
- Runs `frenck/action-addon-linter@v2.13` on every add-on directory.
- Must pass before merging.

---

## Local Development

Uses a dev container (`ghcr.io/home-assistant/devcontainer:addons`) with:
- Port forwarding: `7123:8123` (Home Assistant UI) and `7357:4357` (add-on testing).
- Extensions: ShellCheck, Prettier.
- Auto-format on save/paste/type; trim trailing whitespace.
- Default terminal: ZSH.

To test locally, use the VS Code task **"Start Home Assistant"** or the dev container bootstrap.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `home-task-scheduler/config.yaml` | Add-on version, arch, port, and HA metadata |
| `home-task-scheduler/build.yaml` | Base images per arch, Docker labels |
| `home-task-scheduler/Dockerfile` | Container build instructions |
| `home-task-scheduler/rootfs/usr/bin/server/controller.py` | All REST API routes |
| `home-task-scheduler/rootfs/usr/bin/server/services/generate_tasks_service.py` | Core scheduling algorithm |
| `home-task-scheduler/rootfs/usr/bin/server/repositories/database_client.py` | DB init and session management |
| `.github/workflows/builder.yaml` | Build and publish pipeline |
| `.github/workflows/lint.yaml` | Lint validation pipeline |

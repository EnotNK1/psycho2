# Existing server deployment

`docker-compose.server.yml` is a standalone configuration, not an override.
Use it instead of the default `docker-compose.yml` on the recovered server.
The default configuration is unchanged for existing local PostgreSQL 15 users.

## Preconditions

- Keep a verified database backup outside the checkout before updates.
- Set `POSTGRES_DATA_VOLUME` in the server's untracked `.env` to the exact
  existing, verified PostgreSQL 18 volume. Do not use a PostgreSQL 15 volume.
- `DB_HOST=db`, `DB_PORT=4321`, `DB_USER=postgres`, `DB_NAME=psycho2`.
- `REDIS_HOST=redis`, `REDIS_PORT=6789`.
- `DB_PASS` must match the existing PostgreSQL role password. Changing
  `POSTGRES_PASSWORD` does not reset a password in an initialized cluster.
- Preserve the original encryption and JWT keys. A new encryption key cannot
  decrypt existing sensitive records.
- The existing Docker network `odeyalo-network` must be present.
- Use the existing Compose project name. For the recovered checkout this is
  `back`; the directory name alone is not a reliable project selector.

Neither PostgreSQL nor Redis publishes host ports. Only nginx publishes 1802.
The external volume declaration intentionally fails if the volume is missing.
Never run two PostgreSQL containers against the same data volume.

## Prepare the transition

Preserve the server's modified Compose file outside the checkout before
replacing it with the tracked version. Do not overwrite `.env`, delete volumes,
or run `down -v`. Keep the original backups and rescue volumes.

Validate without starting services:

```bash
docker compose -p back -f docker-compose.server.yml config --quiet
docker volume inspect "$(grep '^POSTGRES_DATA_VOLUME=' .env | cut -d= -f2-)"
```

The volume inspection example assumes an unquoted value in `.env`.
Do not share full `docker compose config` output: it contains resolved secrets.

## Updates after transition

Review the code and migrations and verify a fresh backup before updating.
Keep `-p back -f docker-compose.server.yml` on every Compose command; do not
mix the server file with the default local file.

```bash
docker compose -p back -f docker-compose.server.yml build app celery_worker celery_beat
docker compose -p back -f docker-compose.server.yml up -d
docker compose -p back -f docker-compose.server.yml ps
docker compose -p back -f docker-compose.server.yml logs --since 5m --tail 80 app celery_worker backup
docker compose -p back -f docker-compose.server.yml exec -T backup /backup.sh
```

The first transition can recreate containers and requires a maintenance window.
Do not run it merely to validate the file. Application startup stops if Alembic
fails. Before deploying schema changes, test migrations on an isolated restored
backup; successful startup alone does not prove that existing records are usable.
Check login, old diary text, mood history, worker readiness, and backup output.
Reverting Git commits does not revert database schemas or recover lost records.

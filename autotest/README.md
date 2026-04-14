Test architecture:

- `autotest/local/api/entities`
  Endpoint-level local tests with dependency overrides and HTTP assertions.
- `autotest/local/unit/services`
  Service-layer logic tests with fake repositories and explicit error-path coverage.
- `autotest/local/unit/api`
  Unit tests for API helper functions that do not require HTTP transport.
- `autotest/factories`
  Shared data builders, constants and reusable entity payload factories.
- `autotest/integration`
  Integration tests for selected entities. This layer is optional and is not part of the default docker run.
- `autotest/docker/smoke`
  Containerized smoke suites for fast environment-level checks.
- `autotest/conftest.py`
  Shared fixtures and app factory.
- `autotest/docker/Dockerfile`
  Dedicated image for containerized test runs.
- `autotest/docker/docker-compose.yml`
  Compose entrypoint for containerized test execution with a dedicated PostgreSQL container.

Run all local tests:

```powershell
.\.venv\Scripts\python -m pytest autotest\local\api autotest\local\unit -c autotest\pytest.ini -q
```

Run integration tests:

```powershell
.\.venv\Scripts\python -m pytest autotest\integration -c autotest\pytest.ini -q
```

Run a single local API suite:

```powershell
.\.venv\Scripts\python -m pytest autotest\local\api\entities\test_user_task_api.py -c autotest\pytest.ini -q
```

Run a single local service suite:

```powershell
.\.venv\Scripts\python -m pytest autotest\local\unit\services\test_user_task_service.py -c autotest\pytest.ini -q
```

Run main containerized suite:

```powershell
docker compose -f autotest/docker/docker-compose.yml up --build --abort-on-container-exit
```

This compose run starts:

- `testdb` - PostgreSQL 15 test database
- `autotest-runner` - pytest runner for `autotest/local/api`, `autotest/local/unit` and `autotest/docker/smoke`

Run integration tests separately:

```powershell
.\.venv\Scripts\python -m pytest autotest\integration -c autotest\pytest.ini -q
```

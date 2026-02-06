# Testing Guide

## Overview

TrainerLab uses a multi-layered testing strategy to ensure reliability and quality across the competitive intelligence platform.

### Testing Layers

1. **Unit Tests** - Fast, isolated tests for individual functions and components
   - Backend: pytest with pytest-asyncio for async code
   - Frontend: Vitest with React Testing Library
2. **Integration Scripts** - Automated verification of API endpoints and data flows
   - `verify-local.sh` - Core API validation (meta, intelligence, cards)
   - `verify-phase3.sh` - Phase 3 feature verification (comparison, forecast, tech cards)
3. **Manual QA** - Visual and functional testing checklists
   - `QA_PHASE3_CHECKLIST.md` - Phase 3 feature verification checklist

### Current Coverage

As of February 2026:

- **Backend**: 1,747+ passing tests (1,721 pre-Phase 3 + 26 new Phase 3 tests)
- **Frontend**: 1,822 passing tests (1,799 pre-Phase 3 + 23 new Phase 3 tests)

All feature work must include unit tests. Test-driven development (TDD) is preferred.

## Running Tests

### Backend (Python)

```bash
# Run all tests with coverage
cd apps/api
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_specific.py -v

# Run tests matching a pattern
uv run pytest -k "test_meta" -v

# Run with coverage report
uv run pytest --cov --cov-report=html
open htmlcov/index.html

# Run single test
uv run pytest tests/test_specific.py::test_function_name -v
```

### Frontend (TypeScript)

```bash
# Run all tests
cd apps/web
pnpm test

# Run with coverage
pnpm test:coverage

# Run in watch mode
pnpm test:watch

# Run specific test file
pnpm test src/components/MetaSnapshot.test.tsx

# Update snapshots
pnpm test -u
```

### Integration Scripts

```bash
# Start local environment
docker compose up -d

# Run all verification checks
./scripts/verify-local.sh

# Run specific group of checks
./scripts/verify-local.sh --group=comparison
./scripts/verify-local.sh --group=forecast
./scripts/verify-local.sh --group=tech-cards

# Run Phase 3 verification with verbose output
./scripts/verify-phase3.sh --verbose

# Stop environment
docker compose down
```

### Pre-commit Hooks

```bash
# Install hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run prettier --all-files
```

## Backend Test Patterns

### Database Mocking

Use `AsyncMock` with `spec=AsyncSession` to mock database sessions:

```python
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)
```

### HTTP Testing

Use FastAPI's `TestClient` for endpoint testing:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/api/meta/snapshots")
    assert response.status_code == 200
    assert "snapshots" in response.json()
```

### Dependency Injection

Override FastAPI dependencies for testing:

```python
from src.main import app
from src.database import get_db

async def override_get_db():
    """Override database dependency."""
    mock_db = AsyncMock(spec=AsyncSession)
    yield mock_db

app.dependency_overrides[get_db] = override_get_db

# Don't forget to clean up
app.dependency_overrides.clear()
```

### Service Patching

Patch service classes at the module level where they're imported:

```python
from unittest.mock import patch, AsyncMock

@patch("src.routers.meta.MetaService")
async def test_meta_endpoint(mock_svc_cls):
    # Create mock service instance
    mock_svc = AsyncMock()
    mock_svc.get_snapshots.return_value = [...]

    # Make the class constructor return our mock instance
    mock_svc_cls.return_value = mock_svc

    # Test the endpoint
    response = client.get("/api/meta/snapshots")
    assert response.status_code == 200
```

**Important**: Use lowercase names like `mock_svc_cls` to avoid Ruff N806 violations.

### Model Mocking

Use `MagicMock` with explicit `spec` and attribute assignments:

```python
from unittest.mock import MagicMock
from src.models.meta import MetaSnapshot

def test_snapshot_processing():
    mock_snapshot = MagicMock(spec=MetaSnapshot)
    mock_snapshot.id = 1
    mock_snapshot.date = datetime(2026, 4, 10)
    mock_snapshot.region = "us"
    mock_snapshot.format = "standard"

    # Test logic using mock_snapshot
    result = process_snapshot(mock_snapshot)
    assert result is not None
```

### Async Tests

Use `@pytest.mark.asyncio` for async test functions:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

## Frontend Test Patterns

### Render Wrapper

Wrap components with `QueryClientProvider` to avoid cache issues:

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}
```

### API Mocking

Mock API functions using Vitest's `vi.mock`:

```typescript
import { vi } from "vitest";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  getMetaSnapshots: vi.fn(),
  getComparison: vi.fn(),
}));

// In test
vi.mocked(api.getMetaSnapshots).mockResolvedValue([
  { id: 1, date: "2026-04-10", region: "us" },
]);
```

### Async Assertions

Use `waitFor` for assertions that depend on async operations:

```typescript
import { render, screen, waitFor } from "@testing-library/react";

test("displays snapshot data", async () => {
  renderWithQueryClient(<MetaSnapshotView />);

  await waitFor(() => {
    expect(screen.getByText("April 10, 2026")).toBeInTheDocument();
  });
});
```

### User Interaction

Use `fireEvent` or `userEvent` for simulating user actions:

```typescript
import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

test("handles click event", async () => {
  renderWithQueryClient(<ComparisonSelector />);

  const button = screen.getByRole("button", { name: "Compare" });
  fireEvent.click(button);

  // Or for more realistic interactions
  const user = userEvent.setup();
  await user.click(button);
});
```

### Component Testing Flow

Follow this pattern for component tests:

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

describe("MetaSnapshotCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders snapshot data correctly", async () => {
    // 1. Setup mocks
    vi.mocked(api.getSnapshot).mockResolvedValue(mockSnapshot);

    // 2. Render component
    renderWithQueryClient(<MetaSnapshotCard id={1} />);

    // 3. Wait for async data
    await waitFor(() => {
      expect(screen.getByText("Standard")).toBeInTheDocument();
    });

    // 4. Assert DOM content
    expect(screen.getByText("April 10, 2026")).toBeInTheDocument();
    expect(screen.getByText("United States")).toBeInTheDocument();
  });
});
```

## Common Gotchas

### Backend

1. **Never use `importlib.reload()` in tests**
   - Corrupts module-level globals and singleton instances
   - If you need fresh imports, structure tests to avoid this need

2. **Ruff N806 enforcement**
   - No PascalCase variables in functions: `mock_service_cls` not `MockService`
   - This applies to mock class variables in tests

3. **Ruff line limit is 88 characters**
   - Not 79 (PEP 8) or 120 (common alternative)
   - Pre-commit hooks will reject lines longer than 88 chars

4. **`python-multipart` dependency required**
   - Admin router uses `UploadFile` which needs this package
   - Missing dependency causes cryptic import errors

5. **AsyncMock for async methods**
   - Use `AsyncMock()` not `MagicMock()` for async functions
   - Otherwise `await mock_function()` will fail

### Frontend

1. **React Query cache management**
   - Always set `gcTime: 0` in test QueryClient to prevent cache leaks
   - Cached data from one test can affect subsequent tests

2. **Clear mocks between tests**
   - Always call `vi.clearAllMocks()` in `beforeEach`
   - Prevents mock state from leaking between tests

3. **Async rendering issues**
   - Use `waitFor` for any assertion that depends on async data
   - Don't assume data is immediately available after render

4. **Mock implementation location**
   - Mock at the import location, not the definition location
   - Example: Mock `@/lib/api` not the internal fetch implementation

5. **Snapshot testing gotchas**
   - Snapshots capture implementation details, making refactoring harder
   - Prefer explicit assertions over snapshots for critical functionality

## Manual QA

For visual and functional verification of features, especially Phase 3 intelligence surfaces, refer to:

- **`QA_PHASE3_CHECKLIST.md`** - Comprehensive checklist for Phase 3 features including:
  - Meta comparison interface
  - Forecast trends and predictions
  - Tech card insights and analysis
  - Visual layout and responsiveness
  - Data accuracy and edge cases

Manual QA should be performed:

- After significant UI changes
- Before major releases
- When integration tests pass but visual verification is needed
- For features that are difficult to test automatically (charts, animations, layouts)

## CI/CD

### GitHub Actions

All tests run automatically on push and pull request:

1. **Backend Tests** (`pytest`)
   - Runs full test suite with coverage
   - Uploads coverage report as artifact
   - Fails PR if tests fail or coverage drops

2. **Frontend Tests** (`vitest`)
   - Runs all component and integration tests
   - Generates coverage report
   - Uploads coverage as artifact

3. **Pre-commit Checks**
   - Ruff linting and formatting (88 char limit)
   - Type checking with `ty`
   - Prettier formatting
   - TypeScript type checking

### Coverage Requirements

- Backend: Aim for 80%+ coverage on new code
- Frontend: Aim for 75%+ coverage on new components
- Critical paths (auth, payment, data processing) should have 90%+ coverage

### Viewing Coverage Reports

After CI runs, download coverage artifacts from the Actions tab:

```bash
# Backend coverage
cd apps/api
uv run pytest --cov --cov-report=html
open htmlcov/index.html

# Frontend coverage
cd apps/web
pnpm test:coverage
open coverage/index.html
```

## Best Practices

1. **Write tests first (TDD)**
   - Define expected behavior before implementation
   - Catch edge cases early
   - Easier to refactor with confidence

2. **Test behavior, not implementation**
   - Focus on what the code does, not how it does it
   - Makes tests resilient to refactoring

3. **Keep tests isolated**
   - Each test should be independent
   - Don't rely on execution order
   - Clean up state in `beforeEach` / `afterEach`

4. **Use descriptive test names**
   - `test_get_meta_snapshot_returns_404_when_not_found`
   - Better than `test_meta_snapshot`

5. **Mock external dependencies**
   - Don't make real API calls in unit tests
   - Use integration scripts for end-to-end validation
   - Mock time/dates for consistent test results

6. **Test edge cases**
   - Empty lists, null values, missing fields
   - Boundary conditions (max/min values)
   - Error states and exceptions

7. **Keep tests fast**
   - Unit tests should run in milliseconds
   - Use mocks to avoid slow I/O
   - Reserve slow tests for integration layer

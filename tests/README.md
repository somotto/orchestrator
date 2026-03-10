# Testing Guide

## Prerequisites

```bash
pip install pytest pytest-cov requests
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ --cov=srcs --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_inventory.py -v
```

### Run specific test
```bash
pytest tests/test_inventory.py::TestInventoryAPI::test_create_movie -v
```

## Test Structure

- `conftest.py`: Shared fixtures and setup
- `test_inventory.py`: Inventory service tests
- `test_billing.py`: Billing service tests

## Notes

- Tests require the cluster to be running
- API must be accessible at http://localhost:3000
- Tests clean up after themselves

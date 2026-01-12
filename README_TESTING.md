# 🧪 WUT-WAY Integration Testing Guide

Comprehensive testing documentation for the WUT-WAY RAG Integration system.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Test Suite Overview](#test-suite-overview)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
  - [Bash Integration Tests](#bash-integration-tests)
  - [Python Unit/Integration Tests](#python-unitintegration-tests)
  - [Performance Benchmarks](#performance-benchmarks)
- [Test Scenarios](#test-scenarios)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🚀 Quick Start

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 3. Run quick integration test
chmod +x tests/integration_test.sh
./tests/integration_test.sh

# 4. Run Python test suite
pip install -r tests/requirements.txt
pytest tests/test_runner.py -v
```

---

## 📊 Test Suite Overview

### Test Files

| File | Purpose | Test Count | Duration |
|------|---------|------------|----------|
| `integration_test.sh` | Bash-based API integration tests | 15+ | ~30s |
| `test_runner.py` | Python pytest suite | 30+ | ~60s |
| `test_scenarios.json` | Test data repository | 40+ scenarios | - |
| `performance_benchmark.py` | Locust load testing | Configurable | Variable |

### Test Categories

```
📦 tests/
├── 🏥 Health Checks          (6 tests)
├── 🎯 Functional Tests        (10 tests)
├── 🔀 Integration Tests       (8 tests)
├── 🚨 Edge Cases              (8 tests)
├── ⚡ Performance Tests       (3 tests)
└── 🔑 Keyword Detection       (7 tests)
```

### Coverage Areas

- ✅ **Service Health**: Qdrant, WAY, WUT health checks
- ✅ **API Endpoints**: All WUT and WAY endpoints
- ✅ **Business Logic**: Classification, signal detection, decision engine
- ✅ **Data Flow**: End-to-end query processing
- ✅ **Error Handling**: Invalid inputs, edge cases
- ✅ **Performance**: Response times, load capacity
- ✅ **Internationalization**: English and Thai language support

---

## 🔧 Prerequisites

### System Requirements

```bash
# Required tools
- Docker & docker-compose (20.10+)
- Bash (4.0+)
- Python (3.9+)
- curl
- jq

# Check installations
docker --version
docker-compose --version
python3 --version
curl --version
jq --version
```

### Python Dependencies

Create `tests/requirements.txt`:

```txt
pytest>=7.4.0
requests>=2.31.0
locust>=2.15.0
python-dotenv>=1.0.0
```

Install dependencies:

```bash
pip install -r tests/requirements.txt
```

### Environment Setup

Create `.env` file in project root:

```bash
# Service URLs (default values)
WUT_URL=http://localhost:8001
WAY_URL=http://localhost:8000
QDRANT_URL=http://localhost:6333

# API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Test Configuration
REQUEST_TIMEOUT=10
MIN_CONFIDENCE=0.5
MAX_RESPONSE_TIME_MS=5000

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

## 🏃 Running Tests

### Bash Integration Tests

#### Run All Tests

```bash
chmod +x tests/integration_test.sh
./tests/integration_test.sh
```

#### Run Specific Service Tests

```bash
# Test WUT service only
./tests/integration_test.sh --service wut

# Test WAY service only
./tests/integration_test.sh --service way

# Test Qdrant only
./tests/integration_test.sh --service qdrant
```

#### Verbose Mode

```bash
./tests/integration_test.sh --verbose
```

#### Custom URLs

```bash
WUT_URL=http://production:8001 \
WAY_URL=http://production:8000 \
./tests/integration_test.sh
```

#### Output Files

```bash
tests/
├── integration_test.log      # Detailed test log
└── test_results.json         # Summary results (JSON)
```

**Example Results:**

```json
{
  "timestamp": "2026-01-13T00:00:00+07:00",
  "total": 15,
  "passed": 14,
  "failed": 1,
  "success_rate": 93.33,
  "service": "all",
  "log_file": "tests/integration_test.log"
}
```

---

### Python Unit/Integration Tests

#### Run All Tests

```bash
pytest tests/test_runner.py -v
```

#### Run Specific Test Classes

```bash
# Health checks only
pytest tests/test_runner.py::TestHealthChecks -v

# WUT service tests
pytest tests/test_runner.py::TestWUTService -v

# Integration tests
pytest tests/test_runner.py::TestIntegration -v

# Edge cases
pytest tests/test_runner.py::TestEdgeCases -v
```

#### Run Tests by Keyword

```bash
# All health tests
pytest tests/test_runner.py -k "health" -v

# All urgent detection tests
pytest tests/test_runner.py -k "urgent" -v

# All WUT tests
pytest tests/test_runner.py -k "wut" -v
```

#### Show Print Output

```bash
pytest tests/test_runner.py -v -s
```

#### Stop After First Failure

```bash
pytest tests/test_runner.py -v --maxfail=1
```

#### Generate HTML Report

```bash
pip install pytest-html
pytest tests/test_runner.py -v --html=tests/report.html --self-contained-html
```

#### Coverage Report

```bash
pip install pytest-cov
pytest tests/test_runner.py --cov=backend --cov-report=html
```

---

### Performance Benchmarks

#### Install Locust

```bash
pip install locust
```

#### Run with Web UI

```bash
locust -f tests/performance_benchmark.py --host=http://localhost:8001

# Then open: http://localhost:8089
```

#### Run Headless Mode

```bash
# 50 users, spawn 10/sec, run for 5 minutes
locust -f tests/performance_benchmark.py \
    --host=http://localhost:8001 \
    --users 50 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless
```

#### Generate HTML Report

```bash
locust -f tests/performance_benchmark.py \
    --host=http://localhost:8001 \
    --users 100 \
    --spawn-rate 20 \
    --run-time 10m \
    --headless \
    --html tests/performance_report.html
```

#### Performance Metrics

Locust tracks:
- **Response Times**: P50, P95, P99 percentiles
- **Request Rate**: Requests per second (RPS)
- **Failure Rate**: % of failed requests
- **Concurrent Users**: Active user count over time

**Expected Baseline Performance:**

| Metric | Target | Acceptable |
|--------|--------|------------|
| P50 Response Time | < 1000ms | < 2000ms |
| P95 Response Time | < 2500ms | < 4000ms |
| P99 Response Time | < 4000ms | < 6000ms |
| Success Rate | > 99% | > 95% |
| RPS (100 users) | > 20 | > 10 |

---

## 📝 Test Scenarios

### Scenario Structure

Test scenarios are defined in `tests/test_scenarios.json`:

```json
{
  "functional_tests": [...],
  "edge_cases": [...],
  "error_cases": [...],
  "performance_tests": [...],
  "keyword_detection_tests": [...],
  "department_classification_tests": [...]
}
```

### Adding New Scenarios

1. **Edit `test_scenarios.json`**:

```json
{
  "id": "F011",
  "name": "My new test scenario",
  "input": {
    "message": "Test query",
    "department": "IT",
    "trace_id": "test-f011"
  },
  "expected": {
    "action": "answer",
    "min_confidence": 0.7,
    "business_signals": {
      "has_action_keywords": false
    }
  }
}
```

2. **Scenarios are automatically used by**:
   - `performance_benchmark.py` for load testing
   - Manual testing via API clients

### Example Test Scenarios

#### Functional Test
```json
{
  "id": "F001",
  "input": {
    "message": "How do I reset my password?",
    "department": "IT"
  },
  "expected": {
    "action": "answer",
    "min_confidence": 0.7
  }
}
```

#### Urgent Detection
```json
{
  "id": "F004",
  "input": {
    "message": "URGENT: My computer crashed!",
    "department": "IT"
  },
  "expected": {
    "business_signals": {
      "has_urgent_keywords": true,
      "has_action_keywords": true
    }
  }
}
```

#### Error Case
```json
{
  "id": "ERR001",
  "input": {
    "department": "IT"
  },
  "expected": {
    "http_status": 422
  }
}
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Integration Tests

on:
  push:
    branches: [ way, main ]
  pull_request:
    branches: [ way, main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      
      - name: Start services
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          docker-compose up -d
          sleep 30  # Wait for services
      
      - name: Run Bash integration tests
        run: |
          chmod +x tests/integration_test.sh
          ./tests/integration_test.sh
      
      - name: Run Python tests
        run: |
          pytest tests/test_runner.py -v --html=tests/report.html
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            tests/integration_test.log
            tests/test_results.json
            tests/report.html
      
      - name: Stop services
        if: always()
        run: docker-compose down
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: integration-test
        name: Run Integration Tests
        entry: tests/integration_test.sh --service wut
        language: script
        pass_filenames: false
        always_run: true
```

Install:
```bash
pip install pre-commit
pre-commit install
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Services Not Healthy

**Problem**: Tests fail with connection errors

**Solution**:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs wut-backend
docker-compose logs way-backend
docker-compose logs qdrant

# Restart services
docker-compose restart
```

#### 2. Port Already in Use

**Problem**: `Error: Port 8001 already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>

# Or use different ports
WUT_PORT=8002 docker-compose up -d
```

#### 3. jq Not Found

**Problem**: `integration_test.sh: jq: command not found`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

#### 4. Python Tests Import Error

**Problem**: `ModuleNotFoundError: No module named 'requests'`

**Solution**:
```bash
pip install -r tests/requirements.txt
```

#### 5. Timeout Errors

**Problem**: Tests timeout waiting for response

**Solution**:
```bash
# Increase timeout
export REQUEST_TIMEOUT=30
pytest tests/test_runner.py -v

# Or in test file:
REQUEST_TIMEOUT = 30
```

#### 6. Gemini API Errors

**Problem**: `Error: Gemini API key invalid`

**Solution**:
```bash
# Set API key in .env
echo "GEMINI_API_KEY=your_key_here" >> .env

# Restart services
docker-compose down
docker-compose up -d
```

### Debug Mode

Enable debug logging:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart
docker-compose restart

# View debug logs
docker-compose logs -f wut-backend
```

### Test Isolation

Run tests in isolation:

```bash
# Clean docker environment
docker-compose down -v
docker system prune -f

# Fresh start
docker-compose up -d --build
```

---

## 🤝 Contributing

### Adding New Tests

1. **Add to `test_scenarios.json`**:
   - Choose appropriate category
   - Follow naming convention: `F###`, `E###`, `ERR###`, etc.
   - Include expected results

2. **Add to `test_runner.py`**:
   ```python
   def test_my_new_feature(self, wut_client, trace_id):
       """Test description."""
       payload = {...}
       response = wut_client.post(...)
       assert response.status_code == 200
   ```

3. **Add to `integration_test.sh`**:
   ```bash
   test_my_new_feature() {
       test_start "My new feature test"
       # ... test logic
   }
   ```

### Test Guidelines

- ✅ **DO**: Write clear test names
- ✅ **DO**: Use trace_id for debugging
- ✅ **DO**: Test both happy and error paths
- ✅ **DO**: Document expected behavior
- ❌ **DON'T**: Hard-code URLs (use environment variables)
- ❌ **DON'T**: Depend on test execution order
- ❌ **DON'T**: Leave commented-out tests

### Pull Request Checklist

- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Test scenarios documented
- [ ] No hard-coded values
- [ ] Updated this README if needed

---

## 📚 Additional Resources

- [Main README](README.md) - Project overview
- [Integration Guide](INTEGRATION.md) - WUT-WAY integration details
- [API Documentation](http://localhost:8001/docs) - Swagger/OpenAPI docs
- [Pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Thanat-Wut/Rag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Thanat-Wut/Rag/discussions)

---

**Last Updated**: 2026-01-13  
**Version**: 1.0.0  
**Maintainer**: WUT-WAY Integration Team

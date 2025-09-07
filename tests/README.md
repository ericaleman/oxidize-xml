# oxidize-xml Test Suite

This directory contains comprehensive tests for the oxidize-xml XML parser.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── README.md               # This file
├── fixtures/               # Test data and sample files
│   └── sample_files.py    # XML samples for testing
├── integration/           # Integration tests
│   ├── test_basic_functionality.py   # Core API functionality
│   └── test_error_handling.py        # Error handling tests
├── performance/          # Performance and benchmarking tests
│   ├── test_benchmarks.py           # Performance benchmarks
│   └── test_memory_usage.py         # Memory usage tests
└── unit/                # Unit tests
    └── test_edge_cases.py          # Edge cases and corner conditions
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Integration tests only
pytest tests/integration/

# Performance tests only (slow)
pytest -m benchmark tests/performance/

# Memory tests only
pytest tests/performance/test_memory_usage.py

# Error handling tests
pytest tests/integration/test_error_handling.py

# Edge case tests
pytest tests/unit/test_edge_cases.py
```

### Run Tests with Coverage
```bash
pytest --cov=oxidize_xml --cov-report=html
```

### Run Benchmarks
```bash
pytest --benchmark-only tests/performance/test_benchmarks.py
```

## Test Categories

### Integration Tests (`tests/integration/`)
- **test_basic_functionality.py**: Tests core API functions with real XML data
- **test_error_handling.py**: Tests error handling with malformed and invalid inputs

### Performance Tests (`tests/performance/`)
- **test_benchmarks.py**: Performance benchmarks and regression tests
- **test_memory_usage.py**: Memory usage monitoring and leak detection

### Unit Tests (`tests/unit/`)
- **test_edge_cases.py**: Edge cases, corner conditions, and unusual inputs

## Key Test Features

### Fixtures and Test Data
- **XML Generators**: Dynamic generation of large test files
- **Sample Files**: Real-world XML examples for testing
- **Memory Monitoring**: Built-in memory usage tracking
- **Temporary Files**: Automatic cleanup of test files

### Performance Testing
- **Benchmarking**: Automated performance regression detection
- **Memory Monitoring**: Real-time memory usage tracking
- **Scalability Tests**: Performance with varying data sizes
- **Throughput Measurement**: Records/second and MB/second metrics

### Error Testing
- **Malformed XML**: Various types of invalid XML
- **File System Errors**: Invalid paths, permissions, etc.
- **Memory Limits**: Very large files and deep nesting
- **Concurrent Access**: Multi-threaded scenarios

### Edge Cases
- **Unicode Support**: Multi-language content and emojis
- **Namespace Handling**: Various XML namespace scenarios  
- **CDATA Sections**: Complex CDATA content
- **Mixed Content**: Text and elements combined
- **Self-closing Tags**: Various self-closing formats

## Test Requirements

The test suite requires these packages:
- `pytest`: Test framework
- `pytest-benchmark`: Performance benchmarking
- `pytest-cov`: Coverage reporting
- `psutil`: System monitoring for memory tests
- `oxidize_xml`: The package being tested (built from source)

## Adding New Tests

### Test Organization
- Place integration tests in `tests/integration/`
- Place performance tests in `tests/performance/`
- Place unit tests in `tests/unit/`
- Add new fixtures to `tests/fixtures/`

### Test Naming
- File names: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Using Fixtures
```python
def test_example(xml_file, temp_dir, memory_monitor):
    # xml_file: Temporary XML file with sample data
    # temp_dir: Temporary directory for output files  
    # memory_monitor: Memory usage tracking
    pass
```

### Performance Tests
Mark performance tests with `@pytest.mark.benchmark`:

```python
@pytest.mark.benchmark
def test_performance_example():
    pass
```

### Memory Tests
Use the `memory_monitor` fixture for memory tracking:

```python
def test_memory_example(memory_monitor):
    baseline = memory_monitor.start_monitoring()
    # ... run test code ...
    stats = memory_monitor.get_stats()
    assert stats['increase'] < 100  # Less than 100MB increase
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=oxidize_xml --cov-report=xml
```

For performance regression detection:
```yaml
- name: Run benchmarks  
  run: |
    pytest --benchmark-only --benchmark-json=benchmark.json
```
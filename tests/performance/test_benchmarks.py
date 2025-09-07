"""
Performance regression tests and benchmarks for oxidize-xml.
"""
import pytest
import time
import json
import psutil
import os
from pathlib import Path


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_small_file_performance(self, benchmark, xml_file):
        """Benchmark performance with small files (< 1MB)."""
        import oxidize_xml
        
        def parse_small_file():
            return oxidize_xml.parse_xml_file_to_json_string(str(xml_file), "record")
        
        result = benchmark(parse_small_file)
        
        # Verify correctness
        lines = result.strip().split('\n')
        assert len(lines) == 2
        
        # Performance expectations (adjust based on actual performance)
        # benchmark.stats contains timing statistics, access via get method
        stats = getattr(benchmark, 'stats', None)
        if stats and hasattr(stats, 'mean'):
            assert stats.mean < 1.0  # Should complete in < 1 second
        # If no stats available, just verify the result is correct
    
    
    def test_medium_file_performance(self, benchmark, temp_dir, large_xml_generator):
        """Benchmark performance with medium files (1-10MB)."""
        import oxidize_xml
        
        # Create medium-sized file (~2MB)
        xml_content = large_xml_generator(num_records=5000, record_size='medium')
        xml_path = temp_dir / "medium.xml"
        xml_path.write_text(xml_content)
        
        def parse_medium_file():
            return oxidize_xml.parse_xml_file_to_json_string(str(xml_path), "record")
        
        result = benchmark(parse_medium_file)
        
        # Verify correctness
        lines = result.strip().split('\n')
        assert len(lines) == 5000
        
        # Performance expectations  
        stats = getattr(benchmark, 'stats', None)
        if stats and hasattr(stats, 'mean'):
            assert stats.mean < 5.0  # Should complete in < 5 seconds
    
    
    def test_large_file_performance(self, benchmark, temp_dir, large_xml_generator):
        """Benchmark performance with large files (10-100MB)."""
        import oxidize_xml
        
        # Create large file (~20MB)
        xml_content = large_xml_generator(num_records=20000, record_size='large')
        xml_path = temp_dir / "large.xml"
        xml_path.write_text(xml_content)
        
        def parse_large_file():
            output_path = temp_dir / "large_output.json"
            return oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path))
        
        count = benchmark(parse_large_file)
        assert count == 20000
        
        # Performance expectations for large files
        stats = getattr(benchmark, 'stats', None)
        if stats and hasattr(stats, 'mean'):
            assert stats.mean < 30.0  # Should complete in < 30 seconds
    
    
    def test_batch_size_performance_comparison(self, temp_dir, large_xml_generator):
        """Compare performance across different batch sizes."""
        import oxidize_xml
        
        # Create test file
        xml_content = large_xml_generator(num_records=10000, record_size='medium')
        xml_path = temp_dir / "batch_test.xml"
        xml_path.write_text(xml_content)
        
        batch_sizes = [100, 500, 1000, 2000, 5000]
        results = {}
        
        for batch_size in batch_sizes:
            output_path = temp_dir / f"batch_output_{batch_size}.json"
            
            start_time = time.time()
            count = oxidize_xml.parse_xml_file_to_json_file(
                str(xml_path), "record", str(output_path), batch_size=batch_size
            )
            end_time = time.time()
            
            results[batch_size] = {
                'time': end_time - start_time,
                'count': count
            }
            
            assert count == 10000
            
            # Clean up
            if output_path.exists():
                output_path.unlink()
        
        # Log results for analysis
        print("\nBatch Size Performance Results:")
        for batch_size, data in results.items():
            print(f"  Batch {batch_size}: {data['time']:.3f}s ({data['count']} records)")
        
        # All batch sizes should produce same count
        counts = [data['count'] for data in results.values()]
        assert all(c == counts[0] for c in counts)
    
    
    def test_memory_efficiency_during_parsing(self, temp_dir, large_xml_generator):
        """Test memory usage during parsing of large files."""
        import oxidize_xml
        
        # Create large file
        xml_content = large_xml_generator(num_records=15000, record_size='large')
        xml_path = temp_dir / "memory_test.xml"
        xml_path.write_text(xml_content)
        
        # Get current process
        process = psutil.Process()
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parse file and monitor memory
        output_path = temp_dir / "memory_output.json"
        
        start_time = time.time()
        count = oxidize_xml.parse_xml_file_to_json_file(
            str(xml_path), "record", str(output_path), batch_size=1000
        )
        end_time = time.time()
        
        # Measure peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        assert count == 15000
        
        print(f"\nMemory Usage Analysis:")
        print(f"  Baseline: {baseline_memory:.1f} MB")
        print(f"  Peak: {peak_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        print(f"  Parse time: {end_time - start_time:.3f}s")
        print(f"  Records/sec: {count / (end_time - start_time):.0f}")
        
        # Memory should not grow excessively (streaming should keep it bounded)
        # This is a rough threshold - adjust based on actual performance
        assert memory_increase < 500  # Should not use more than 500MB additional
    
    
    def test_throughput_measurement(self, temp_dir, large_xml_generator):
        """Measure parsing throughput (records/second, MB/second)."""
        import oxidize_xml
        
        # Create test file with known size
        xml_content = large_xml_generator(num_records=10000, record_size='medium')
        xml_path = temp_dir / "throughput_test.xml"
        xml_path.write_text(xml_content)
        
        # Get file size
        file_size_mb = xml_path.stat().st_size / 1024 / 1024
        
        # Parse and measure
        output_path = temp_dir / "throughput_output.json"
        
        start_time = time.time()
        count = oxidize_xml.parse_xml_file_to_json_file(
            str(xml_path), "record", str(output_path)
        )
        end_time = time.time()
        
        parse_time = end_time - start_time
        records_per_second = count / parse_time
        mb_per_second = file_size_mb / parse_time
        
        print(f"\nThroughput Analysis:")
        print(f"  File size: {file_size_mb:.1f} MB")
        print(f"  Records: {count}")
        print(f"  Parse time: {parse_time:.3f}s")
        print(f"  Records/sec: {records_per_second:.0f}")
        print(f"  MB/sec: {mb_per_second:.1f}")
        
        # Performance expectations (adjust based on hardware)
        assert records_per_second > 1000  # Should process > 1000 records/sec
        assert mb_per_second > 1.0        # Should process > 1 MB/sec
    
    
    def test_string_vs_file_performance_comparison(self, temp_dir, large_xml_generator):
        """Compare performance of string vs file operations."""
        import oxidize_xml
        
        # Create test data
        xml_content = large_xml_generator(num_records=5000, record_size='medium')
        xml_path = temp_dir / "comparison_test.xml"
        xml_path.write_text(xml_content)
        
        # Test file-to-string vs string-to-string
        start_time = time.time()
        result1 = oxidize_xml.parse_xml_file_to_json_string(str(xml_path), "record")
        file_to_string_time = time.time() - start_time
        
        start_time = time.time()
        result2 = oxidize_xml.parse_xml_string_to_json_string(xml_content, "record")
        string_to_string_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Test file-to-file vs string-to-file
        output_path1 = temp_dir / "file_output.json"
        output_path2 = temp_dir / "string_output.json"
        
        start_time = time.time()
        count1 = oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path1))
        file_to_file_time = time.time() - start_time
        
        start_time = time.time()
        count2 = oxidize_xml.parse_xml_string_to_json_file(xml_content, "record", str(output_path2))
        string_to_file_time = time.time() - start_time
        
        assert count1 == count2
        
        print(f"\nPerformance Comparison:")
        print(f"  File->String: {file_to_string_time:.3f}s")
        print(f"  String->String: {string_to_string_time:.3f}s")
        print(f"  File->File: {file_to_file_time:.3f}s")
        print(f"  String->File: {string_to_file_time:.3f}s")
        
        # File operations might be slightly faster due to streaming
        # But differences should not be dramatic
        assert abs(file_to_string_time - string_to_string_time) < 2.0
        assert abs(file_to_file_time - string_to_file_time) < 2.0


@pytest.mark.benchmark
def test_performance_regression_threshold(temp_dir, large_xml_generator):
    """Test that performance hasn't regressed below acceptable thresholds."""
    import oxidize
    
    # Create standard test file
    xml_content = large_xml_generator(num_records=8000, record_size='medium')
    xml_path = temp_dir / "regression_test.xml"
    xml_path.write_text(xml_content)
    output_path = temp_dir / "regression_output.json"
    
    # Run multiple iterations for stability
    times = []
    for i in range(3):
        if output_path.exists():
            output_path.unlink()
        
        start_time = time.time()
        count = oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path))
        end_time = time.time()
        
        times.append(end_time - start_time)
        assert count == 8000
    
    avg_time = sum(times) / len(times)
    print(f"\nRegression Test Results:")
    print(f"  Individual times: {[f'{t:.3f}s' for t in times]}")
    print(f"  Average time: {avg_time:.3f}s")
    
    # Performance threshold - adjust based on expected performance
    # This should be set based on baseline measurements
    PERFORMANCE_THRESHOLD = 5.0  # seconds
    
    assert avg_time < PERFORMANCE_THRESHOLD, f"Performance regression detected: {avg_time:.3f}s > {PERFORMANCE_THRESHOLD}s"


@pytest.mark.benchmark
def test_scalability_with_record_count(temp_dir, large_xml_generator):
    """Test how performance scales with increasing record count."""
    import oxidize
    
    record_counts = [1000, 2000, 4000, 8000]
    results = {}
    
    for count in record_counts:
        xml_content = large_xml_generator(num_records=count, record_size='small')
        xml_path = temp_dir / f"scale_test_{count}.xml"
        xml_path.write_text(xml_content)
        output_path = temp_dir / f"scale_output_{count}.json"
        
        start_time = time.time()
        parsed_count = oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path))
        end_time = time.time()
        
        parse_time = end_time - start_time
        results[count] = {
            'time': parse_time,
            'rate': count / parse_time
        }
        
        assert parsed_count == count
        
        # Clean up
        xml_path.unlink()
        if output_path.exists():
            output_path.unlink()
    
    print(f"\nScalability Analysis:")
    for count, data in results.items():
        print(f"  {count} records: {data['time']:.3f}s ({data['rate']:.0f} rec/s)")
    
    # Performance should scale roughly linearly
    # Check that rate doesn't degrade significantly
    rates = [data['rate'] for data in results.values()]
    min_rate = min(rates)
    max_rate = max(rates)
    
    # Rate shouldn't vary by more than 50%
    rate_variance = (max_rate - min_rate) / max_rate
    assert rate_variance < 0.5, f"Performance scaling issue: rate variance {rate_variance:.2f}"
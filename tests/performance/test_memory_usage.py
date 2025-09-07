"""
Memory usage tests for oxidize-xml to ensure streaming behavior and prevent memory leaks.
"""
import pytest
import psutil
import os
import gc
import time
from pathlib import Path


class MemoryMonitor:
    """Helper class to monitor memory usage during tests."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline = None
        self.peak = None
        self.samples = []
    
    def start_monitoring(self):
        """Start memory monitoring."""
        gc.collect()  # Force garbage collection for cleaner baseline
        time.sleep(0.1)  # Allow GC to complete
        self.baseline = self.process.memory_info().rss / 1024 / 1024  # MB
        self.samples = []
        return self.baseline
    
    def sample(self):
        """Take a memory sample."""
        current = self.process.memory_info().rss / 1024 / 1024  # MB
        self.samples.append(current)
        if self.peak is None or current > self.peak:
            self.peak = current
        return current
    
    def get_stats(self):
        """Get memory usage statistics."""
        if not self.samples:
            return None
        
        return {
            'baseline': self.baseline,
            'peak': self.peak,
            'increase': self.peak - self.baseline if self.baseline else 0,
            'final': self.samples[-1],
            'samples': len(self.samples)
        }


@pytest.fixture
def memory_monitor():
    """Fixture to provide memory monitoring."""
    return MemoryMonitor()


def test_small_file_memory_usage(memory_monitor, xml_file):
    """Test memory usage with small files."""
    import oxidize_xml
    
    baseline = memory_monitor.start_monitoring()
    
    # Parse multiple times to check for memory leaks
    for i in range(10):
        result = oxidize_xml.parse_xml_file_to_json_string(str(xml_file), "record")
        memory_monitor.sample()
        
        # Verify result
        lines = result.strip().split('\n')
        assert len(lines) == 2
    
    stats = memory_monitor.get_stats()
    
    print(f"\nSmall File Memory Usage:")
    print(f"  Baseline: {stats['baseline']:.1f} MB")
    print(f"  Peak: {stats['peak']:.1f} MB")
    print(f"  Increase: {stats['increase']:.1f} MB")
    
    # Small files should not cause significant memory increase
    assert stats['increase'] < 50  # Less than 50MB increase


def test_large_file_streaming_memory(memory_monitor, temp_dir, large_xml_generator):
    """Test that large files are processed with bounded memory usage."""
    import oxidize_xml
    
    # Create large file (>50MB)
    xml_content = large_xml_generator(num_records=25000, record_size='large')
    xml_path = temp_dir / "large_memory_test.xml"
    xml_path.write_text(xml_content)
    
    file_size_mb = xml_path.stat().st_size / 1024 / 1024
    print(f"\nTesting file size: {file_size_mb:.1f} MB")
    
    baseline = memory_monitor.start_monitoring()
    output_path = temp_dir / "large_memory_output.json"
    
    # Parse large file
    count = oxidize_xml.parse_xml_file_to_json_file(
        str(xml_path), "record", str(output_path), batch_size=1000
    )
    
    memory_monitor.sample()
    stats = memory_monitor.get_stats()
    
    assert count == 25000
    
    print(f"\nLarge File Memory Usage:")
    print(f"  File size: {file_size_mb:.1f} MB")
    print(f"  Baseline: {stats['baseline']:.1f} MB")
    print(f"  Peak: {stats['peak']:.1f} MB")
    print(f"  Increase: {stats['increase']:.1f} MB")
    print(f"  Memory/File ratio: {stats['increase']/file_size_mb:.2f}")
    
    # Memory usage should be bounded and much less than file size
    # This is the key test for streaming behavior
    assert stats['increase'] < file_size_mb * 0.5  # Less than 50% of file size
    assert stats['increase'] < 1000  # Less than 1GB


def test_multiple_large_files_memory_stability(memory_monitor, temp_dir, large_xml_generator):
    """Test memory stability when processing multiple large files."""
    import oxidize_xml
    
    baseline = memory_monitor.start_monitoring()
    
    # Process multiple large files
    for i in range(5):
        xml_content = large_xml_generator(num_records=5000, record_size='large')
        xml_path = temp_dir / f"multi_large_{i}.xml"
        xml_path.write_text(xml_content)
        output_path = temp_dir / f"multi_large_output_{i}.json"
        
        count = oxidize_xml.parse_xml_file_to_json_file(
            str(xml_path), "record", str(output_path)
        )
        
        assert count == 5000
        memory_monitor.sample()
        
        # Clean up files to save disk space
        xml_path.unlink()
        if output_path.exists():
            output_path.unlink()
    
    stats = memory_monitor.get_stats()
    
    print(f"\nMultiple Files Memory Usage:")
    print(f"  Baseline: {stats['baseline']:.1f} MB")
    print(f"  Peak: {stats['peak']:.1f} MB")
    print(f"  Increase: {stats['increase']:.1f} MB")
    
    # Memory should not continuously grow with each file
    # Check that final memory is close to peak (no continuous growth)
    memory_growth_ratio = (stats['final'] - stats['baseline']) / (stats['peak'] - stats['baseline'])
    
    print(f"  Final memory ratio: {memory_growth_ratio:.2f}")
    
    assert stats['increase'] < 800  # Reasonable upper bound
    assert memory_growth_ratio < 1.2  # Final should be close to peak, not continuously growing


def test_memory_leak_detection(memory_monitor, temp_dir, large_xml_generator):
    """Test for memory leaks by processing many small files."""
    import oxidize_xml
    
    baseline = memory_monitor.start_monitoring()
    
    # Process many small files
    for i in range(50):
        xml_content = large_xml_generator(num_records=100, record_size='small')
        xml_path = temp_dir / f"leak_test_{i}.xml"
        xml_path.write_text(xml_content)
        output_path = temp_dir / f"leak_output_{i}.json"
        
        count = oxidize_xml.parse_xml_file_to_json_file(
            str(xml_path), "record", str(output_path)
        )
        
        assert count == 100
        
        if i % 10 == 0:  # Sample every 10 iterations
            memory_monitor.sample()
        
        # Clean up files
        xml_path.unlink()
        if output_path.exists():
            output_path.unlink()
    
    # Force garbage collection and take final sample
    gc.collect()
    time.sleep(0.1)
    final_memory = memory_monitor.sample()
    
    stats = memory_monitor.get_stats()
    
    print(f"\nMemory Leak Detection:")
    print(f"  Baseline: {stats['baseline']:.1f} MB")
    print(f"  Peak: {stats['peak']:.1f} MB")
    print(f"  Final: {stats['final']:.1f} MB")
    print(f"  Net increase: {stats['final'] - stats['baseline']:.1f} MB")
    
    # Final memory should be close to baseline (no significant leak)
    net_increase = stats['final'] - stats['baseline']
    assert net_increase < 100  # Less than 100MB net increase after processing 50 files


def test_string_vs_file_memory_comparison(memory_monitor, temp_dir, large_xml_generator):
    """Compare memory usage between string and file operations."""
    import oxidize_xml
    
    # Create test data
    xml_content = large_xml_generator(num_records=8000, record_size='medium')
    xml_path = temp_dir / "string_vs_file_test.xml"
    xml_path.write_text(xml_content)
    
    # Test file operations
    baseline1 = memory_monitor.start_monitoring()
    output_path = temp_dir / "file_op_output.json"
    
    count1 = oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path))
    memory_monitor.sample()
    file_op_stats = memory_monitor.get_stats()
    
    # Clean up and test string operations
    if output_path.exists():
        output_path.unlink()
    gc.collect()
    time.sleep(0.1)
    
    baseline2 = memory_monitor.start_monitoring()
    output_path = temp_dir / "string_op_output.json"
    
    count2 = oxidize_xml.parse_xml_string_to_json_file(xml_content, "record", str(output_path))
    memory_monitor.sample()
    string_op_stats = memory_monitor.get_stats()
    
    assert count1 == count2
    assert count1 == 8000
    
    print(f"\nString vs File Memory Comparison:")
    print(f"  File operations: {file_op_stats['increase']:.1f} MB")
    print(f"  String operations: {string_op_stats['increase']:.1f} MB")
    
    # String operations might use more memory (need to hold entire string)
    # But both should be reasonable
    assert file_op_stats['increase'] < 500
    assert string_op_stats['increase'] < 1000
    
    # Clean up
    if output_path.exists():
        output_path.unlink()


def test_concurrent_memory_usage(memory_monitor, temp_dir, large_xml_generator):
    """Test memory usage when multiple operations run concurrently."""
    import oxidize_xml
    import threading
    import time
    
    # Create test files
    xml_files = []
    for i in range(3):
        xml_content = large_xml_generator(num_records=3000, record_size='medium')
        xml_path = temp_dir / f"concurrent_{i}.xml"
        xml_path.write_text(xml_content)
        xml_files.append(xml_path)
    
    baseline = memory_monitor.start_monitoring()
    
    results = []
    errors = []
    
    def worker(worker_id, xml_path):
        try:
            output_path = temp_dir / f"concurrent_output_{worker_id}.json"
            count = oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "record", str(output_path))
            results.append((worker_id, count))
        except Exception as e:
            errors.append((worker_id, str(e)))
    
    # Start concurrent workers
    threads = []
    for i, xml_path in enumerate(xml_files):
        thread = threading.Thread(target=worker, args=(i, xml_path))
        threads.append(thread)
        thread.start()
    
    # Monitor memory during concurrent execution
    while any(thread.is_alive() for thread in threads):
        memory_monitor.sample()
        time.sleep(0.1)
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    memory_monitor.sample()
    stats = memory_monitor.get_stats()
    
    print(f"\nConcurrent Memory Usage:")
    print(f"  Baseline: {stats['baseline']:.1f} MB")
    print(f"  Peak: {stats['peak']:.1f} MB")
    print(f"  Increase: {stats['increase']:.1f} MB")
    print(f"  Successful workers: {len(results)}")
    print(f"  Errors: {len(errors)}")
    
    # Should have successful results
    assert len(results) > 0
    
    # Memory usage should be bounded even with concurrent operations
    assert stats['increase'] < 800  # Reasonable upper bound for 3 concurrent operations
    
    # Clean up
    for xml_path in xml_files:
        if xml_path.exists():
            xml_path.unlink()
    for i in range(len(xml_files)):
        output_path = temp_dir / f"concurrent_output_{i}.json"
        if output_path.exists():
            output_path.unlink()
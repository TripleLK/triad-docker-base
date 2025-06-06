# Triad Scientific Scraper: Step 6 Implementation Guide

This guide provides comprehensive documentation for the enhanced Triad Scientific scraper, focusing on the parallel processing capabilities, monitoring system, error handling, and resume functionality implemented in Step 6.

## Table of Contents

1. [Overview](#overview)
2. [New Command Line Options](#new-command-line-options)
3. [Parallel Processing](#parallel-processing)
4. [Monitoring and Reporting](#monitoring-and-reporting)
5. [Error Handling](#error-handling)
6. [Checkpoint and Resume Functionality](#checkpoint-and-resume-functionality)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

The Step 6 implementation enhances the Triad Scientific scraper with:

- **Parallel Processing**: Multi-threaded URL discovery and data extraction
- **Advanced Monitoring**: Real-time progress tracking and statistics
- **Improved Error Handling**: Comprehensive error detection, logging, and recovery
- **Checkpoint System**: Resume capability for interrupted operations
- **Documentation**: Detailed usage instructions and best practices

These enhancements make the scraper more efficient, reliable, and suitable for production deployment with large-scale imports.

## New Command Line Options

The following new command-line options have been added to the `import_triadscientific` management command:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--workers` | int | 4 | Number of worker threads for parallel processing |
| `--batch-size` | int | 10 | Number of items to process in a single batch |
| `--checkpoint-file` | string | 'triad_checkpoint.json' | File to save/resume progress |
| `--resume` | flag | - | Resume from the last checkpoint |
| `--stats-interval` | int | 60 | Interval in seconds for printing statistics |
| `--log-file` | string | 'triad_import.log' | Log file for detailed import information |

### Examples

```bash
# Basic parallel processing with 8 workers
python manage.py import_triadscientific --discover-urls --parent-page=3 --workers=8

# Resume a previously interrupted import
python manage.py import_triadscientific --url-file=urls.txt --parent-page=3 --resume

# Full import with parallel processing, custom logging, and more frequent stats
python manage.py import_triadscientific --discover-urls --parent-page=3 --workers=6 \
  --log-file=import_july2023.log --stats-interval=30 --checkpoint-file=july2023_checkpoint.json
```

## Parallel Processing

### URL Discovery

The parallel URL discovery process:

1. Fetches the main categories from the Triad Scientific homepage
2. Creates a thread pool with the specified number of workers
3. Distributes category URL processing across worker threads
4. Collects discovered product URLs from all categories
5. Provides real-time progress tracking with a progress bar

This approach significantly speeds up URL discovery, especially for sites with many category pages.

### Data Import

The parallel data import process:

1. Creates a task queue with all URLs to be processed
2. Initializes worker threads that:
   - Get a URL from the queue
   - Scrape and process the product data
   - Submit results to a result queue
3. The main thread collects results and updates statistics
4. Progress is displayed in real-time with a progress bar
5. Checkpoints are saved periodically

### Thread Management

The implementation uses:

- `ThreadPoolExecutor` for URL discovery
- Custom threading with queue for data import
- Thread synchronization with locks to prevent race conditions
- Signal handling for graceful shutdown

## Monitoring and Reporting

### Real-time Progress Tracking

The scraper provides real-time progress information:

- Progress bars showing completion percentage
- Periodic statistics reports at configurable intervals
- Time estimates for completion

### Statistics Reporting

The statistics report includes:

- Runtime duration
- URLs discovered and processed
- Success, failure, and skip counts
- Success rate percentage
- Processing rate (URLs/second)
- Recent errors (if any)

Example output:

```
Current Statistics Report:
Runtime: 1h 23m 45s
URLs discovered: 1240
URLs processed: 856
Successful imports: 798
Failed imports: 25
Skipped items: 33
Tags applied: 798
Success rate: 93.22%
Processing rate: 0.17 URLs/sec
```

### Logging System

The enhanced logging system:

- Sends detailed logs to a configurable log file
- Uses different log levels (INFO, WARNING, ERROR, DEBUG)
- Includes timestamps and context information
- Logs important events like import successes/failures, validation issues, etc.

## Error Handling

### Robust Exception Handling

The implementation includes:

- Comprehensive try/except blocks around critical operations
- Specific handling for different error types
- Detailed error logging with tracebacks
- Recovery mechanisms where appropriate

### Validation Improvements

Enhanced data validation:

- Validates product names, descriptions, models, and images
- Provides detailed validation error messages
- Logs validation failures for later analysis
- Implements graceful degradation for non-critical missing data

### Network Resilience

Network error handling includes:

- Session-level retry logic with configurable attempts and delays
- Connection pooling for efficiency
- Timeout handling
- Rate limiting to avoid overloading the source site

## Checkpoint and Resume Functionality

### Checkpoint System

The checkpoint system:

1. Periodically saves progress to a JSON file
2. Records:
   - Processed URLs
   - Current statistics
   - Timestamp
   - Total URLs to process

### Resume Capability

The resume functionality:

1. Loads the most recent checkpoint file
2. Filters out already processed URLs
3. Restores statistics counters
4. Continues processing from where it left off

This allows long-running imports to be safely interrupted and resumed later without duplicating work.

## Best Practices

### Resource Management

1. **Worker Count**: Set `--workers` based on available CPU cores and memory:
   - For most systems, use CPU count - 1 for best performance
   - For I/O-bound operations, you can use more workers than cores
   - For resource-constrained environments, reduce workers to 2-3

2. **Batch Size**: Adjust `--batch-size` based on system resources:
   - Larger batches (20-50) for modern systems with ample memory
   - Smaller batches (5-10) for limited resources

3. **Request Delay**: Set appropriate `--request-delay` to avoid overloading the source site:
   - 1 second is a reasonable default
   - Increase to 2-3 seconds for busy periods
   - Never use less than 0.5 seconds to avoid being blocked

### Monitoring Performance

1. **Stats Interval**: Adjust based on import size:
   - For small imports (< 100 URLs), use 30 seconds
   - For medium imports (100-1000 URLs), use 60 seconds
   - For large imports (> 1000 URLs), use 120-300 seconds

2. **Log File Management**:
   - Use descriptive log file names with dates
   - Implement log rotation for very large imports
   - Monitor log file size during operation

### Production Deployment

1. **Recommended Setup**:
   - Run as a scheduled task during off-hours
   - Use checkpoints for very large imports
   - Implement monitoring of the log file

2. **Resource Planning**:
   - Allocate sufficient disk space for images
   - Ensure database has appropriate indexes
   - Consider dedicated processing environment for large imports

## Troubleshooting

### Common Issues and Solutions

1. **Memory Usage Too High**:
   - Reduce number of workers (`--workers=2`)
   - Decrease batch size (`--batch-size=5`)
   - Process URLs in smaller groups using `--limit`

2. **Too Many Network Errors**:
   - Increase request delay (`--request-delay=2`)
   - Increase retry attempts (`--retry=5`)
   - Increase retry delay (`--retry-delay=10`)

3. **Process Too Slow**:
   - Increase number of workers if resources allow
   - Check network connection quality
   - Ensure database is properly indexed

4. **Checkpoint File Issues**:
   - Verify file permissions
   - Check disk space
   - Try using an absolute path for checkpoint file

### Diagnosing Problems

1. **Check Logs**:
   - Review the log file for error patterns
   - Look for recurring warnings or errors
   - Check timestamps to identify performance bottlenecks

2. **Analyze Failed URLs**:
   - Extract and test problematic URLs manually
   - Look for common patterns in failed URLs
   - Check if specific categories have higher failure rates

3. **Monitor System Resources**:
   - Check CPU usage during import
   - Monitor memory consumption
   - Watch disk I/O for image processing bottlenecks

---

This guide covers the essential aspects of the enhanced Triad Scientific scraper. For specific use cases or additional questions, please refer to the code comments or contact the development team. 
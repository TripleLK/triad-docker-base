#!/bin/bash

# Script to manage the Triad URL queue processing
# This provides a convenient wrapper around the Django management command

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
DJANGO_ROOT="$(dirname "$SCRIPT_DIR")"
QUEUE_FILE="$DJANGO_ROOT/triad_url_queue.json"
URL_FILE=""
BATCH_NAME="Triad Import $(date +'%Y-%m-%d %H:%M')"
DELAY="2.0"
SCRIPT_NAME=$(basename "$0")
SELECTORS_FILE="$SCRIPT_DIR/triad_selectors.json"  # Default selectors file location

# Function to display the help message
function show_help {
    echo "Usage: $SCRIPT_NAME [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status            Show the current queue status"
    echo "  load [file]       Load URLs from a file into the queue"
    echo "  process           Process the next URL in the queue"
    echo "  resume [n]        Resume processing the queue (optionally process n URLs)"
    echo ""
    echo "Options:"
    echo "  --queue FILE      Specify a custom queue file (default: $QUEUE_FILE)"
    echo "  --batch NAME      Specify a custom batch name"
    echo "  --delay SECONDS   Specify the delay between processing URLs (default: $DELAY)"
    echo "  --selectors FILE  Specify a JSON file with CSS selectors (default: $SELECTORS_FILE)"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $SCRIPT_NAME status"
    echo "  $SCRIPT_NAME load scripts/triad_product_urls.txt"
    echo "  $SCRIPT_NAME process"
    echo "  $SCRIPT_NAME resume    # Process 3 URLs by default"
    echo "  $SCRIPT_NAME resume 10 # Process 10 URLs then stop"
    echo "  $SCRIPT_NAME process --selectors scripts/triad_selectors.json"
    echo ""
}

# Function to run the Django command
function run_django_command {
    cd "$DJANGO_ROOT" || exit 1
    
    # Activate virtual environment if it exists
    if [ -f "envs/bin/activate" ]; then
        source "envs/bin/activate"
    fi
    
    # Run the Django command
    python manage.py process_url_queue "$@"
}

# Parse command-line options
COMMAND=""
LIMIT="3"  # Default to processing 3 URLs

while [[ $# -gt 0 ]]; do
    case $1 in
        status)
            COMMAND="status"
            shift
            ;;
        load)
            COMMAND="load"
            if [[ $2 && ! $2 == --* ]]; then
                URL_FILE="$2"
                shift
            fi
            shift
            ;;
        process)
            COMMAND="process"
            shift
            ;;
        resume)
            COMMAND="resume"
            if [[ $2 && ! $2 == --* && "$2" =~ ^[0-9]+$ ]]; then
                LIMIT="$2"
                shift
            fi
            shift
            ;;
        --queue)
            QUEUE_FILE="$2"
            shift 2
            ;;
        --batch)
            BATCH_NAME="$2"
            shift 2
            ;;
        --delay)
            DELAY="$2"
            shift 2
            ;;
        --selectors)
            SELECTORS_FILE="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set default command if none specified
if [ -z "$COMMAND" ]; then
    show_help
    exit 1
fi

# Read the selectors file if it exists
CSS_SELECTORS=""
if [ -f "$SELECTORS_FILE" ]; then
    CSS_SELECTORS=$(cat "$SELECTORS_FILE")
    echo "Using CSS selectors from $SELECTORS_FILE"
else
    echo "Warning: Selectors file $SELECTORS_FILE not found, using default selectors"
fi

# Build the command arguments
ARGS=()
ARGS+=("--queue-file" "$QUEUE_FILE")

# Execute the appropriate command
case $COMMAND in
    status)
        ARGS+=("--status")
        ;;
    load)
        if [ -z "$URL_FILE" ]; then
            echo "Error: No URL file specified"
            show_help
            exit 1
        fi
        ARGS+=("--urls-file" "$URL_FILE" "--batch-name" "$BATCH_NAME" "--delay" "$DELAY")
        if [ -n "$CSS_SELECTORS" ]; then
            ARGS+=("--css-selectors" "$CSS_SELECTORS")
        fi
        ;;
    process)
        ARGS+=("--process" "--delay" "$DELAY")
        if [ -n "$CSS_SELECTORS" ]; then
            ARGS+=("--css-selectors" "$CSS_SELECTORS")
        fi
        ;;
    resume)
        ARGS+=("--resume" "--delay" "$DELAY")
        # Always use the limit parameter with resume
        ARGS+=("--limit" "$LIMIT")
        if [ -n "$CSS_SELECTORS" ]; then
            ARGS+=("--css-selectors" "$CSS_SELECTORS")
        fi
        ;;
esac

# Run the command
run_django_command "${ARGS[@]}"
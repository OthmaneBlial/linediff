#!/bin/bash

# Interactive test script for linediff
# Tests different file types with all display modes

show_menu() {
    echo "Linediff Test Examples"
    echo "======================"
    echo ""
    echo "Available examples:"
    echo "1. Python code changes"
    echo "2. JavaScript code changes"
    echo "3. JSON configuration changes"
    echo "4. Text document changes"
    echo "5. Large file performance test"
    echo "0. Exit"
    echo ""
    echo -n "Choose an example (0-5): "
}

run_test() {
    local file1=$1
    local file2=$2
    local description=$3

    echo "Testing: $description"
    echo "Files: $file1 vs $file2"
    echo ""

    # Test unified diff
    echo "=== Unified Diff ==="
    PYTHONPATH=src python3 -m linediff --display unified "data/$file1" "data/$file2"

    echo ""
    echo "=== Side-by-Side Diff ==="
    PYTHONPATH=src python3 -m linediff --display side-by-side "data/$file1" "data/$file2"

    echo ""
    echo "=== Inline Diff ==="
    PYTHONPATH=src python3 -m linediff --display inline "data/$file1" "data/$file2"

    echo ""
    echo "Test completed!"
    echo ""
}

# Main menu loop
while true; do
    show_menu
    read -r choice
    echo ""

    case $choice in
        1)
            run_test "python_original.py" "python_modified.py" "Python Code Changes"
            ;;
        2)
            run_test "js_original.js" "js_modified.js" "JavaScript Code Changes"
            ;;
        3)
            run_test "config_original.json" "config_modified.json" "JSON Configuration Changes"
            ;;
        4)
            run_test "document_original.txt" "document_modified.txt" "Text Document Changes"
            ;;
        5)
            run_test "large_original.py" "large_modified.py" "Large File Performance Test"
            ;;
        0)
            echo "Goodbye! 👋"
            exit 0
            ;;
        *)
            echo "Invalid option. Please choose 0-5."
            echo ""
            ;;
    esac
done

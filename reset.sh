#!/bin/bash

# Check if bin/ exists and remove it
if [ -d "src/bin/" ]; then
    echo "Removing bin/ directory and its contents..."
    rm -rf src/bin/
fi

# Recreate bin/ directory
echo "Recreating bin/ directory..."
mkdir src/bin/

# Create an empty file named empty.txt inside bin/
echo "Creating empty.txt inside bin/..."
touch src/bin/empty.txt

echo "Cleaned up!"
echo "Starting server..."
docker run --rm -p 5234:5000 -v $(pwd)/src:/shared dotcoin flask --app dotcoin.py --debug run --host=0.0.0.0
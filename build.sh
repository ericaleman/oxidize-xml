#!/bin/bash

# Build oxidize-xml
cd oxidize-xml

if [[ "$1" == "--distribute" ]]; then
    cargo clean
    # Build wheel for distribution
    maturin build --release
    echo "Wheel built successfully"
else
    # Build for development
    maturin develop --release -v
    echo "oxidize-xml built successfully"
fi
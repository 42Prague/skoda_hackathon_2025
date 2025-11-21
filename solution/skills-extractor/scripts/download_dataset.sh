#!/bin/bash

# Script to download the Kaggle job descriptions dataset

set -e

echo "📥 Downloading Kaggle Job Descriptions Dataset..."
echo ""

# Check if kaggle CLI is installed
if ! command -v kaggle &> /dev/null; then
    echo "❌ Kaggle CLI not found. Installing..."
    pip install kaggle
fi

# Check if Kaggle credentials are configured
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "❌ Kaggle credentials not found!"
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://www.kaggle.com/settings"
    echo "2. Scroll down to 'API' section"
    echo "3. Click 'Create New API Token'"
    echo "4. Move the downloaded kaggle.json to ~/.kaggle/"
    echo "5. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Download the dataset
echo "⬇️  Downloading dataset..."
kaggle datasets download -d ravindrasinghrana/job-description-dataset -p data/

# Unzip the dataset
echo "📦 Extracting files..."
cd data
unzip -o job-description-dataset.zip
rm job-description-dataset.zip
cd ..

# List the downloaded files
echo ""
echo "✅ Dataset downloaded successfully!"
echo ""
echo "📁 Files in data/:"
ls -lh data/*.csv

echo ""
echo "🚀 Ready to run the pipeline!"
echo "   python scripts/cli.py pipeline --dataset data/job_descriptions.csv"

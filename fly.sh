#!/bin/bash
set -e

echo "🚀 Installing Fly CLI..."
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

echo "✅ Fly CLI installed. Checking version..."
fly version

echo "🌐 Logging in to Fly..."
fly auth login

# Array of services and their folders
declare -A SERVICES
SERVICES=( ["ed-dashboard"]="ed-dashboard" ["ed-]()

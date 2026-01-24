#!/bin/bash
# Setup script to configure git hooks for this repository

echo "Setting up git hooks..."

# Configure git to use the .githooks directory
git config core.hooksPath .githooks

# Make hooks executable
chmod +x .githooks/*

echo "✅ Git hooks configured successfully!"
echo ""
echo "The following hooks are now active:"
echo " - pre-push: Runs tests before allowing a push"
echo ""
echo "To bypass hooks during push (not recommended), use: git push --no-verify"

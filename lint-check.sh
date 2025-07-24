#!/bin/bash

echo "🔍 Running linting checks..."

# Frontend checks
echo "📦 Checking frontend..."
cd frontend
if ! npm run typecheck; then
    echo "❌ Frontend TypeScript check failed"
    exit 1
fi
echo "✅ Frontend checks passed"

# Backend checks  
echo "🐍 Checking backend..."
cd ../backend
if ! python -m black --check .; then
    echo "❌ Backend formatting check failed"
    echo "Run: python -m black . to fix"
    exit 1
fi
echo "✅ Backend checks passed"

echo "🎉 All linting checks passed!"
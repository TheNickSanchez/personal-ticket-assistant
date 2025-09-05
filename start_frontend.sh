#!/bin/bash
set -e

echo "🚀 Starting frontend server..."

# Start frontend
cd web/frontend
npm run dev

echo "Frontend started"

#!/bin/bash
set -e

echo ""=== ENTRYPOINT STARTED ===""

echo ""Running database migrations...""
flask db upgrade || echo ""Migration failed but continuing...""

echo ""Starting application...""
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 60 app:app
#!/bin/sh

alembic upgrade head

echo "Migrations complete!"

exec "$@"

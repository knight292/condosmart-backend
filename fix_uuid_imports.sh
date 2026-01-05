#!/bin/bash
# Script para corregir imports de UUID en todos los modelos
for file in app/models/*.py; do
    if grep -q "from sqlalchemy.dialects.postgresql import UUID" "$file"; then
        sed -i 's/from sqlalchemy.dialects.postgresql import UUID/from sqlalchemy.dialects.postgresql import UUID as PostgresUUID\nfrom app.db import USE_SQLITE\nfrom sqlalchemy import String\nUUID = String(36) if USE_SQLITE else PostgresUUID(as_uuid=True)/' "$file"
        echo "Fixed: $file"
    fi
done

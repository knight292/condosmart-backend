#!/bin/bash
# Script que se ejecuta después del deploy
cd /var/app/current
source venv/bin/activate
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"

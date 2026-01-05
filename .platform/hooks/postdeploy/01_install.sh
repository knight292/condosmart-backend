#!/bin/bash
# Script post-deploy para instalar dependencias
cd /var/app/current
source /var/app/venv/*/bin/activate
pip install -r requirements.txt

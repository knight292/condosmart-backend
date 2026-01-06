#!/bin/bash

echo "🔍 Verificando configuración de PostgreSQL en Railway..."
echo ""

cd "$(dirname "$0")"

echo "📋 Obteniendo logs recientes de Railway..."
echo ""

# Obtener logs y buscar mensajes sobre la base de datos
railway logs --tail 200 2>&1 | grep -i -E "postgres|sqlite|database|base de datos|usando|advertencia|✅|⚠️" | head -20

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📋 Verificando variables de entorno..."
railway variables 2>&1 | grep -i "DATABASE" || echo "No se encontró DATABASE_URL en variables del servicio actual"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 Si ves '✅ Usando base de datos persistente' → PostgreSQL está configurado"
echo "💡 Si ves '⚠️ ADVERTENCIA CRÍTICA: SQLite' → Necesitas configurar PostgreSQL"
echo ""

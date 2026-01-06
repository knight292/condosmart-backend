#!/bin/bash

echo "🔧 Configurando PostgreSQL en Railway..."
echo ""

cd "$(dirname "$0")"

# Verificar si Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado"
    echo "Instala con: npm i -g @railway/cli"
    exit 1
fi

echo "📋 Paso 1: Verificando proyecto actual..."
railway status

echo ""
echo "📋 Paso 2: Verificando si ya existe PostgreSQL..."
railway variables get DATABASE_URL 2>&1 | head -5

echo ""
echo "📋 Paso 3: Creando base de datos PostgreSQL..."
echo "⚠️  Esto requiere interacción. Sigue las instrucciones en pantalla."
railway add --database postgres

echo ""
echo "📋 Paso 4: Obteniendo DATABASE_URL de PostgreSQL..."
# Obtener el DATABASE_URL del servicio PostgreSQL
POSTGRES_URL=$(railway variables get DATABASE_URL --service postgres 2>&1 | grep -i postgresql || echo "")

if [ -z "$POSTGRES_URL" ]; then
    echo "⚠️  No se pudo obtener DATABASE_URL automáticamente"
    echo "Por favor, cópialo manualmente desde Railway Dashboard:"
    echo "1. Ve a Railway → Tu proyecto → Servicio PostgreSQL → Variables"
    echo "2. Copia el valor de DATABASE_URL"
    echo "3. Ejecuta: railway variables set DATABASE_URL='tu-valor-aqui'"
else
    echo "✅ DATABASE_URL obtenido: ${POSTGRES_URL:0:50}..."
    echo ""
    echo "📋 Paso 5: Configurando DATABASE_URL en el servicio backend..."
    railway variables set DATABASE_URL="$POSTGRES_URL"
fi

echo ""
echo "✅ Configuración completada!"
echo "Verifica en Railway Dashboard que DATABASE_URL esté configurado correctamente"

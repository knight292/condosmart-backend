#!/bin/bash

echo "🔧 Configurando PostgreSQL en Railway..."
echo ""

cd "$(dirname "$0")"

# Paso 1: Obtener DATABASE_URL de PostgreSQL
echo "📋 Paso 1: Obteniendo DATABASE_URL de PostgreSQL..."
echo ""

# Intentar obtener el DATABASE_URL del servicio postgres
POSTGRES_URL=$(railway variables --service postgres -k 2>&1 | grep "DATABASE_URL=" | cut -d'=' -f2- | tr -d '"' || echo "")

if [ -z "$POSTGRES_URL" ]; then
    # Intentar otro método
    POSTGRES_URL=$(railway variables --service postgres --json 2>&1 | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('DATABASE_URL', ''))" 2>/dev/null || echo "")
fi

if [ -z "$POSTGRES_URL" ] || [[ ! "$POSTGRES_URL" == postgresql* ]]; then
    echo "⚠️  No se pudo obtener DATABASE_URL automáticamente"
    echo ""
    echo "📝 OBTÉN EL DATABASE_URL MANUALMENTE:"
    echo ""
    echo "1. En Railway Dashboard, haz clic en el servicio 'Postgres'"
    echo "2. Ve a la pestaña 'Variables'"
    echo "3. Busca 'DATABASE_URL'"
    echo "4. Copia TODO el valor (es largo)"
    echo "5. Ejecuta este comando reemplazando <VALOR> con lo que copiaste:"
    echo ""
    echo "   railway variables --set DATABASE_URL=\"<VALOR>\""
    echo ""
    exit 1
fi

echo "✅ DATABASE_URL obtenido: ${POSTGRES_URL:0:60}..."
echo ""

# Paso 2: Configurar en el servicio backend
echo "📋 Paso 2: Configurando DATABASE_URL en el servicio backend..."
echo ""

# Intentar configurar en el servicio principal (striking-intuition)
railway variables --set "DATABASE_URL=$POSTGRES_URL" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DATABASE_URL configurado exitosamente!"
    echo ""
    echo "🔄 Railway reiniciará automáticamente el servicio"
    echo "📋 Verifica en los logs que diga: '✅ Usando base de datos persistente'"
    echo ""
    echo "⏱️  Espera 1-2 minutos y verifica los logs"
else
    echo ""
    echo "⚠️  No se pudo configurar automáticamente"
    echo ""
    echo "📝 CONFIGURA MANUALMENTE:"
    echo ""
    echo "1. En Railway Dashboard, haz clic en el servicio 'striking-intuition'"
    echo "2. Ve a 'Variables'"
    echo "3. Busca o crea 'DATABASE_URL'"
    echo "4. Pega este valor:"
    echo ""
    echo "   $POSTGRES_URL"
    echo ""
fi

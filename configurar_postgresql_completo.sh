#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  CONFIGURAR POSTGRESQL EN RAILWAY - AUTOMÁTICO"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Verificar Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI no está instalado"
    echo "Instala con: npm i -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI encontrado: $(railway --version)"
echo ""

# Verificar proyecto
echo "📋 Verificando proyecto actual..."
railway status
echo ""

# Verificar si ya existe PostgreSQL
echo "📋 Verificando servicios existentes..."
SERVICES=$(railway service list 2>&1 || echo "")

if echo "$SERVICES" | grep -qi "postgres\|postgresql"; then
    echo "✅ PostgreSQL ya existe en el proyecto"
    POSTGRES_SERVICE=$(echo "$SERVICES" | grep -i "postgres" | head -1 | awk '{print $1}')
    echo "📋 Servicio PostgreSQL: $POSTGRES_SERVICE"
    
    echo ""
    echo "📋 Obteniendo DATABASE_URL de PostgreSQL..."
    POSTGRES_URL=$(railway variables --service "$POSTGRES_SERVICE" -k 2>&1 | grep "DATABASE_URL" | cut -d'=' -f2- | tr -d '"' || echo "")
    
    if [ -n "$POSTGRES_URL" ] && [[ "$POSTGRES_URL" == postgresql* ]]; then
        echo "✅ DATABASE_URL obtenido"
        echo ""
        echo "📋 Configurando DATABASE_URL en servicio backend..."
        
        # Obtener el servicio backend (el que no es postgres)
        BACKEND_SERVICE=$(railway service list 2>&1 | grep -v -i "postgres" | head -1 | awk '{print $1}' || echo "")
        
        if [ -n "$BACKEND_SERVICE" ]; then
            echo "📋 Servicio backend: $BACKEND_SERVICE"
            railway variables --service "$BACKEND_SERVICE" --set "DATABASE_URL=$POSTGRES_URL"
            echo ""
            echo "✅ DATABASE_URL configurado en el servicio backend"
            echo ""
            echo "🔄 Railway reiniciará automáticamente el servicio"
            echo "📋 Verifica en los logs que diga: '✅ Usando base de datos persistente'"
        else
            echo "⚠️  No se pudo identificar el servicio backend"
            echo "Configura manualmente:"
            echo "  railway variables --set DATABASE_URL=\"$POSTGRES_URL\""
        fi
    else
        echo "⚠️  No se pudo obtener DATABASE_URL automáticamente"
        echo ""
        echo "📝 INSTRUCCIONES MANUALES:"
        echo "1. Ve a Railway Dashboard → Tu proyecto → Servicio PostgreSQL"
        echo "2. Variables → Copia DATABASE_URL"
        echo "3. Ve a tu servicio backend → Variables"
        echo "4. Edita o crea DATABASE_URL con el valor copiado"
    fi
else
    echo "⚠️  PostgreSQL no existe. Creando..."
    echo ""
    echo "📝 Esto requiere interacción. Sigue estos pasos:"
    echo ""
    echo "1. Ejecuta: railway add"
    echo "2. Selecciona: Database"
    echo "3. Selecciona: PostgreSQL"
    echo "4. Luego ejecuta este script de nuevo para configurar DATABASE_URL"
    echo ""
    echo "O hazlo manualmente desde Railway Dashboard:"
    echo "1. Ve a https://railway.app"
    echo "2. Tu proyecto → + New → Database → Add PostgreSQL"
    echo "3. Luego ejecuta este script de nuevo"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"

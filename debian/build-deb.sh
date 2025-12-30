#!/bin/bash
# ============================================================================
# Script para construir el paquete Debian de litellm-puter
# ============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Construyendo paquete Debian litellm-puter${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ] || [ ! -d "litellm_puter" ]; then
    echo -e "${RED}Error: Ejecutar desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Verificar dependencias de construcción
echo -e "${YELLOW}Verificando dependencias de construcción...${NC}"
MISSING_DEPS=""

for dep in debhelper dh-python dpkg-dev; do
    if ! dpkg -l | grep -q "^ii  $dep"; then
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [ -n "$MISSING_DEPS" ]; then
    echo -e "${YELLOW}Instalando dependencias faltantes:$MISSING_DEPS${NC}"
    sudo apt-get update
    sudo apt-get install -y debhelper dh-python python3-all python3-setuptools dpkg-dev
fi

# Limpiar builds anteriores
echo -e "${YELLOW}Limpiando builds anteriores...${NC}"
rm -rf debian/.debhelper
rm -rf debian/litellm-puter
rm -rf debian/files
rm -rf debian/*.log
rm -rf debian/*.substvars
rm -f ../litellm-puter_*.deb
rm -f ../litellm-puter_*.changes
rm -f ../litellm-puter_*.buildinfo

# Construir el paquete
echo -e "${YELLOW}Construyendo paquete...${NC}"
dpkg-buildpackage -us -uc -b

# Verificar que se creó el paquete
if [ -f "../litellm-puter_"*".deb" ]; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}Paquete construido exitosamente!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${GREEN}Paquete generado:${NC}"
    ls -lh ../litellm-puter_*.deb
    echo ""
    echo -e "${YELLOW}Para instalar:${NC}"
    echo "  sudo dpkg -i ../litellm-puter_*.deb"
    echo "  sudo apt-get install -f  # Resolver dependencias"
    echo ""
    echo -e "${YELLOW}Para verificar:${NC}"
    echo "  dpkg -c ../litellm-puter_*.deb  # Ver contenido"
    echo "  dpkg -I ../litellm-puter_*.deb  # Ver información"
    echo ""
    echo -e "${YELLOW}Después de instalar:${NC}"
    echo "  1. Editar /etc/default/litellm-puter (agregar PUTER_API_KEY)"
    echo "  2. sudo systemctl start litellm-puter"
    echo "  3. sudo systemctl status litellm-puter"
    echo ""
else
    echo -e "${RED}Error: No se pudo construir el paquete${NC}"
    exit 1
fi

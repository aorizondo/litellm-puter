# LiteLLM-Puter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-1.80.10+-green.svg)](https://github.com/BerriAI/litellm)

Custom provider para LiteLLM que permite acceder a 488+ modelos de IA a través de la API unificada de [Puter.com](https://puter.com).

## 🌟 Características

- **488+ Modelos de IA**: Acceso a modelos de OpenAI, Anthropic, DeepSeek, xAI, Google, Meta y más
- **API Unificada**: Interfaz consistente para todos los proveedores
- **Custom Provider**: Integración nativa con LiteLLM
- **Docker Ready**: Despliegue fácil con Docker Compose
- **PostgreSQL**: Base de datos integrada con pgvector
- **Scraper Automático**: Obtención programática de tokens temporales para pruebas
- **Proxy Gateway**: Servidor proxy completo con autenticación

## 📋 Requisitos

### Sistema Base
- Python 3.10+
- PostgreSQL 15+ (con extensión pgvector)
- Google Chrome
- Xvfb (para entorno headless)

### Para Docker
- Docker 20.10+
- Docker Compose 2.0+

## 🚀 Instalación

### Opción 1: Docker (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/aorizondo/litellm-puter.git
cd litellm-puter

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu PUTER_API_KEY

# Iniciar servicios
docker-compose up -d

# Verificar estado
docker-compose ps
docker-compose logs -f litellm
```

El servidor estará disponible en `http://localhost:4000`

### Opción 2: Instalación Local

```bash
# Instalar dependencias del sistema (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install -y \
    python3.10 python3-pip \
    postgresql-15 postgresql-contrib \
    google-chrome-stable \
    xvfb xvfbwrapper

# Clonar repositorio
git clone https://github.com/aorizondo/litellm-puter.git
cd litellm-puter

# Instalar con Poetry
pip install poetry
poetry install

# O con pip
pip install -r requirements.txt
pip install -e .
```

### Opción 3: Paquete Debian

```bash
# Construir paquete
./debian/build-deb.sh

# Instalar
sudo dpkg -i litellm-puter_*.deb
sudo apt-get install -f  # Resolver dependencias

# Configurar
sudo nano /etc/litellm-puter/config.yaml
# Agregar PUTER_API_KEY en /etc/default/litellm-puter

# Iniciar servicio
sudo systemctl start litellm-puter
sudo systemctl enable litellm-puter
sudo systemctl status litellm-puter
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# API Key de Puter (REQUERIDO)
PUTER_API_KEY=your_puter_api_key_here

# PostgreSQL
POSTGRES_USER=litellm
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=litellm_db
DATABASE_URL=postgresql://litellm:password@localhost:5432/litellm_db

# LiteLLM
LITELLM_PORT=4000
LITELLM_MASTER_KEY=sk-1234

# Scraper (opcional)
USE_XVFB=1
DISPLAY=:99
```

### Obtener API Key de Puter

1. Visita [https://puter.com](https://puter.com)
2. Crea una cuenta o inicia sesión
3. Ve a Settings → Developer → API Keys
4. Genera una nueva API key
5. Copia la key y agrégala a tu `.env`

## 💻 Uso

### Como Biblioteca Python

```python
import os
from litellm_puter import setup_puter_provider
import litellm

# Configurar provider
os.environ["PUTER_API_KEY"] = "your_api_key"
setup_puter_provider()

# Usar cualquier modelo
response = litellm.completion(
    model="puter/openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Otros ejemplos
response = litellm.completion(
    model="puter/anthropic/claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)

response = litellm.completion(
    model="puter/deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Write a Python function"}]
)
```

### Como Servidor Proxy

```bash
# Iniciar servidor
litellm --config config.yaml --port 4000

# O con Docker
docker-compose up -d
```

Usar el proxy con OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-1234",  # LITELLM_MASTER_KEY
    base_url="http://localhost:4000"
)

response = client.chat.completions.create(
    model="puter/openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Formato de Modelos

```
puter/<provider>/<model-id>
```

Ejemplos:
- `puter/openai/gpt-4o`
- `puter/anthropic/claude-3-5-sonnet-20241022`
- `puter/deepseek/deepseek-chat`
- `puter/xai/grok-2-1212`
- `puter/google/gemini-2.0-flash-exp`

### Scraper de Tokens Temporales

Para pruebas sin API key:

```bash
# Ejecutar scraper
python -m litellm_puter.scraper

# Los tokens se guardan en token.txt
# Usar el primer token válido como PUTER_API_KEY
```

**Nota**: El scraper requiere Xvfb y Chrome. Usa proxies automáticamente si es necesario.

## 🏗️ Arquitectura

```
litellm-puter/
├── litellm_puter/          # Módulo principal
│   ├── __init__.py         # Inicialización del paquete
│   ├── provider.py         # Custom provider para LiteLLM
│   ├── models_cache.py     # Cache de modelos disponibles
│   └── scraper.py          # Scraper de tokens temporales
├── config.yaml             # Configuración de LiteLLM
├── docker-compose.yml      # Orquestación de servicios
├── Dockerfile              # Imagen de contenedor
├── entrypoint.sh           # Script de inicio
├── debian/                 # Tooling para paquete .deb
│   ├── control             # Metadatos del paquete
│   ├── postinst            # Script post-instalación
│   ├── prerm               # Script pre-desinstalación
│   ├── litellm-puter.service  # Servicio systemd
│   └── build-deb.sh        # Script de construcción
└── pyproject.toml          # Configuración de Poetry
```

### Componentes

1. **PuterHTTPHandler**: Intercepta peticiones HTTP y las transforma al formato de Puter
2. **PuterLLM**: Custom provider que se registra en LiteLLM
3. **models_cache**: Cache de modelos disponibles en Puter
4. **scraper**: Automatización con Playwright para obtener tokens

## 🐳 Docker

### Servicios

- **litellm**: Servidor proxy principal (puerto 4000)
- **db**: PostgreSQL 15 con pgvector

### Comandos Útiles

```bash
# Ver logs
docker-compose logs -f litellm
docker-compose logs -f db

# Reiniciar servicios
docker-compose restart litellm

# Reconstruir imagen
docker-compose build --no-cache litellm

# Limpiar todo
docker-compose down -v
```

### Recursos

El docker-compose está optimizado para VPS con recursos limitados:
- LiteLLM: 384MB RAM, 0.5 CPU
- PostgreSQL: 192MB RAM, 0.3 CPU

Ajusta según tus necesidades en `docker-compose.yml`.

## 📦 Paquete Debian

### Construcción

```bash
# Instalar dependencias de construcción
sudo apt-get install -y debhelper dh-python python3-all python3-setuptools

# Construir paquete
cd litellm-puter
./debian/build-deb.sh

# El paquete se genera en ../
ls -lh ../litellm-puter_*.deb
```

### Instalación

```bash
sudo dpkg -i litellm-puter_*.deb
sudo apt-get install -f
```

### Configuración Post-Instalación

```bash
# Editar configuración
sudo nano /etc/litellm-puter/config.yaml

# Agregar API key
sudo nano /etc/default/litellm-puter
# PUTER_API_KEY=your_key_here

# Iniciar servicio
sudo systemctl start litellm-puter
sudo systemctl enable litellm-puter
```

### Archivos Instalados

- `/usr/lib/python3/dist-packages/litellm_puter/` - Módulo Python
- `/etc/litellm-puter/config.yaml` - Configuración
- `/etc/default/litellm-puter` - Variables de entorno
- `/lib/systemd/system/litellm-puter.service` - Servicio systemd
- `/var/log/litellm-puter/` - Logs

## 🔧 Desarrollo

```bash
# Instalar dependencias de desarrollo
poetry install --with dev

# Ejecutar tests
poetry run pytest

# Formatear código
poetry run black litellm_puter/
poetry run ruff check litellm_puter/

# Type checking
poetry run mypy litellm_puter/
```

## 🐛 Troubleshooting

### Error: "PUTER_API_KEY environment variable is required"

```bash
# Verificar que la variable esté configurada
echo $PUTER_API_KEY

# Configurarla
export PUTER_API_KEY=your_key_here

# O en .env
echo "PUTER_API_KEY=your_key_here" >> .env
```

### Error: "Valid Puter API key is required"

Tu API key es inválida o ha expirado. Genera una nueva en [puter.com](https://puter.com).

### Error: "You have reached your AI usage limit"

Has alcanzado el límite de uso gratuito. Opciones:
1. Espera a que se renueve tu cuota
2. Usa el scraper para obtener tokens temporales
3. Actualiza tu plan en Puter

### Scraper no funciona

```bash
# Verificar Chrome
google-chrome --version

# Verificar Xvfb
which Xvfb

# Ejecutar con display virtual
export DISPLAY=:99
Xvfb :99 -screen 0 1280x1024x24 &
python -m litellm_puter.scraper
```

### PostgreSQL no conecta

```bash
# Verificar servicio
docker-compose ps db
docker-compose logs db

# Verificar conexión
docker-compose exec db psql -U litellm -d litellm_db -c "SELECT 1;"
```

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 🔗 Enlaces

- [Repositorio GitHub](https://github.com/aorizondo/litellm-puter)
- [Puter.com](https://puter.com)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [Documentación de Puter AI](https://docs.puter.com/ai)

## 📧 Soporte

- Issues: [GitHub Issues](https://github.com/aorizondo/litellm-puter/issues)
- Email: aorizondo@users.noreply.github.com

## ⭐ Agradecimientos

- [Puter Team](https://puter.com) por la API de IA
- [BerriAI](https://github.com/BerriAI) por LiteLLM
- Comunidad open source

---

**Nota**: Este proyecto no está afiliado oficialmente con Puter.com. Es un proyecto comunitario independiente.

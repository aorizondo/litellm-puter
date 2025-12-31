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

- Python 3.10+
- LiteLLM 1.80.10+
- API Key de Puter (obtener en [puter.com](https://puter.com))

### Opcional (para Docker)
- Docker 20.10+
- Docker Compose 2.0+

## 🚀 Instalación

### Opción 1: Instalación Local (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/aorizondo/litellm-puter.git
cd litellm-puter

# Instalar con pip
pip install -e .

# Configurar API key
export PUTER_API_KEY=your_api_key

# Iniciar servidor (ejecutar desde el directorio litellm-puter/)
litellm --config config.yaml
```

**Nota**: El comando `litellm --config config.yaml` debe ejecutarse desde el directorio que contiene tanto el módulo `litellm_puter/` como el archivo `config.yaml`.

### Opción 2: Docker

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

## ⚙️ Configuración

### Variables de Entorno

```bash
# API Key de Puter (REQUERIDO)
PUTER_API_KEY=your_puter_api_key_here

# LiteLLM (opcional)
LITELLM_MASTER_KEY=sk-1234  # Para autenticación del proxy
```

### Obtener API Key de Puter

1. Visita [https://puter.com](https://puter.com)
2. Crea una cuenta o inicia sesión
3. Ve a Settings → Developer → API Keys
4. Genera una nueva API key
5. Copia la key y agrégala a tu `.env`

## 💻 Uso

### ⚠️ Requisito Importante

**El módulo `litellm_puter` y el archivo `config.yaml` DEBEN estar en el mismo directorio** para el correcto funcionamiento del sistema.

### Como Servidor Proxy

```bash
# Configurar API key
export PUTER_API_KEY=your_api_key

# Iniciar servidor (OBLIGATORIO ejecutar desde el directorio que contiene litellm_puter/)
cd /path/to/litellm-puter
litellm --config config.yaml

# O especificar puerto
litellm --config config.yaml --port 4000

# O con Docker
docker-compose up -d
```

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

### Scraper de Tokens Temporales (Opcional)

Para pruebas sin API key, instala las dependencias adicionales:

```bash
# Instalar con soporte para scraper
pip install -e ".[scraper]"

# Ejecutar scraper
python -m litellm_puter.scraper

# Los tokens se guardan en token.txt
# Usar el primer token válido como PUTER_API_KEY
```

**Nota**: El scraper requiere Chrome instalado.

## 🏗️ Arquitectura

```
litellm-puter/
├── litellm_puter/          # Módulo principal (DEBE estar junto a config.yaml)
│   ├── __init__.py         # Inicialización del paquete
│   ├── provider.py         # Custom provider para LiteLLM
│   ├── models_cache.py     # Cache de modelos disponibles
│   └── scraper.py          # Scraper de tokens temporales
├── config.yaml             # Configuración de LiteLLM (OBLIGATORIO)
└── pyproject.toml          # Configuración del paquete
```

### Componentes

1. **PuterHTTPHandler**: Intercepta peticiones HTTP y las transforma al formato de Puter
2. **PuterLLM**: Custom provider que se registra en LiteLLM
3. **models_cache**: Cache de modelos disponibles en Puter
4. **scraper**: Automatización para obtener tokens temporales

### Estructura de Directorios Requerida

```
tu-proyecto/
├── litellm_puter/     # Módulo Python
└── config.yaml        # Archivo de configuración
```

**Importante**: Ejecuta `litellm --config config.yaml` desde el directorio que contiene ambos elementos.

## 🐳 Docker

### Comandos Útiles

```bash
# Ver logs
docker-compose logs -f litellm

# Reiniciar servicios
docker-compose restart litellm

# Reconstruir imagen
docker-compose build --no-cache litellm

# Limpiar todo
docker-compose down -v
```

## 🔧 Desarrollo

```bash
# Instalar con dependencias de desarrollo
pip install -e ".[scraper]"
pip install pytest pytest-asyncio black ruff mypy

# Ejecutar tests
pytest

# Formatear código
black litellm_puter/
ruff check litellm_puter/
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
2. Usa el scraper para obtener tokens temporales (requiere `pip install -e ".[scraper]"`)
3. Actualiza tu plan en Puter

### Scraper no funciona

```bash
# Instalar dependencias del scraper
pip install -e ".[scraper]"

# Verificar Chrome
google-chrome --version

# Ejecutar scraper
python -m litellm_puter.scraper
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

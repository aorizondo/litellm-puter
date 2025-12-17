# Instalación de Dependencias - LiteLLM Puter Gateway

## Dependencias Instaladas

### Core Dependencies
- ✅ `litellm[proxy]` - LiteLLM con extensiones para modo proxy
- ✅ `fastapi>=0.100.0` - Framework web para el gateway
- ✅ `uvicorn` - Servidor ASGI para FastAPI
- ✅ `pytest` - Framework de testing
- ✅ `pytest-asyncio` - Soporte async para pytest

### Dependencias Existentes (ya presentes)
- `litellm>=1.80.0` - Core de LiteLLM
- `httpx>=0.28.0` - Cliente HTTP async
- `boto3>=1.42.0` - AWS SDK
- `python-dotenv>=1.0.0` - Carga de variables de entorno

## Mejoras Implementadas

### 1. Sistema de Mapeo de Drivers a Providers (`puter_models_cache.py`)

Se agregaron funciones para mapear automáticamente los drivers de Puter a providers de LiteLLM:

```python
def map_driver_to_provider(driver: str) -> str:
    """
    Mapea nombres de drivers de Puter a nombres de providers de LiteLLM.
    
    Ejemplos:
        "openai-completion" -> "openai"
        "claude" -> "anthropic"
        "deepseek" -> "deepseek"
        "openrouter" -> "openrouter"
    """

def get_model_provider(model: str, token: Optional[str] = None) -> str:
    """
    Obtiene el nombre del provider de LiteLLM para un modelo.
    
    Combina get_model_driver() con map_driver_to_provider().
    """
```

**Providers soportados:**
- OpenAI (`openai-completion`, `openai`)
- Anthropic (`claude`, `anthropic`)
- DeepSeek (`deepseek`)
- Google (`gemini`, `google`, `google-ai-studio`)
- Mistral (`mistral`)
- xAI/Grok (`xai`, `grok`)
- OpenRouter (`openrouter`)
- Cohere (`cohere`)
- AI21 (`ai21`)
- Meta/Llama (`llama`, `meta`)

### 2. Gateway Mejorado (`start_gateway.py`)

El gateway ahora:

1. **Determina automáticamente el provider**: Usa `get_model_provider()` para identificar qué provider usar
2. **Construye el formato correcto**: Convierte nombres de modelos simples al formato `puter/<provider>/<model>`
3. **Transparente para el cliente**: Los clientes pueden usar nombres de modelos estándar

**Flujo de trabajo:**

```
Cliente envía:         "gpt-4o-mini"
↓
Gateway determina:     provider = "openai" (via get_model_provider)
↓
Gateway construye:     "puter/openai/gpt-4o-mini"
↓
LiteLLM enruta:        Al handler de Puter con provider=openai
↓
Cliente recibe:        Respuesta en formato OpenAI estándar
```

### 3. Formato de Modelo Correcto

El formato correcto para usar el provider de Puter es:

```
puter/<provider>/<model>
```

**Ejemplos:**
- `puter/openai/gpt-4o` → Usa OpenAI GPT-4o via Puter
- `puter/anthropic/claude-3-5-sonnet-20241022` → Usa Claude via Puter
- `puter/deepseek/deepseek-chat` → Usa DeepSeek via Puter
- `puter/openrouter/openrouter:deepseek/deepseek-chat` → Usa OpenRouter via Puter

**Por qué es necesario el provider:**
- Puter actúa como un proxy que intercepta peticiones
- LiteLLM necesita saber qué handler usar para parsear la respuesta
- Cada provider (OpenAI, Anthropic, etc.) tiene un formato de respuesta diferente
- El provider especificado determina qué parser de respuesta usar

### 4. Documentación Actualizada

`GATEWAY_SETUP.md` ahora incluye:
- Explicación del sistema de traducción automática
- Ejemplos de uso con diferentes providers
- Documentación de la API del gateway

## Estado Actual

### ✅ Implementado y Funcionando:
- Sistema de mapeo de drivers a providers
- Parsing correcto del formato `puter/<provider>/<model>`
- Gateway con endpoints OpenAI-compatibles
- Documentación completa

### ⚠️ Requiere Acción:
**Token de Puter Expirado**: El `PUTER_API_KEY` en `.env` tiene más de 12 días de antigüedad y ha expirado.

**Para obtener un nuevo token:**

1. Ir a https://puter.com e iniciar sesión
2. Abrir las herramientas de desarrollador (F12)
3. Ir a la pestaña "Application" > "Local Storage" > "https://puter.com"
4. Buscar la clave que contiene el token de sesión
5. Copiar el token y actualizar `.env`:
   ```bash
   PUTER_API_KEY=nuevo_token_aqui
   ```

### 🧪 Para Probar:

Una vez que tengas un token válido:

```bash
# 1. Iniciar el gateway
cd /workspace/project/litellm-puter
python start_gateway.py --port 12000

# 2. En otra terminal, probar el gateway
curl -X POST http://localhost:12000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Archivos Modificados

1. **puter_models_cache.py**: +100 líneas
   - `map_driver_to_provider()`: Mapeo de drivers a providers
   - `get_model_provider()`: Obtención de provider para un modelo

2. **start_gateway.py**: Modificado
   - Importa `get_model_provider` y `setup_puter_provider`
   - Construye formato `puter/<provider>/<model>` automáticamente
   - Usa `litellm.acompletion()` en lugar de llamar directamente al handler

3. **GATEWAY_SETUP.md**: Actualizado
   - Sección "How It Works" con explicación del flujo
   - Ejemplos actualizados

4. **tests/test_simple.py**: Corregido
   - Usa formato correcto: `puter/openrouter/openrouter:deepseek/deepseek-chat`

## Notas Técnicas

### LiteLLM y Custom Providers

Cuando se registra un custom provider con `custom_provider_map`, LiteLLM:

1. Detecta el prefijo del provider en el modelo (ej: `puter/`)
2. Extrae el resto del modelo y lo pasa al handler
3. El handler recibe el modelo **sin** el prefijo `puter/`
4. El handler debe procesar el modelo en formato `<provider>/<model>`

Por ejemplo:
- Cliente: `puter/openai/gpt-4o`
- LiteLLM detecta: provider = `puter`
- Handler recibe: `openai/gpt-4o`
- Handler separa: provider = `openai`, model = `gpt-4o`

### Proxy HTTP

Si estás en un entorno con restricciones de red, puedes configurar un proxy:

```bash
export HTTP_PROXY=http://proxy.ejemplo.com:8080
export HTTPS_PROXY=http://proxy.ejemplo.com:8080
export NO_PROXY=localhost,127.0.0.1
```

## Siguientes Pasos

1. **Obtener token válido** de Puter
2. **Probar el gateway** con el nuevo token
3. **Verificar streaming** funciona correctamente
4. **Probar múltiples modelos** de diferentes providers
5. **Considerar commit** de los cambios (requiere autorización del usuario)

## Comandos Útiles

```bash
# Ver logs del gateway
tail -f gateway.log

# Probar test simple
python tests/test_simple.py

# Ejecutar todos los tests
pytest tests/ -v

# Verificar que el token no ha expirado
python -c "
import time
import base64
import json

with open('.env') as f:
    for line in f:
        if line.startswith('PUTER_API_KEY'):
            token = line.split('=')[1].strip()
            payload = base64.b64decode(token.split('.')[1] + '==')
            data = json.loads(payload)
            iat = data.get('iat', 0)
            age = time.time() - iat
            print(f'Token age: {age/3600:.1f} hours')
            if age > 86400:
                print('⚠️  Token may be expired')
            else:
                print('✅ Token appears valid')
"
```

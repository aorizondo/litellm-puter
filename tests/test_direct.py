import os
import litellm
from puter_provider import PuterHTTPHandler
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar variables de entorno necesarias
os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"

# Verificar que la API key esté configurada
api_key = os.getenv("PUTER_API_KEY")
if not api_key:
    print("❌ Error: PUTER_API_KEY no está configurada")
    exit(1)

print(f"✅ PUTER_API_KEY configurada (longitud: {len(api_key)} caracteres)")
print("\n🚀 Realizando una petición de prueba a Puter AI usando HTTPHandler directamente...")

try:
    # Usar el HTTPHandler directamente sin Custom Provider
    # El formato del modelo debe ser "openrouter:deepseek/deepseek-chat" o "anthropic/claude-..."
    response = litellm.completion(
        client=PuterHTTPHandler(api_key=api_key),
        model="openrouter/openrouter:deepseek/deepseek-chat",
        api_key="None",  # No se usa pero es requerido
        messages=[{"role": "user", "content": "Responde solo con 'Hola' en español"}],
    )
    
    print("\n✅ Respuesta recibida exitosamente!")
    print(f"\nModelo: {response.model}")
    print(f"Contenido: {response.choices[0].message.content}")
    print(f"\nTokens usados:")
    print(f"  - Prompt: {response.usage.prompt_tokens}")
    print(f"  - Completion: {response.usage.completion_tokens}")
    print(f"  - Total: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

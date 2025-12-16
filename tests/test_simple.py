import os
import litellm
from puter_provider import puter_llm
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Verificar que la API key esté configurada
api_key = os.getenv("PUTER_API_KEY")
if not api_key:
    print("❌ Error: PUTER_API_KEY no está configurada")
    exit(1)

print(f"✅ PUTER_API_KEY configurada (longitud: {len(api_key)} caracteres)")

# Registrar el custom provider
litellm.custom_provider_map = [
    {"provider": "puter", "custom_handler": puter_llm}
]

print("\n🚀 Realizando una petición de prueba a Puter AI...")

try:
    # Hacer una petición simple
    response = litellm.completion(
        model="puter/openrouter:deepseek/deepseek-chat",
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

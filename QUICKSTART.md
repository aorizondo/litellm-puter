# 🚀 Quick Start - 3 Pasos para Empezar

## Paso 1: Obtén tu API Key de Puter

1. Ve a https://puter.com
2. Inicia sesión o crea una cuenta
3. Ve a **Settings → API Keys**
4. Haz clic en **"Create new API key"**
5. Copia tu API key

## Paso 2: Configura el Proyecto

```bash
cd litellm-puter

# Copia la plantilla de configuración
cp .env.example .env

# Edita .env y pega tu API key
nano .env
```

En el archivo `.env`:
```bash
PUTER_API_KEY=tu_api_key_aqui
```

## Paso 3: Ejecuta un Ejemplo

```bash
# Instala las dependencias si aún no lo has hecho
pip install -r requirements.txt

# Ejecuta el ejemplo básico
cd examples
python basic_usage.py
```

## 🎉 ¡Listo!

Si ves una respuesta del modelo, ¡todo funciona correctamente!

---

## 📖 Más Ejemplos

```bash
# Requests asíncronos
python async_usage.py

# Múltiples providers (OpenAI, Claude, etc.)
python multiple_providers.py

# Control fino con HTTP handler
python http_handler_usage.py
```

---

## 📚 Documentación Completa

Lee el **README.md** para información detallada sobre:
- Configuración avanzada
- API Reference
- Troubleshooting
- Todos los modelos soportados
- Y mucho más

---

## ❓ Necesitas Ayuda?

- **README.md** - Documentación completa
- **RESUMEN_FINAL.md** - Resumen en español
- **examples/** - Código de ejemplo ejecutable

---

**Versión:** 2.0.0  
**Estado:** ✅ Production-Ready

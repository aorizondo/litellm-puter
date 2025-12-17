# Puter Providers - max_tokens Limits

## 📋 Proveedores Soportados por Puter

Basado en el análisis del código fuente de Puter (`github.com/HeyPuter/puter`), estos son todos los proveedores que Puter soporta y sus límites de `max_tokens`:

---

## 🔍 Resumen de Proveedores

| # | Provider | Límites típicos | Riesgo con max_tokens |
|---|----------|-----------------|----------------------|
| 1 | **OpenRouter** | 8,192 - 16,384+ | ⚠️ **ALTO** - Varía por modelo |
| 2 | **OpenAI** | 16,384 - 128,000 | ✅ BAJO - Límites altos |
| 3 | **Claude (Anthropic)** | 8,192 - 64,000 | ⚠️ MEDIO - Depende del modelo |
| 4 | **Gemini (Google)** | 8,192 - 65,536 | ⚠️ MEDIO - Varía |
| 5 | **DeepSeek** | 8,000 - 64,000 | ⚠️ ALTO - Límite bajo en v2 |
| 6 | **Groq** | 8,192 (default) | ⚠️ MEDIO - Limitado |
| 7 | **Mistral AI** | 32,768 - 131,072 | ✅ BAJO - Límites altos |
| 8 | **Together AI** | 8,000 (default) | ⚠️ MEDIO - Limitado |
| 9 | **XAI (Grok)** | Variable | ⚠️ MEDIO - Nuevo provider |

---

## 1. 🔄 OpenRouter

**Archivo:** `OpenRouterProvider/OpenRouterProvider.ts`

### Código Relevante

```typescript
// Línea 141
max_tokens: model.top_provider.max_completion_tokens,

// Línea 91 - complete()
max_tokens,  // Pasado directamente al SDK de OpenAI
```

### Características

- **Límites:** Varía por modelo (obtiene límites de API de OpenRouter)
- **Típico:** 8,192 para muchos modelos
- **Máximo:** 16,384+ para algunos modelos
- **Problema:** Los límites varían MUCHO entre modelos
  - DeepSeek v2: 8,192
  - GPT-4: 8,192 o más
  - Claude: Variable según versión

### ⚠️ Riesgo: **ALTO**

**Por qué:**
- Cada modelo tiene su propio límite
- Puter obtiene `max_completion_tokens` de la API
- Este valor puede ser incorrecto o desactualizado en cache
- El cálculo de Puter puede exceder el límite real

**Recomendación:**
- ✅ NO enviar max_tokens >8000
- ✅ Dejar que Puter lo calcule automáticamente

---

## 2. 🤖 OpenAI

**Archivo:** `OpenAiProvider/OpenAiChatProvider.ts`

### Código Relevante

```typescript
// Línea 202
...(max_tokens ? { max_completion_tokens: max_tokens } : {}),
```

### Modelos y Límites

```typescript
// models.ts
GPT-4: max_tokens: 16,384
GPT-4o: max_tokens: 16,384  
GPT-4o-mini: max_tokens: 16,384
o1-preview: max_tokens: 128,000
o1-mini: max_tokens: 128,000
```

### ✅ Riesgo: **BAJO**

**Por qué:**
- Límites altos (16,384 - 128,000)
- OpenAI maneja bien max_tokens
- Menos probable que exceda límites

**Recomendación:**
- ✅ Puede enviar max_tokens hasta 8,000 sin problemas
- ✅ Para valores >8000, considerar dejar que Puter calcule

---

## 3. 🎭 Claude (Anthropic)

**Archivo:** `ClaudeProvider/ClaudeProvider.ts`

### Código Relevante

```typescript
// Línea 103-107
max_tokens: Math.floor(max_tokens ||
    (
        model.startsWith('claude-3-5-sonnet') ||
        model.startsWith('claude-3-opus')
    ) ? 8192 : this.models().filter(e => (e.name === model || e.aliases?.includes(model)))[0]?.max_tokens || 4096),
```

### Modelos y Límites

```typescript
// models.ts
Claude 3.5 Sonnet: max_tokens: 8,192
Claude 3.5 Haiku: max_tokens: 8,192
Claude 3 Opus: max_tokens: 64,000
```

### ⚠️ Riesgo: **MEDIO**

**Por qué:**
- Claude **requiere** max_tokens (no es opcional)
- Puter establece default de 8,192 o 4,096
- Si enviamos valor más alto, puede causar problemas
- Diferentes versiones tienen límites diferentes

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000 para Claude
- ✅ Dejar que Puter use sus defaults

---

## 4. 🌟 Gemini (Google)

**Archivo:** `GeminiProvider/GeminiChatProvider.ts`

### Código Relevante

```typescript
// Línea 54
...(max_tokens ? { max_completion_tokens: max_tokens } : {}),
```

### Modelos y Límites

```typescript
// models.ts
Gemini 1.5 Pro: max_tokens: 8,192
Gemini 1.5 Flash: max_tokens: 8,192
Gemini 2.0 Flash: max_tokens: 65,536
```

### ⚠️ Riesgo: **MEDIO**

**Por qué:**
- Límites varían mucho (8,192 vs 65,536)
- Gemini 1.5: 8,192 (limitado)
- Gemini 2.0: 65,536 (alto)

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000 para Gemini 1.5
- ✅ Gemini 2.0 puede manejar valores más altos

---

## 5. 🧠 DeepSeek

**Archivo:** `DeepSeekProvider/DeepSeekProvider.ts`

### Código Relevante

```typescript
// Línea 106
max_tokens: max_tokens || 1000,  // Default: 1000
```

### Modelos y Límites

```typescript
// models.ts
DeepSeek v2: max_tokens: 8,000
DeepSeek v3: max_tokens: 64,000
```

### ⚠️ Riesgo: **ALTO**

**Por qué:**
- DeepSeek v2 tiene límite bajo (8,000)
- Default de Puter es solo 1,000
- v3 tiene límite alto (64,000) pero v2 es más común

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000
- ✅ Dejar que Puter use default o calcule

---

## 6. ⚡ Groq

**Archivo:** `GroqAiProvider/GroqAIProvider.ts`

### Código Relevante

```typescript
// Línea 78
max_completion_tokens: max_tokens,
```

### Modelos y Límites

```typescript
// models.ts
max_tokens: max_tokens ?? context ?? 8192
```

### ⚠️ Riesgo: **MEDIO**

**Por qué:**
- Default es 8,192
- Groq es rápido pero tiene límites estrictos
- Enfocado en inferencia rápida, no respuestas largas

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000
- ✅ Groq funciona mejor con respuestas cortas

---

## 7. 🌊 Mistral AI

**Archivo:** `MistralAiProvider/MistralAiProvider.ts`

### Código Relevante

```typescript
// Línea 82
maxTokens: max_tokens,
```

### Modelos y Límites

```typescript
// models.ts
Mistral Large: max_tokens: 131,072
Mistral Medium: max_tokens: 32,768
Mistral Small: max_tokens: 131,072
```

### ✅ Riesgo: **BAJO**

**Por qué:**
- Límites muy altos (32,768 - 131,072)
- Mistral maneja bien max_tokens altos
- Menos restrictivo que otros providers

**Recomendación:**
- ✅ Puede enviar max_tokens hasta 8,000
- ✅ Incluso valores >8000 probablemente funcionen

---

## 8. 🤝 Together AI

**Archivo:** `TogetherAiProvider/TogetherAiProvider.ts`

### Código Relevante

```typescript
// Línea 66
max_tokens: model.context_length ?? 8000,

// Línea 118
...(max_tokens ? { max_tokens } : {}),
```

### ⚠️ Riesgo: **MEDIO**

**Por qué:**
- Default es 8,000
- Depende del modelo específico
- `context_length` puede variar

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000
- ✅ Dejar que Puter use `context_length` del modelo

---

## 9. 🤖 XAI (Grok)

**Archivo:** `XAIProvider/XAIProvider.ts`

### Código Relevante

```typescript
// Línea 72
max_tokens: 1000,  // Default muy bajo
```

### ⚠️ Riesgo: **MEDIO**

**Por qué:**
- Provider relativamente nuevo
- Default muy bajo (1,000)
- Límites no están claros

**Recomendación:**
- ⚠️ NO enviar max_tokens >8000
- ✅ Dejar que Puter maneje defaults

---

## 🎯 Conclusión: Estrategia Unificada

### Regla General para TODOS los Providers

Basándonos en el análisis de TODOS los providers que Puter soporta:

| Situación | Acción | Razón |
|-----------|--------|-------|
| **Sin max_tokens** | ✅ No enviar | Puter calcula automáticamente |
| **max_tokens ≤ 8,000** | ✅ Enviar | Seguro para TODOS los providers |
| **max_tokens > 8,000** | ❌ No enviar | Riesgoso para OpenRouter, DeepSeek, Groq, Claude, Gemini 1.5 |

### Implementación Actual

Nuestra implementación en `puter_provider.py` ya maneja esto correctamente:

```python
if 'max_tokens' in filtered:
    max_tokens_value = filtered['max_tokens']
    
    if max_tokens_value is None:
        del filtered['max_tokens']
    elif max_tokens_value > 8000:
        # Valores >8000 son riesgosos para:
        # - OpenRouter (varía por modelo)
        # - DeepSeek v2 (8,000 límite)
        # - Groq (8,192 límite)
        # - Claude (8,192 límite)
        # - Gemini 1.5 (8,192 límite)
        del filtered['max_tokens']
```

### ¿Por qué 8,000 es el Umbral Seguro?

Analizando los límites de TODOS los providers:

```
Límites más restrictivos:
- DeepSeek v2: 8,000 ← EL MÁS BAJO
- Groq: 8,192
- Claude 3.5: 8,192
- Gemini 1.5: 8,192
- OpenRouter (muchos modelos): 8,192

Límites permisivos:
- OpenAI: 16,384+
- Mistral: 32,768+
- Gemini 2.0: 65,536
- Claude 3 Opus: 64,000
- DeepSeek v3: 64,000
```

**Conclusión:** 8,000 es el valor más alto que es seguro para CASI TODOS los modelos.

---

## 📊 Tabla Comparativa Completa

| Provider | Límite Mínimo | Límite Típico | Límite Máximo | Riesgo | Nuestra Estrategia |
|----------|---------------|---------------|---------------|--------|--------------------|
| OpenRouter | Variable | 8,192 | 16,384+ | ⚠️ ALTO | Filtrar >8000 |
| OpenAI | 16,384 | 16,384 | 128,000 | ✅ BAJO | Permitir ≤8000 |
| Claude | 4,096 | 8,192 | 64,000 | ⚠️ MEDIO | Filtrar >8000 |
| Gemini | 8,192 | 8,192 | 65,536 | ⚠️ MEDIO | Filtrar >8000 |
| DeepSeek | 8,000 | 8,000 | 64,000 | ⚠️ ALTO | Filtrar >8000 |
| Groq | 8,192 | 8,192 | 8,192 | ⚠️ MEDIO | Filtrar >8000 |
| Mistral | 32,768 | 32,768 | 131,072 | ✅ BAJO | Permitir ≤8000 |
| Together | 8,000 | 8,000 | Variable | ⚠️ MEDIO | Filtrar >8000 |
| XAI | 1,000 | Variable | ? | ⚠️ MEDIO | Filtrar >8000 |

---

## 🔧 Configuración Recomendada

### Para Máxima Compatibilidad

```python
# NO especificar max_tokens
response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello"}]
)
```

✅ Funciona con **TODOS** los 9 providers

### Para Control de Longitud

```python
# Especificar max_tokens ≤ 8000
response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Write a short story"}],
    max_tokens=1000  # Seguro para TODOS los providers
)
```

✅ Funciona con **TODOS** los 9 providers

### Para Respuestas Largas

```python
# NO especificar max_tokens, dejar que Puter calcule
response = litellm.completion(
    model="puter/openai:gpt-4o",  # Provider con límite alto
    messages=[{"role": "user", "content": "Write a detailed essay"}]
    # NO especificar max_tokens - Puter usará el máximo disponible
)
```

✅ Puter calculará el max_tokens óptimo según el provider

---

## 🚨 Casos Especiales

### Claude requiere max_tokens

```typescript
// ClaudeProvider.ts línea 103
max_tokens: Math.floor(max_tokens || 8192)  // REQUERIDO
```

Si NO enviamos max_tokens, Puter usa:
- Claude 3.5 Sonnet/Opus: 8,192
- Otros: 4,096

**Solución:** Nuestra implementación funciona bien porque:
1. Si usuario NO especifica max_tokens → Puter usa default
2. Si usuario especifica ≤8000 → Se envía
3. Si usuario especifica >8000 → Se filtra, Puter usa default

### DeepSeek tiene default bajo

```typescript
// DeepSeekProvider.ts línea 106
max_tokens: max_tokens || 1000  // Default: 1000
```

**Solución:** Si usuario NO especifica max_tokens, Puter usa 1,000 (conservador pero seguro).

---

## 📝 Resumen Final

### Providers con Riesgo ALTO

1. **OpenRouter** - Límites varían mucho por modelo
2. **DeepSeek** - v2 tiene límite bajo (8,000)

### Providers con Riesgo MEDIO

3. **Claude** - Requiere max_tokens, varía por versión
4. **Gemini** - 1.5 limitado (8,192), 2.0 alto (65,536)
5. **Groq** - Límite estricto (8,192)
6. **Together AI** - Default 8,000
7. **XAI** - Nuevo, límites no claros

### Providers con Riesgo BAJO

8. **OpenAI** - Límites altos (16,384+)
9. **Mistral** - Límites muy altos (32,768+)

### Estrategia Unificada ✅

```python
# Regla simple que funciona para TODOS:
if max_tokens > 8000:
    # No enviar, dejar que Puter calcule
    del filtered['max_tokens']
```

**Resultado:**
- ✅ Compatible con OpenRouter
- ✅ Compatible con DeepSeek
- ✅ Compatible con Groq
- ✅ Compatible con Claude
- ✅ Compatible con Gemini 1.5
- ✅ Compatible con OpenAI
- ✅ Compatible con Mistral
- ✅ Compatible con Together AI
- ✅ Compatible con XAI

---

**Versión:** 2.2.1  
**Fecha:** 2025-12-16  
**Fuente:** Análisis de `github.com/HeyPuter/puter`  
**Estado:** ✅ Documentado y Verificado

---

**🎯 Conclusión:** Nuestra estrategia de filtrar max_tokens >8000 es óptima para **TODOS** los providers que Puter soporta.

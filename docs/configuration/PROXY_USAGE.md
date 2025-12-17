# Uso de Proxy (Opcional)

## ¿Cuándo usar proxy?

El sistema de proxy está diseñado para situaciones donde el API de Puter está bloqueando tu dirección IP. Por defecto, **el proxy está DESHABILITADO** y no es necesario para el funcionamiento normal.

## Configuración

### 1. Habilitar proxy (solo si es necesario)

Edita tu archivo `.env`:

```bash
# Para habilitar proxy, descomenta estas líneas:
USE_PROXY=true
SOCKS5_PROXY=socks5://your.proxy.server:port
```

### 2. Para pruebas temporales

El archivo `.env` incluye un proxy público para pruebas:

```bash
# Para testing only - comment out after testing:
USE_PROXY=true
SOCKS5_PROXY=socks5://142.54.232.6:4145
```

**⚠️ IMPORTANTE**: Los proxies públicos son **temporales y poco confiables**. Úsalos solo para testing.

### 3. Para producción

Si necesitas proxy en producción, usa un servicio de proxy confiable:

```bash
USE_PROXY=true

# Opciones de proxy (prioridad en este orden):
SOCKS5_PROXY=socks5://your-socks-proxy:1080    # Preferido para bypass SSL
HTTPS_PROXY=https://your-https-proxy:8080      # Alternativa
HTTP_PROXY=http://your-http-proxy:8080         # Último recurso
```

## Deshabilitar proxy (comportamiento por defecto)

Para desactivar el proxy, simplemente comenta o elimina `USE_PROXY=true`:

```bash
# Proxy configuration (optional - for bypassing IP blocks)
# Set USE_PROXY=true to enable proxy usage
# Uncomment and configure for production if needed:
# USE_PROXY=true
# SOCKS5_PROXY=socks5://your.proxy.server:port
```

## Cómo funciona

1. **Sin proxy** (por defecto):
   - Las peticiones se hacen directamente a `api.puter.com`
   - Es el modo recomendado para la mayoría de casos

2. **Con proxy habilitado**:
   - Las peticiones HTTP/HTTPS pasan a través del proxy configurado
   - Para proxies SOCKS5, se desactiva la verificación SSL automáticamente
   - Útil cuando tu IP está bloqueada por el API de Puter

## Verificar si necesitas proxy

Prueba sin proxy primero:

```bash
# En .env, asegúrate de que USE_PROXY no esté configurado
# USE_PROXY=true  # <- comentado o eliminado

# Ejecuta el test
python tests/test_simple.py
```

Si ves errores **403 Forbidden** o **IP bloqueada**, entonces habilita el proxy.

## Proxies públicos gratuitos

Si necesitas un proxy temporal para pruebas, puedes consultar:

- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List) (actualizado cada 30 minutos)
- [proxy-list.download](https://www.proxy-list.download/)

**⚠️ ADVERTENCIA**: Los proxies públicos:
- Son lentos e inestables
- Pueden dejar de funcionar en cualquier momento
- NO son seguros para datos sensibles
- Solo deberían usarse para testing

## Solución de problemas

### Error: SSL certificate verification failed

Este error es normal con proxies SOCKS5. El código lo maneja automáticamente desactivando la verificación SSL cuando usas SOCKS5.

### El proxy no funciona

1. Verifica que el proxy esté activo: `curl --socks5 <proxy> https://api.puter.com/`
2. Prueba con otro proxy de la lista
3. Cambia de SOCKS5 a HTTP/HTTPS proxy

### Peticiones muy lentas

Los proxies públicos suelen ser lentos. Para producción, usa un servicio de proxy comercial.

## Recomendaciones

1. **Desarrollo local**: NO uses proxy (comportamiento por defecto)
2. **Testing en CI/CD**: Habilita proxy solo si CI tiene restricciones de IP
3. **Producción**: Usa proxy solo si tu servidor tiene IP bloqueada
4. **Servicios de proxy recomendados** (comerciales):
   - Bright Data (antes Luminati)
   - Smartproxy
   - Oxylabs
   - Your own VPS with Squid proxy

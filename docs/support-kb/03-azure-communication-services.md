# Azure Communication Services - Guía de Soporte

## Descripción General

Azure Communication Services (ACS) proporciona capacidades de comunicación en tiempo real para aplicaciones, incluyendo chat, voz, video, SMS y email.

## Servicios Disponibles

### 1. Email Service
- Envío de emails transaccionales
- Dominios verificados de Azure o personalizados
- Templates HTML personalizables
- Tracking de entregas

### 2. SMS Service
- Envío y recepción de SMS
- Números de teléfono toll-free y locales
- Short codes para campañas masivas
- Disponible en múltiples países

### 3. Chat Service
- Chat en tiempo real
- Hilos de conversación
- Indicadores de typing y lectura
- Historial persistente

### 4. Voice & Video
- Llamadas VoIP
- Videollamadas grupales
- Integración con PSTN
- Grabación de llamadas

## Configuración Inicial

### Crear Recurso ACS
```bash
az communication create \
    --name myacs \
    --resource-group myRG \
    --location global \
    --data-location Europe
```

### Configurar Email
1. Crear Email Communication Service
2. Agregar dominio (Azure Managed o propio)
3. Verificar registros DNS (SPF, DKIM, DMARC)
4. Conectar con el recurso ACS principal

## Problemas Comunes - Email

### Error: "Email domain not verified"
**Causa**: Registros DNS no configurados correctamente.
**Solución**:
1. Ir a Azure Portal > Email Communication Service
2. Copiar los registros DNS requeridos
3. Configurarlos en tu proveedor DNS
4. Esperar propagación (hasta 48h)
5. Verificar en el portal

### Error: "From address not allowed"
**Causa**: El remitente no está en el dominio verificado.
**Solución**:
1. Usar dirección del dominio verificado
2. Formato: `user@{dominio-verificado}`
3. Para dominio Azure: `DoNotReply@{guid}.azurecomm.net`

### Emails no llegan al destinatario
**Causa**: Posible bloqueo por spam o rebote.
**Solución**:
1. Verificar logs en Azure Portal
2. Comprobar si está en lista de supresión
3. Revisar contenido por palabras de spam
4. Configurar Event Grid para tracking

## Problemas Comunes - SMS

### Error: "Phone number not SMS enabled"
**Causa**: El número no tiene capacidad SMS.
**Solución**:
1. Verificar en Portal las capabilities del número
2. Comprar número con SMS habilitado
3. Usar número toll-free para USA/Canada

### SMS no entregados
**Causa**: Operador bloqueó el mensaje o número inválido.
**Solución**:
1. Verificar formato E.164 (+1234567890)
2. Comprobar delivery reports
3. Verificar que el país está soportado

## Precios

| Servicio | Precio (aprox.) |
|----------|----------------|
| Email | $0.00025 por email |
| SMS (USA) | $0.0075 por mensaje |
| Chat | $0.0008 por mensaje |
| Voice (PSTN) | Desde $0.004/min |

## Límites y Cuotas

- **Email**: 100 emails/minuto por defecto
- **SMS**: 1 mensaje/segundo por número
- **Chat**: 10,000 mensajes/minuto

Para aumentar límites: Abrir ticket de soporte en Azure Portal.

## Monitorización

### Métricas Disponibles
- Emails enviados/fallidos
- SMS delivery rate
- Latencia de chat
- Minutos de llamada

### Alertas Recomendadas
- Tasa de error > 5%
- Latencia > 500ms
- Cuota > 80%

## Integración con Agentes

ACS puede integrarse con Azure AI Agents mediante MCP (Model Context Protocol) para:
- Envío automático de notificaciones
- Confirmaciones de tickets
- Alertas de escalación
- Comunicación proactiva con usuarios

## Soporte

- **Documentación**: https://learn.microsoft.com/azure/communication-services
- **Samples**: https://github.com/Azure-Samples/communication-services-samples
- **Pricing**: https://azure.microsoft.com/pricing/details/communication-services

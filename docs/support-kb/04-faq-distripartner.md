# DistriPartner Platform - Preguntas Frecuentes (FAQ)

## General

### ¿Qué es DistriPartner Platform?
DistriPartner Platform es una solución de soporte automatizado que utiliza agentes de IA para proporcionar asistencia técnica a partners de Microsoft. La plataforma combina varios agentes especializados que trabajan juntos para resolver problemas y gestionar tickets de soporte.

### ¿Qué agentes componen la plataforma?
1. **Orchestrator**: Punto de entrada, enruta las conversaciones
2. **Support**: Soporte de nivel 1 con base de conocimiento
3. **Ticketing**: Creación y gestión de tickets
4. **Profiler**: Obtención de datos de usuario de EntraID
5. **DataCollector**: Consulta de datos de suscripciones
6. **Communication**: Envío de notificaciones por email
7. **CampaignManager**: Gestión de campañas de partners

### ¿Cómo inicio una conversación de soporte?
Simplemente envía un mensaje describiendo tu problema. El Orchestrator analizará tu solicitud y te conectará con el agente apropiado.

## Soporte Técnico

### ¿Qué tipos de problemas puede resolver el agente de Support?
- Preguntas sobre Azure, Microsoft 365, Dynamics
- Problemas de configuración
- Guías de troubleshooting
- Consultas sobre documentación
- Dudas sobre licenciamiento

### ¿Cuándo se crea un ticket?
Se crea un ticket automáticamente cuando:
- El problema no se puede resolver con la documentación
- Necesitas intervención humana
- El problema requiere acceso elevado
- Tú lo solicitas explícitamente

### ¿Cómo puedo hacer seguimiento de mi ticket?
El agente de Ticketing te proporcionará un número de referencia. También recibirás notificaciones por email con actualizaciones del estado.

## Cuenta y Perfil

### ¿Qué información se obtiene de mi perfil?
El agente Profiler puede obtener de EntraID:
- Nombre y email
- Organización
- Grupos y roles
- País y zona horaria

Esta información ayuda a personalizar el soporte.

### ¿Es segura mi información?
Sí. La plataforma:
- Usa Managed Identity de Azure
- No almacena credenciales
- Cumple con GDPR
- Solo accede a datos autorizados

## Suscripciones y Datos

### ¿Qué datos de suscripción se consultan?
El agente DataCollector puede obtener:
- Información de tenant
- Suscripciones activas
- Configuraciones de servicios
- Historial de tickets

### ¿De dónde vienen estos datos?
De CosmosDB, donde se almacena la información de partners de forma segura y cifrada.

## Notificaciones

### ¿Qué notificaciones recibiré?
- Confirmación de apertura de ticket
- Actualizaciones de estado
- Solicitud de información adicional
- Resolución de ticket

### ¿Puedo cambiar mis preferencias de notificación?
Contacta con soporte para modificar tus preferencias de email.

## Campañas (Partners)

### ¿Qué es el CampaignManager?
Es un agente que ayuda a partners a ejecutar campañas de marketing y ventas mediante automatización de PowerShell.

### ¿Qué puedo hacer con CampaignManager?
- Consultar campañas activas
- Ver estadísticas de rendimiento
- Ejecutar acciones automatizadas
- Obtener recomendaciones de mejora

## Troubleshooting

### El agente no responde
1. Verifica tu conexión a internet
2. Refresca la página
3. Intenta de nuevo en unos minutos
4. Si persiste, abre ticket manualmente

### Respuestas incorrectas o irrelevantes
1. Proporciona más contexto
2. Sé específico en tu pregunta
3. Menciona el producto exacto
4. Si el problema continúa, solicita escalación

### No puedo crear ticket
1. Verifica que tu cuenta está activa
2. Comprueba permisos en el portal
3. Intenta describir el problema de nuevo
4. Contacta administrador si persiste

## Límites del Servicio

| Aspecto | Límite |
|---------|--------|
| Mensajes por sesión | 50 |
| Tickets abiertos simultáneos | 5 |
| Archivos adjuntos | 10MB máx |
| Tiempo de sesión | 30 minutos |

## Contacto Humano

### ¿Cómo hablo con un humano?
Escribe "hablar con un agente humano" o "escalación" en cualquier momento. El sistema creará un ticket prioritario.

### Horario de soporte humano
- Lunes a Viernes: 9:00 - 18:00 (CET)
- Respuesta en tickets: 24 horas hábiles
- Emergencias: 24/7 para Severity 1

## Feedback

### ¿Cómo puedo dar feedback?
Al finalizar una conversación, podrás valorar la experiencia. Tu feedback nos ayuda a mejorar.

### ¿Dónde reporto bugs?
Abre un ticket con categoría "Bug Report" describiendo:
- Qué intentabas hacer
- Qué esperabas que pasara
- Qué pasó realmente
- Capturas de pantalla si es posible

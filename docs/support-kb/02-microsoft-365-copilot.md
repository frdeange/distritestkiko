# Microsoft 365 Copilot - Guía de Soporte

## ¿Qué es Microsoft 365 Copilot?

Microsoft 365 Copilot es un asistente de productividad impulsado por IA que se integra en las aplicaciones de Microsoft 365 como Word, Excel, PowerPoint, Outlook y Teams.

## Requisitos Previos

### Licenciamiento
- Licencia Microsoft 365 E3/E5 o Business Standard/Premium
- Licencia adicional de Microsoft 365 Copilot

### Configuración del Tenant
1. Activar Copilot en el Admin Center
2. Asignar licencias a usuarios
3. Configurar políticas de datos sensibles

## Funcionalidades por Aplicación

### Word con Copilot
- Redacción de documentos desde cero
- Resumen de documentos extensos
- Cambio de tono y estilo
- Generación de tablas y listas

### Excel con Copilot
- Análisis de datos naturales
- Creación de fórmulas complejas
- Generación de gráficos inteligentes
- Detección de tendencias

### PowerPoint con Copilot
- Creación de presentaciones desde prompt
- Diseño automático de diapositivas
- Resumen de presentaciones
- Sugerencias de imágenes

### Outlook con Copilot
- Redacción de correos
- Resumen de hilos largos
- Sugerencias de respuesta
- Organización de calendario

### Teams con Copilot
- Resumen de reuniones en tiempo real
- Generación de action items
- Transcripción automática
- Chat con historial de conversaciones

## Problemas Comunes

### Copilot no aparece en las aplicaciones
**Causa**: Licencia no asignada o propagación pendiente.
**Solución**:
1. Verificar asignación de licencia en Admin Center
2. Esperar hasta 24 horas para propagación
3. Cerrar sesión y volver a iniciar
4. Actualizar la aplicación de Office

### Copilot no tiene acceso a mis archivos
**Causa**: Permisos de Microsoft Graph insuficientes.
**Solución**:
1. Verificar que los archivos están en SharePoint/OneDrive
2. Comprobar permisos de compartición
3. Revisar políticas de DLP

### Respuestas genéricas o poco relevantes
**Causa**: Contexto insuficiente o datos desactualizados.
**Solución**:
1. Proporcionar más contexto en el prompt
2. Usar @menciones para referenciar archivos específicos
3. Actualizar el índice de búsqueda

## Mejores Prácticas

### Prompts Efectivos
- Ser específico sobre el resultado deseado
- Proporcionar ejemplos cuando sea posible
- Indicar el formato de salida esperado
- Usar lenguaje natural pero claro

### Seguridad de Datos
- Copilot respeta los permisos existentes
- No accede a datos sin autorización del usuario
- Los datos no se usan para entrenar modelos
- Cumplimiento con GDPR y regulaciones locales

## Escalación de Soporte

| Nivel | Tipo de Problema | Tiempo de Respuesta |
|-------|-----------------|---------------------|
| L1 | Configuración básica | Inmediato |
| L2 | Problemas de licencia | 4 horas |
| L3 | Bugs del producto | 24 horas |

## Recursos

- [Centro de Adopción de Copilot](https://adoption.microsoft.com/copilot)
- [Documentación técnica](https://learn.microsoft.com/microsoft-365-copilot)
- [Comunidad Tech](https://techcommunity.microsoft.com/t5/microsoft-365-copilot/ct-p/Microsoft365Copilot)

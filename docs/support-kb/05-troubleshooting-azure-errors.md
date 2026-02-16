# Troubleshooting de Errores Comunes en Azure

## Errores de Autenticación

### Error: "AADSTS50011: The reply URL specified does not match"
**Descripción**: La URL de callback no coincide con la configurada en la app registration.
**Solución**:
1. Ir a Azure Portal > App Registrations
2. Seleccionar la aplicación
3. En "Authentication", verificar Reply URLs
4. Añadir la URL exacta incluyendo protocolo y path

### Error: "AADSTS700016: Application not found in tenant"
**Descripción**: La aplicación no existe en el tenant o el Application ID es incorrecto.
**Solución**:
1. Verificar el Application (Client) ID
2. Comprobar que la app existe en el tenant correcto
3. Si es multi-tenant, verificar configuración en Manifest

### Error: "AADSTS7000218: Request body must contain client_secret"
**Descripción**: Falta el client secret en la autenticación.
**Solución**:
1. Generar nuevo client secret si expiró
2. Actualizar la configuración de la aplicación
3. Verificar que se envía en el body, no en headers

## Errores de Permisos

### Error: "Insufficient privileges to complete the operation"
**Descripción**: El usuario o service principal no tiene permisos suficientes.
**Solución**:
1. Verificar roles RBAC asignados
2. Añadir rol necesario (Reader, Contributor, Owner)
3. Para API permissions, dar admin consent

### Error: "Access denied to the specified resource"
**Descripción**: Sin acceso al recurso específico.
**Solución**:
1. Verificar que el recurso existe
2. Comprobar scope del token
3. Asignar acceso en IAM del recurso

## Errores de Red

### Error: "Connection timed out"
**Descripción**: No se puede establecer conexión con el servicio.
**Solución**:
1. Verificar firewall y NSG rules
2. Comprobar Private Endpoints si aplica
3. Verificar DNS resolution
4. Probar desde otra red/máquina

### Error: "SSL certificate problem"
**Descripción**: Problema con el certificado TLS/SSL.
**Solución**:
1. Verificar fecha de expiración del certificado
2. Comprobar cadena de certificación
3. Actualizar CA certificates del cliente

## Errores de Cuota

### Error: "QuotaExceeded"
**Descripción**: Se ha alcanzado el límite de cuota.
**Solución**:
1. Verificar uso actual en Azure Portal
2. Solicitar aumento de cuota
3. Optimizar recursos existentes
4. Considerar cambio de región

### Error: "TooManyRequests" (429)
**Descripción**: Rate limiting por exceso de peticiones.
**Solución**:
1. Implementar retry con exponential backoff
2. Reducir frecuencia de llamadas
3. Usar caching donde sea posible
4. Considerar tier superior

## Errores de Recursos

### Error: "ResourceNotFound" (404)
**Descripción**: El recurso no existe.
**Solución**:
1. Verificar nombre y grupo de recursos
2. Comprobar que no fue eliminado
3. Verificar la suscripción activa
4. Revisar el resource ID completo

### Error: "ResourceGroupNotFound"
**Descripción**: El grupo de recursos no existe.
**Solución**:
1. Crear el grupo de recursos
2. Verificar nombre exacto (case sensitive)
3. Comprobar suscripción

### Error: "DeploymentFailed"
**Descripción**: Fallo en el despliegue de recursos.
**Solución**:
1. Revisar Activity Log para detalles
2. Verificar dependencias
3. Comprobar naming conventions
4. Validar template antes de desplegar

## Errores de Storage

### Error: "BlobNotFound"
**Descripción**: El blob especificado no existe.
**Solución**:
1. Verificar nombre del contenedor y blob
2. Comprobar que no fue eliminado
3. Verificar permisos de lectura

### Error: "ContainerAlreadyExists"
**Descripción**: El contenedor ya existe.
**Solución**:
1. Usar nombre único
2. Manejar error en código (ignore if exists)
3. Verificar si se puede reusar el existente

## Errores de AI Services

### Error: "ModelNotFound"
**Descripción**: El modelo de IA no está desplegado.
**Solución**:
1. Verificar nombre del deployment
2. Comprobar estado del deployment
3. Verificar región del servicio

### Error: "ContentFilterError"
**Descripción**: El contenido fue filtrado por políticas.
**Solución**:
1. Revisar contenido del prompt
2. Ajustar content filtering settings
3. Reformular la petición

### Error: "ContextLengthExceeded"
**Descripción**: El prompt + respuesta excede el límite.
**Solución**:
1. Reducir tamaño del prompt
2. Usar modelo con mayor context window
3. Implementar chunking de documentos

## Comandos de Diagnóstico Útiles

```bash
# Verificar conectividad
az account show

# Listar recursos en un grupo
az resource list --resource-group <rg-name>

# Ver logs de actividad
az monitor activity-log list --resource-group <rg-name>

# Verificar quotas
az vm list-usage --location <region>

# Test de conectividad de red
az network watcher test-connectivity --source-resource <vm-id> --dest-address <url>
```

## Recursos de Ayuda

- [Azure Status](https://status.azure.com)
- [Azure Updates](https://azure.microsoft.com/updates)
- [Microsoft Q&A](https://learn.microsoft.com/answers)
- [Stack Overflow - Azure](https://stackoverflow.com/questions/tagged/azure)

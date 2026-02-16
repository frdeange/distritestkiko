# Azure AI Foundry - Guía Básica de Soporte

## ¿Qué es Azure AI Foundry?

Azure AI Foundry es la plataforma unificada de Microsoft para desarrollar, desplegar y gestionar aplicaciones de inteligencia artificial. Anteriormente conocido como Azure AI Studio, proporciona un entorno integrado para trabajar con modelos de IA generativa.

## Características Principales

### 1. Model Catalog
- Acceso a modelos de OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Modelos de código abierto (Llama, Mistral, Phi)
- Modelos de Microsoft (Florence, Phi-3)

### 2. Prompt Flow
- Diseño visual de flujos de IA
- Evaluación y testing de prompts
- Integración con Azure DevOps

### 3. Azure AI Search Integration
- Conexión nativa con índices de búsqueda
- RAG (Retrieval Augmented Generation)
- Grounding con datos empresariales

## Problemas Comunes y Soluciones

### Error: "Identity authorization component was unavailable"
**Causa**: Problema temporal del servicio de identidad de Azure.
**Solución**: 
1. Esperar 5-10 minutos y reintentar
2. Verificar que el Managed Identity está habilitado
3. Comprobar permisos RBAC en el recurso

### Error: "Model deployment not found"
**Causa**: El modelo no está desplegado o el nombre es incorrecto.
**Solución**:
1. Verificar el nombre del deployment en Azure Portal
2. Asegurarse de que el deployment está en estado "Succeeded"
3. Comprobar la región del proyecto

### Error: "Quota exceeded"
**Causa**: Se ha superado el límite de tokens por minuto (TPM).
**Solución**:
1. Reducir la frecuencia de llamadas
2. Solicitar aumento de cuota en Azure Portal
3. Usar un modelo con menor consumo de tokens

## Configuración Recomendada

### Para Desarrollo
```yaml
Deployment: gpt-4o-mini
SKU: Standard
Capacity: 10K TPM
```

### Para Producción
```yaml
Deployment: gpt-4o
SKU: GlobalStandard
Capacity: 50K TPM
Region: Sweden Central o East US 2
```

## Contacto de Soporte

- **Nivel 1 (L1)**: Agente de soporte automatizado
- **Nivel 2 (L2)**: Ticket de soporte técnico
- **Nivel 3 (L3)**: Escalación a Microsoft Support

## Recursos Adicionales

- [Documentación oficial](https://learn.microsoft.com/azure/ai-studio)
- [Precios](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
- [SLA](https://azure.microsoft.com/support/legal/sla/cognitive-services)

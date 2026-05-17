# Prompts de Sistema Personalizados

[English](../en/CUSTOM_SYSTEM_PROMPTS.md) | [简体中文](../zh-CN/CUSTOM_SYSTEM_PROMPTS.md) | [繁體中文](../zh-TW/CUSTOM_SYSTEM_PROMPTS.md) | [日本語](../ja/CUSTOM_SYSTEM_PROMPTS.md) | [한국어](../ko/CUSTOM_SYSTEM_PROMPTS.md) | [हिन्दी](../hi/CUSTOM_SYSTEM_PROMPTS.md) | [Tiếng Việt](../vi/CUSTOM_SYSTEM_PROMPTS.md) | [Français](../fr/CUSTOM_SYSTEM_PROMPTS.md) | [Русский](../ru/CUSTOM_SYSTEM_PROMPTS.md) | **Español** | [Português](../pt/CUSTOM_SYSTEM_PROMPTS.md) | [Norsk](../no/CUSTOM_SYSTEM_PROMPTS.md) | [Svenska](../sv/CUSTOM_SYSTEM_PROMPTS.md) | [Deutsch](../de/CUSTOM_SYSTEM_PROMPTS.md) | [Nederlands](../nl/CUSTOM_SYSTEM_PROMPTS.md) | [Italiano](../it/CUSTOM_SYSTEM_PROMPTS.md)

Esta guía explica cómo personalizar el prompt del sistema que GAC utiliza para generar mensajes de commit, permitiéndote definir tu propio estilo y convenciones de mensajes de commit.

## Tabla de Contenidos

- [Prompts de Sistema Personalizados](#prompts-de-sistema-personalizados)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [¿Qué Son los Prompts del Sistema?](#qué-son-los-prompts-del-sistema)
  - [¿Por Qué Usar Prompts de Sistema Personalizados?](#por-qué-usar-prompts-de-sistema-personalizados)
  - [Inicio Rápido](#inicio-rápido)
  - [Escribiendo tu Prompt de Sistema Personalizado](#escribiendo-tu-prompt-de-sistema-personalizado)
  - [Ejemplos](#ejemplos)
    - [Estilo de Commit Basado en Emojis](#estilo-de-commit-basado-en-emojis)
    - [Convenciones Específicas de Equipo](#convenciones-específicas-de-equipo)
    - [Estilo Técnico Detallado](#estilo-técnico-detallado)
  - [Mejores Prácticas](#mejores-prácticas)
    - [Haz:](#haz)
    - [No Hagas:](#no-hagas)
    - [Consejos:](#consejos)
  - [Solución de Problemas](#solución-de-problemas)
    - [Los mensajes aún tienen el prefijo "chore:"](#los-mensajes-aún-tienen-el-prefijo-chore)
    - [La IA ignora mis instrucciones](#la-ia-ignora-mis-instrucciones)
    - [Los mensajes son demasiado largos/cortos](#los-mensajes-son-demasiado-largoscortos)
    - [El prompt personalizado no se está usando](#el-prompt-personalizado-no-se-está-usando)
    - [Quiero volver al predeterminado](#quiero-volver-al-predeterminado)
  - [Documentación Relacionada](#documentación-relacionada)
  - [¿Necesitas Ayuda?](#necesitas-ayuda)

## ¿Qué Son los Prompts del Sistema?

GAC utiliza dos prompts al generar mensajes de commit:

1. **Prompt del Sistema** (personalizable): Instrucciones que definen el rol, estilo y convenciones para los mensajes de commit
2. **Prompt de Usuario** (automático): Los datos del diff de git que muestran qué cambió

El prompt del sistema le dice a la IA _cómo_ escribir mensajes de commit, mientras que el prompt de usuario proporciona el _qué_ (los cambios reales del código).

## ¿Por Qué Usar Prompts de Sistema Personalizados?

Podrías querer un prompt del sistema personalizado si:

- Tu equipo utiliza un estilo de mensaje de commit diferente a los commits convencionales
- Prefieres emojis, prefijos u otros formatos personalizados
- Quieres más o menos detalle en los mensajes de commit
- Tienes guías o plantillas específicas de la empresa
- Quieres que coincida con la voz y el tono de tu equipo
- Quieres mensajes de commit en un idioma diferente (ver Configuración de Idioma abajo)

## Inicio Rápido

1. **Crea tu archivo de prompt del sistema personalizado:**

   ```bash
   # Copia el ejemplo como punto de partida
   cp custom_system_prompt.example.txt ~/.config/gac/my_system_prompt.txt

   # O crea el tuyo desde cero
   vim ~/.config/gac/my_system_prompt.txt
   ```

2. **Añade a tu archivo `.gac.env`:**

   ```bash
   # En ~/.gac.env o .gac.env a nivel de proyecto
   GAC_SYSTEM_PROMPT_PATH=/ruta/a/tu/custom_system_prompt.txt
   ```

3. **Pruébalo:**

   ```bash
   uvx gac --dry-run
   ```

¡Eso es todo! GAC ahora utilizará tus instrucciones personalizadas en lugar de las predeterminadas.

## Escribiendo tu Prompt de Sistema Personalizado

Tu prompt del sistema personalizado puede ser texto plano—no se requiere formato especial o etiquetas XML. Simplemente escribe instrucciones claras sobre cómo la IA debería generar mensajes de commit.

**Cosas clave que incluir:**

1. **Definición del rol** - Qué debe hacer la IA
2. **Requisitos de formato** - Estructura, longitud, estilo
3. **Ejemplos** - Muestra cómo se ven los buenos mensajes de commit
4. **Restricciones** - Qué evitar o requisitos que cumplir

**Ejemplo de estructura:**

```text
Eres un escritor de mensajes de commit para [tu proyecto/equipo].

Al analizar cambios en el código, crea un mensaje de commit que:

1. [Primer requisito]
2. [Segundo requisito]
3. [Tercer requisito]

Formato de ejemplo:
[Muestra un ejemplo de mensaje de commit]

Tu respuesta completa se usará directamente como el mensaje de commit.
```

## Ejemplos

### Estilo de Commit Basado en Emojis

Ver [`custom_system_prompt.example.txt`](../../examples/custom_system_prompt.example.txt) para un ejemplo completo basado en emojis.

**Fragmento rápido:**

```text
Eres un escritor de mensajes de commit que usa emojis y un tono amigable.

Comienza cada mensaje con un emoji:
- 🎉 para nuevas características
- 🐛 para correcciones de errores
- 📝 para documentación
- ♻️ para refactorización

Mantén la primera línea bajo 72 caracteres y explica POR QUÉ importa el cambio.
```

### Convenciones Específicas de Equipo

```text
Estás escribiendo mensajes de commit para una aplicación bancaria empresarial.

Requisitos:
1. Comienza con un número de ticket de JIRA entre corchetes (ej., [BANK-1234])
2. Usa un tono formal y profesional
3. Incluye implicaciones de seguridad si son relevantes
4. Referencia cualquier requisito de cumplimiento (PCI-DSS, SOC2, etc.)
5. Mantén los mensajes concisos pero completos

Formato:
[TICKET-123] Resumen breve del cambio

Explicación detallada de qué cambió y por qué. Incluye:
- Justificación comercial
- Enfoque técnico
- Evaluación de riesgos (si aplica)

Ejemplo:
[BANK-1234] Implementar limitación de velocidad para endpoints de login

Añadida limitación de velocidad basada en Redis para prevenir ataques de fuerza bruta.
Limita intentos de login a 5 por IP cada 15 minutos.
Cumple con requisitos de seguridad SOC2 para control de acceso.
```

### Estilo Técnico Detallado

```text
Eres un escritor de mensajes de commit técnico que crea documentación integral.

Para cada commit, proporciona:

1. Un título claro y descriptivo (bajo 72 caracteres)
2. Una línea en blanco
3. QUÉ: Qué fue cambiado (2-3 oraciones)
4. POR QUÉ: Por qué fue necesario el cambio (2-3 oraciones)
5. CÓMO: Enfoque técnico o detalles clave de implementación
6. IMPACTO: Archivos/componentes afectados y posibles efectos secundarios

Usa precisión técnica. Referencia funciones, clases y módulos específicos.
Usa tiempo presente y voz activa.

Ejemplo:
Refactorizar middleware de autenticación para usar inyección de dependencias

QUÉ: Reemplazado estado de autenticación global con AuthService inyectable. Actualizados
todos los manejadores de ruta para aceptar AuthService a través de inyección de constructor.

POR QUÉ: El estado global dificultaba las pruebas y creaba dependencias ocultas.
La inyección de dependencias mejora la capacidad de prueba y hace las dependencias explícitas.

CÓMO: Creada interfaz AuthService, implementada JWTAuthService y
MockAuthService. Modificados constructores de manejadores de ruta para requerir AuthService.
Actualizada configuración del contenedor de inyección de dependencias.

IMPACTO: Afecta todas las rutas autenticadas. No hay cambios de comportamiento para los usuarios.
Las pruebas ahora se ejecutan 3x más rápido con MockAuthService. Migración requerida para
routes/auth.ts, routes/api.ts y routes/admin.ts.
```

## Mejores Prácticas

### Haz

- ✅ **Sé específico** - Instrucciones claras producen mejores resultados
- ✅ **Incluye ejemplos** - Muestra a la IA cómo se ve lo bueno
- ✅ **Prueba iterativamente** - Prueba tu prompt, refina basado en resultados
- ✅ **Mantenlo enfocado** - Demasiadas reglas pueden confundir a la IA
- ✅ **Usa terminología consistente** - Mantén los mismos términos a lo largo
- ✅ **Termina con un recordatorio** - Refuerza que la respuesta se usará tal cual

### No Hagas

- ❌ **Uses etiquetas XML** - El texto plano funciona mejor (a menos que específicamente quieras esa estructura)
- ❌ **Lo hagas demasiado largo** - Apunta a 200-500 palabras de instrucciones
- ❌ **Te contradigas** - Sé consistente en tus requisitos
- ❌ **Olvides el final** - Recuerda siempre: "Tu respuesta completa se usará directamente como el mensaje de commit"

### Consejos

- **Comienza con el ejemplo** - Copia `../../examples/custom_system_prompt.example.txt` y modifícalo
- **Prueba con `--dry-run`** - Ve el resultado sin hacer un commit
- **Usa `--show-prompt`** - Ve qué se está enviando a la IA
- **Itera basado en resultados** - Si los mensajes no son del todo correctos, ajusta tus instrucciones
- **Controla la versión de tu prompt** - Mantén tu prompt personalizado en el repositorio de tu equipo
- **Prompts específicos de proyecto** - Usa `.gac.env` a nivel de proyecto para estilos específicos de proyecto

## Solución de Problemas

### Los mensajes aún tienen el prefijo "chore:"

**Problema:** Tus mensajes de emoji personalizados están obteniendo "chore:" añadido.

**Solución:** Esto no debería pasar—GAC automáticamente deshabilita la ejecución de commits convencionales al usar prompts del sistema personalizados. Si ves esto, por favor [presenta un issue](https://github.com/cellwebb/gac/issues).

### La IA ignora mis instrucciones

**Problema:** Los mensajes generados no siguen tu formato personalizado.

**Solución:**

1. Haz tus instrucciones más explícitas y específicas
2. Añade ejemplos claros del formato deseado
3. Termina con: "Tu respuesta completa se usará directamente como el mensaje de commit"
4. Reduce el número de requisitos—demasiados pueden confundir a la IA
5. Intenta usar un modelo diferente (algunos siguen instrucciones mejor que otros)

### Los mensajes son demasiado largos/cortos

**Problema:** Los mensajes generados no coinciden con tus requisitos de longitud.

**Solución:**

- Sé explícito sobre la longitud (ej., "Mantén los mensajes bajo 50 caracteres")
- Muestra ejemplos de la longitud exacta que quieres
- Considera usar también la bandera `--one-liner` para mensajes cortos

### El prompt personalizado no se está usando

**Problema:** GAC todavía usa el formato de commit predeterminado.

**Solución:**

1. Verifica que `GAC_SYSTEM_PROMPT_PATH` esté configurado correctamente:

   ```bash
   uvx gac config get GAC_SYSTEM_PROMPT_PATH
   ```

2. Verifica que la ruta del archivo existe y es legible:

   ```bash
   cat "$GAC_SYSTEM_PROMPT_PATH"
   ```

3. Revisa los archivos `.gac.env` en este orden:
   - A nivel de proyecto: `./.gac.env`
   - A nivel de usuario: `~/.gac.env`
4. Intenta una ruta absoluta en lugar de una ruta relativa

### Configuración de Idioma

**Nota:** ¡No necesitas un prompt del sistema personalizado para cambiar el idioma del mensaje de commit!

Si solo quieres cambiar el idioma de tus mensajes de commit (manteniendo el formato de commit convencional estándar), usa el selector de idioma interactivo:

```bash
uvx gac language
```

Esto presentará un menú interactivo con 25+ idiomas en sus scripts nativos (Español, Français, 日本語, etc.). Selecciona tu idioma preferido, y automáticamente establecerá `GAC_LANGUAGE` en tu archivo `~/.gac.env`.

Alternativamente, puedes configurar manualmente el idioma:

```bash
# En ~/.gac.env o .gac.env a nivel de proyecto
GAC_LANGUAGE=Spanish
```

Por defecto, los prefijos de commits convencionales (feat:, fix:, etc.) permanecen en inglés para compatibilidad con herramientas de changelog y pipelines de CI/CD, mientras que todo el otro texto está en tu idioma especificado.

**¿Quieres traducir los prefijos también?** Establece `GAC_TRANSLATE_PREFIXES=true` en tu `.gac.env` para localización completa:

```bash
GAC_LANGUAGE=Spanish
GAC_TRANSLATE_PREFIXES=true
```

Esto traducirá todo, incluyendo prefijos (ej., `corrección:` en lugar de `fix:`).

Esto es más simple que crear un prompt del sistema personalizado si el idioma es tu única necesidad de personalización.

### Quiero volver al predeterminado

**Problema:** Quiero usar temporalmente los predeterminados.

**Solución:**

```bash
# Opción 1: Desestablecer la variable de entorno
uvx gac config unset GAC_SYSTEM_PROMPT_PATH

# Opción 2: Coméntala en .gac.env
# GAC_SYSTEM_PROMPT_PATH=/ruta/a/custom_prompt.txt

# Opción 3: Usa un .gac.env diferente para proyectos específicos
```

---

## Documentación Relacionada

- [USAGE.md](../USAGE.md) - Banderas y opciones de línea de comandos
- [README.md](../README.md) - Instalación y configuración básica
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Solución de problemas general

## ¿Necesitas Ayuda?

- Reporta issues: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- ¡Comparte tus prompts personalizados: Las contribuciones son bienvenidas!

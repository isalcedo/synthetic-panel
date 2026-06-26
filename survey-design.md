# Diseño de encuestas para validación de ideas

Guía para elaborar encuestas que realmente falsifiquen hipótesis de negocio.
El orquestador debe aplicarla siempre que derive preguntas a partir de una idea,
o cuando el usuario entregue un cuestionario que viole estos principios.

## El problema de fondo: sesgo de confirmación

El error más común no está en las preguntas, sino en la intención al formularlas.
La mayoría de los fundadores diseñan encuestas para confirmar lo que ya creen, no
para descubrir la verdad. El resultado es un conjunto de respuestas que se sienten
como validación pero no lo son.

> *"La frase más mortífera es: 'Definitivamente compraría eso.' La gente siempre es
> más positiva, entusiasmada y dispuesta a pagar en el futuro imaginado que cuando
> ese futuro llega."* — Rob Fitzpatrick, *The Mom Test*

La encuesta no debe vender la idea. Debe poner a prueba los supuestos más críticos.

---

## Principio 1: Define primero qué quieres falsificar

Antes de escribir una sola pregunta, lista las **hipótesis centrales** como
afirmaciones que podrían resultar falsas:

- "El problema X existe y es frecuente para este perfil de persona."
- "Las personas que tienen el problema gastan tiempo/dinero en resolverlo hoy."
- "Estarían dispuestas a pagar $Y por una solución."
- "El canal Z es donde estas personas buscan soluciones."

Cada sección de la encuesta debe atacar una hipótesis. Si no puedes asignar cada
pregunta a una hipótesis, esa pregunta sobra.

**En el panel sintético:** registra las hipótesis en `study.hypotheses` y asigna
cada pregunta un campo `hypothesis` (id de hipótesis) y `block` (ver Principio 5).

---

## Principio 2: Segmenta antes de interpretar

Una encuesta aplicada a "todo el mundo" no valida nada. Necesitas saber con quién
estás hablando para que las respuestas sean útiles.

**Coloca preguntas de filtro al inicio:**

- Rol, industria, tamaño de empresa (si es B2B)
- Frecuencia con la que enfrenta el problema que resuelves
- Herramientas o métodos que usa hoy para resolver ese problema

Quien no califica como cliente potencial debe ser separado en el análisis. Sus
respuestas no son datos sobre tu mercado; son ruido.

**En el panel sintético:** las personas ya están segmentadas por `audience`, pero
el Bloque 0 (filtro) permite marcar cuáles califican dentro del panel. Al
agregar, separa distribuciones de quienes pasan vs. no pasan el filtro.

---

## Principio 3: Pregunta sobre el pasado, no sobre el futuro

Las preguntas sobre comportamientos futuros o hipotéticos producen respuestas
optimistas e inútiles. Las preguntas sobre comportamientos pasados revelan la
realidad.


| ❌ Pregunta hipotética                           | ✅ Pregunta anclada en el pasado                                                            |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------ |
| "¿Usarías una herramienta así?"                 | "¿Qué hiciste la última vez que enfrentaste este problema?"                                |
| "¿Cuánto pagarías por esta solución?"           | "¿Cuánto gastaste en los últimos 6 meses en resolver esto (tiempo, dinero, herramientas)?" |
| "¿Qué tan importante es este problema para ti?" | "¿Buscaste activamente una solución en los últimos 3 meses? ¿Cuál?"                        |


Si alguien no ha buscado una solución activamente, probablemente no pagará por la tuya.

**En el panel sintético:** evita escalas de "probabilidad de uso" o "intención de
compra" como preguntas principales. Si el usuario las pide, tradúcelas a
comportamiento pasado o rechaza con una alternativa mejor.

---

## Principio 4: Evita los sesgos más comunes en el diseño

### Preguntas inductoras (*leading questions*)

Presionan al respondiente hacia una respuesta específica.

- ❌ "¿Cuánto te frustra la falta de herramientas eficientes para X?"
- ✅ "¿Cómo describes tu experiencia actual con X?"

### Preguntas de doble barril

Preguntan dos cosas a la vez.

- ❌ "¿La herramienta es fácil de usar y visualmente atractiva?"
- ✅ Una pregunta por cada dimensión, por separado.

### Sesgo de aquiescencia

La gente tiende a decir "sí" o a estar "de acuerdo". Contrarresta con:

- Escalas balanceadas (igual número de opciones positivas y negativas)
- Varía la dirección de las afirmaciones
- No encadenes muchas preguntas de escala seguidas

### Sesgo de deseabilidad social

Los respondientes dicen lo que creen que quieres escuchar. Reduce con:

- Preguntas descriptivas, no evaluativas ("¿Qué haces hoy?" vs. "¿Qué tan bien lo manejas?")
- Contexto que normalice la dificultad ("Muchas personas encuentran esto difícil...")

**En el panel sintético:** las personas sintéticas también pueden ser
over-constrained o demasiado complacientes. Las preguntas descriptivas y el
diagnóstico `over_constrained` ayudan a detectar respuestas poco realistas.

---

## Principio 5: Estructura de la encuesta

### Bloque 0 — Filtro de perfil (2–3 preguntas)

Establece si el respondiente es cliente potencial. Nunca lo menciones como filtro;
solo recoge los datos y filtra al analizar.

### Bloque 1 — El problema (3–4 preguntas)

Explora frecuencia, intensidad y contexto del problema. **No menciones la solución.**

### Bloque 2 — Comportamiento actual (2–3 preguntas)

¿Qué hace hoy para resolver el problema? ¿Cuánto le cuesta (tiempo, dinero,
fricción)? ¿Qué tan satisfecha está con las alternativas actuales?

### Bloque 3 — Disposición a cambiar (2–3 preguntas)

Indaga si han buscado soluciones, qué los detuvo, y qué criterios usarían para
elegir una nueva opción. **Aún sin mencionar el producto.**

### Bloque 4 — Concepto o solución (opcional, al final)

Solo si los bloques anteriores confirman problema real y búsqueda activa.
Presenta brevemente el concepto y recoge reacción. Pregunta clave:
**"¿Qué te haría no usarlo o no pagarlo?"** — más honesta que "¿lo comprarías?".

### Bloque 5 — Disposición a pagar (1–2 preguntas)

Usa rangos concretos, no preguntas abiertas. El método Van Westendorp es útil:
cuatro preguntas sobre el precio que empieza a parecer caro, el que parece una
ganga, el que sería inaceptable por caro y el que sería sospechoso de baja calidad
por barato.

**Límite:** máximo 10–12 preguntas en total.

---

## Principio 6: Longitud y formato

- **Máximo 10–12 preguntas.** Más aumenta abandono y sesgo de cansancio.
- **Mezcla cerradas y abiertas.** Las cerradas dan datos cuantificables; las
abiertas revelan el lenguaje real del cliente.
- **Una pregunta abierta al final:** "¿Hay algo sobre este tema que no te
preguntamos y que consideras importante?"
- **Piloto antes del lanzamiento.** En panel sintético, corre primero con N=3–5
personas si el usuario quiere iterar el cuestionario antes del panel completo.

---

## Principio 7: Muestra y distribución

- **Tamaño orientativo:** 100–500 respuestas reales según nicho. Con menos de 50,
los patrones son tentativas, no evidencia.
- **No uses tu red cercana como muestra principal.**
- **Distribuye por múltiples canales** para evitar sesgo de selección.
- **Separa respondientes por perfil** al analizar.

**En el panel sintético:** N=10 es un banco de descubrimiento, no evidencia
estadística. Diversifica personas (demografía, OCEAN, ocupación) para simular
variación de canal/perfil. Comunica al usuario que el panel complementa, no
reemplaza, encuestas reales con muestra adecuada.

---

## Principio 8: Interpretación honesta

- **Busca patrones que falsifiquen la hipótesis**, no solo los que la confirman.
- **El lenguaje espontáneo en respuestas abiertas vale oro.** Usa esas palabras
exactas en el resumen ejecutivo del canvas.
- **Desconfía del entusiasmo sin acción.** Entusiasmo alto + búsqueda pasiva
activa = señal débil de demanda.
- **El no-respondiente también es dato.** Alta varianza o respuestas vacías en un
bloque pueden indicar preguntas irrelevantes.

**En el panel sintético:** el resumen ejecutivo y el canvas deben incluir:

1. Por cada hipótesis: ¿confirmada, refutada o inconclusa?
2. Citas literales de respuestas abiertas (lenguaje del cliente).
3. Señales de falsificación explícitas, no solo métricas positivas.
4. Advertencia cuando entusiasmo (Bloque 4) contradice comportamiento pasado
  (Bloques 1–3).

---

## Lista de verificación antes de publicar

- [ ] Cada pregunta está asociada a una hipótesis de negocio específica
- [ ] Ninguna pregunta revela la solución antes del Bloque 4
- [ ] No hay preguntas inductoras, de doble barril ni con carga emocional
- [ ] Las escalas son balanceadas (mismo número de opciones positivas y negativas)
- [ ] Hay al menos una pregunta de comportamiento pasado por hipótesis clave
- [ ] Existe una pregunta de filtro de perfil al inicio
- [ ] La encuesta completa se puede responder en menos de 7 minutos
- [ ] Total de preguntas ≤ 12

El orquestador debe pasar esta checklist antes de confirmar el cuestionario con
el usuario y antes de escribir `personas.json`.
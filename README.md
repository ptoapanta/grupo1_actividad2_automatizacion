# grupo1_actividad2_automatizacion
# Análisis Macroeconómico del Euro (EUR)
## 1. Contextualización del Problema
La Eurozona constituye uno de los bloques económicos más complejos e influyentes del comercio global. La toma de decisiones financieras, la gestión de portafolios de inversión y la evaluación del riesgo cambiario dependen críticamente de la correcta interpretación de variables macroeconómicas dinámicas. Indicadores como las tasas de interés fijadas por el Banco Central Europeo (BCE), el Índice de Precios al Consumidor (IPC) que mide la inflación, el Producto Interno Bruto (PIB) y las tasas de desempleo generan un flujo constante de datos heterogéneos y de alta frecuencia.
El problema radica en que estos datos macroeconómicos suelen encontrarse dispersos en múltiples fuentes institucionales (Eurostat, bases de datos del BCE, APIs financieras), presentando diferentes formatos, periodicidades y niveles de estructuración. Para un analista, estudiante o tomador de decisiones, la recopilación manual, el procesamiento y la modelización visual de estos factores representa una alta carga operativa y un riesgo de error humano.
Existe, por lo tanto, la necesidad de desarrollar una solución informática centralizada y automatizada que no solo extraiga e integre estas variables en tiempo real, sino que además ofrezca herramientas avanzadas de análisis, visualización y modelado predictivo de volatilidad, permitiendo transformar datos macroeconómicos crudos en información estratégica accionable.
## 2. Objetivos del Proyecto
Objetivo General
Desarrollar e implementar una aplicación informática modular y operativa que centralice, procese y visualice indicadores macroeconómicos clave de la eurozona, con el fin de proveer un entorno automatizado de análisis financiero y soporte para la evaluación de riesgos del Euro.

Objetivos Específicos
Automatización de Datos: Diseñar e implementar un pipeline de ingesta de datos eficiente para extraer información en tiempo real e histórica desde fuentes oficiales (como APIs financieras o Eurostat).

Arquitectura Mantenible: Desarrollar el sistema bajo una arquitectura de software limpia y modular que garantice la reutilización de código, la separación de responsabilidades y la escalabilidad del sistema.

Análisis Analítico Avanzado: Integrar módulos de cálculo técnico para evaluar la volatilidad, tendencias y correlaciones entre las variables macroeconómicas y el comportamiento del par de divisas (por ejemplo, EUR/USD).

Interfaz de Usuario Ingestible: Construir una interfaz gráfica de usuario intuitiva y dinámica que presente gráficos interactivos y tableros de control (dashboards) estructurados para facilitar la interpretación de datos complejos.

Gestión de Calidad y Versiones: Evidenciar un flujo de trabajo colaborativo y progresivo utilizando GitHub, aplicando buenas prácticas de ramificación (branching), resolución de conflictos y documentación continua.

## 3. Arquitectura Detallada del Sistema: Análisis Macroeconómico del Euro

El diseño arquitectónico de la aplicación sigue un enfoque de Capas Desacopladas (Decoupled Layered Architecture). Esta separación lógica garantiza la modularidad, la fácil detección de errores (debugging) y la escalabilidad de las funcionalidades analíticas sin comprometer el rendimiento de la interfaz gráfica de usuario. 
El flujo de datos opera de manera unidireccional, transformando datos macroeconómicos crudos de la eurozona en métricas financieras procesadas e interactivas.

Capa de Ingesta y Conectores de Datos: Establece la comunicación directa con las APIs institucionales del Banco Central Europeo (BCE), Eurostat y proveedores de datos de mercado (como Yahoo Finance o Alpha Vantage). Este módulo implementa peticiones asíncronas para extraer las series temporales de variables fundamentales de la eurozona: Tasas de interés de operaciones principales de refinanciación, Índices de Precios de Consumo Armonizado (IPCA) para la inflación, evolución trimestral del PIB y cotizaciones de cierre diarias del tipo de cambio EUR/USD. Las credenciales de acceso se gestionan mediante un archivo aislado de configuración ambiental (.env).

Capa de Limpieza y Homologación de Series: Los datos macroeconómicos extraídos presentan inconsistencias críticas: periodicidades heterogéneas (tasas de interés y cotizaciones cambiarias son diarias, la inflación es mensual y el PIB es trimestral). Esta capa se encarga de estructurar los sets de datos mediante herramientas avanzadas de manipulación de matrices (Pandas). Aplica técnicas de interpolación lineal para rellenar registros faltantes, normaliza las marcas de tiempo a un formato estándar de series temporales (ISO 8601) y ejecuta procesos de remuestreo (resampling) para alinear temporalmente los indicadores antes de su cruce analítico.

Capa de Análisis Económico y Modelado Matemático: Representa el núcleo inteligente o motor analítico de la aplicación. Ejecuta algoritmos estadísticos sobre las variables macroeconómicas previamente homologadas

Capa de Presentación e Interfaz de Usuario: Se encarga de renderizar la información de forma visual, interactiva y dinámica. Utilizando librerías de componentes analíticos avanzados, abstrae la lógica compleja en tableros de control visuales (Dashboards). Presenta al usuario gráficos de líneas interactivos de series temporales combinadas (como tasas de interés vs. cotización cambiaria), mapas de calor de correlaciones económicas y paneles informativos con alertas dinámicas ante cambios drásticos en la política monetaria de la Eurozona.

# Web Analysis Framework

Un framework avanzado para análisis de sitios web, generación automática de casos de prueba y ejecución de tests utilizando modelos de lenguaje (LLM).

## Características principales

- **Análisis completo de sitios web** - Navega y analiza la estructura completa de un sitio web, identificando páginas, enlaces y relaciones.
- **Visualización interactiva** - Representa la estructura del sitio como un grafo interactivo donde puedes explorar la jerarquía del sitio.
- **Generación automática de casos de prueba** - Crea automáticamente casos de prueba basados en la estructura del sitio y el contenido de las páginas.
- **Detección de caminos** - Al seleccionar un nodo en el grafo, muestra visualmente todos los caminos posibles desde la raíz hasta ese nodo.
- **Generación de código Selenium** - Utiliza Llama 3.1 (8B) a través de Ollama para generar código de prueba en Python/Selenium.
- **Ejecución en tiempo real** - Ejecuta tests de Selenium y visualiza el progreso en tiempo real directamente desde la interfaz.
- **Categorización con ML** - Aplica machine learning para clasificar el tipo de sitio web y generar tests específicos.

## Arquitectura

El sistema está construido con una arquitectura modular:

- **Frontend**: HTML/CSS/JS con Bootstrap 5 para la interfaz de usuario
- **Backend**: API FastAPI para gestionar las solicitudes y coordinar el análisis
- **Módulos principales**:
  - `web_analyzer.py` - Realiza el análisis del sitio web y genera la estructura
  - `test_generator.py` - Genera casos de prueba basados en la estructura analizada
  - `code_generator.py` - Genera código Selenium utilizando Ollama (Llama 3.1)

## Requisitos

- Python 3.8 o superior
- Ollama (con el modelo llama3.1:8b instalado)
- Navegador compatible con WebDriver (Chrome/Firefox)
- Selenium WebDriver

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/web-analysis-framework.git
   cd web-analysis-framework
   ```

2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   # En Windows
   venv\Scripts\activate
   # En Linux/Mac
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. Instala Ollama y descarga el modelo:
   ```bash
   # Instala Ollama desde https://ollama.com/
   
   # Una vez instalado, descarga el modelo
   ollama pull llama3.1:8b
   ```

4. Instala los WebDrivers para Selenium:
   - Chrome: https://sites.google.com/chromium.org/driver/
   - Firefox: https://github.com/mozilla/geckodriver/releases
   
   Añade los WebDrivers al PATH del sistema o colócalos en el directorio del proyecto.

## Configuración

1. Asegúrate de que Ollama esté ejecutándose:
   ```bash
   # Inicia el servidor Ollama (si no está en ejecución automática)
   ollama serve
   ```

2. Comprueba que el modelo esté disponible:
   ```bash
   ollama list
   ```

## Uso del sistema

1. Inicia la aplicación:
   ```bash
   python -m app.main
   ```

2. Abre tu navegador en `http://localhost:8000`

3. Flujo básico de uso:
   - Introduce la URL del sitio web a analizar
   - Visualiza la estructura del sitio como un grafo interactivo
   - Selecciona nodos específicos para ver los caminos y generar casos de prueba
   - Genera código Selenium con Ollama para los casos de prueba seleccionados
   - Ejecuta tests y visualiza resultados en tiempo real

## Pasos detallados

### 1. Análisis de un sitio web

1. En la pestaña "Analyze Website", introduce la URL completa del sitio web
2. El sistema analizará la estructura del sitio, identificando páginas y conexiones
3. El grafo interactivo mostrará la estructura jerárquica del sitio web
4. Puedes hacer clic en cualquier nodo para ver detalles y resaltar caminos

### 2. Generación de casos de prueba

1. En la pestaña "Test Cases", haz clic en "Generate Test Cases"
2. El sistema creará automáticamente casos de prueba basados en el análisis
3. Para generar tests para una página específica, selecciona primero un nodo en el grafo
4. Haz clic en "Generate Tests for This Page" para obtener tests específicos

### 3. Generación y ejecución de código

1. En la pestaña "Generated Code", selecciona un caso de prueba
2. Haz clic en "Generate Code with Ollama" para crear código Selenium
3. Revisa el código generado y ajústalo si es necesario
4. Haz clic en "Execute Test" para ejecutar la prueba
5. Observa el progreso y los resultados en tiempo real

## Solución de problemas

- **Problema**: Error de conexión con Ollama
  - **Solución**: Verifica que Ollama esté en ejecución con `ollama serve`

- **Problema**: WebDriver no encontrado
  - **Solución**: Asegúrate de que el WebDriver esté en el PATH y sea compatible con tu versión del navegador

- **Problema**: Fallos en la generación del grafo
  - **Solución**: Utiliza el botón "Reload Graph" para intentar regenerar la visualización

## Limitaciones actuales

- Profundidad de análisis configurada a 5 niveles máximo
- Máximo de 100 páginas analizadas por sitio
- Tiempos de espera configurados para sitios de tamaño mediano

## Créditos y licencia

Este proyecto utiliza varias tecnologías de código abierto:
- Llama 3.1 (Meta AI)
- Ollama
- Selenium WebDriver
- vis.js para visualización de grafos
- FastAPI para el backend

Licenciado bajo MIT License. 
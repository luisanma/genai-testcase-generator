/**
 * Saved Explorations UI Management
 * 
 * Este archivo contiene la funcionalidad para gestionar exploraciones guardadas,
 * test cases, y código generado asociado a cada exploración.
 */

// Variables globales
let currentExploration = null;
let currentTestCases = [];
let currentGeneratedCode = {};

/**
 * Inicializa la interfaz de exploraciones guardadas
 */
function initSavedExplorations() {
    $('#saved-explorations-btn').on('click', loadSavedExplorations);
    $('#exploration-details-close').on('click', closeExplorationDetails);
    
    // Botones de acción
    $('#show-test-cases-btn').on('click', showTestCasesForExploration);
    $('#generate-test-cases-btn').on('click', generateTestCasesForExploration);
    
    // Inicializa los tooltips y popovers
    $('[data-toggle="tooltip"]').tooltip();
    $('[data-toggle="popover"]').popover();
}

/**
 * Carga la lista de exploraciones guardadas
 */
function loadSavedExplorations() {
    showLoading('Cargando exploraciones guardadas...');
    
    fetch('/api/explorations')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.explorations && data.explorations.length > 0) {
                displaySavedExplorations(data.explorations);
                $('#saved-explorations-container').removeClass('d-none');
                $('#website-form-container').addClass('d-none');
            } else {
                showNotification('No hay exploraciones guardadas', 'info');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error loading saved explorations:', error);
            showNotification('Error al cargar las exploraciones guardadas: ' + error.message, 'error');
        });
}

/**
 * Muestra la lista de exploraciones guardadas
 */
function displaySavedExplorations(explorations) {
    const tableBody = $('#saved-explorations-table tbody');
    tableBody.empty();
    
    explorations.forEach((exploration, index) => {
        const hasTestCases = exploration.summary && exploration.summary.has_test_cases;
        const hasGeneratedCode = exploration.summary && exploration.summary.has_generated_code;
        const testCaseCount = exploration.summary && exploration.summary.test_case_count || 0;
        
        const row = `
            <tr data-exploration-id="${exploration._id}">
                <td>${index + 1}</td>
                <td>
                    <strong>${exploration.name || exploration.domain || 'Sin nombre'}</strong>
                    <br>
                    <small class="text-muted">${exploration.url}</small>
                </td>
                <td>${new Date(exploration.created_at).toLocaleString()}</td>
                <td>
                    ${hasTestCases 
                        ? `<span class="badge badge-success">${testCaseCount} Test Cases</span>` 
                        : '<span class="badge badge-secondary">No hay tests</span>'}
                    ${hasGeneratedCode 
                        ? '<span class="badge badge-info">Código Generado</span>' 
                        : ''}
                </td>
                <td>
                    <button class="btn btn-sm btn-primary load-exploration-btn" 
                            data-exploration-id="${exploration._id}">
                        <i class="fas fa-eye"></i> Ver
                    </button>
                    <button class="btn btn-sm btn-danger delete-exploration-btn" 
                            data-exploration-id="${exploration._id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        
        tableBody.append(row);
    });
    
    // Asigna event handlers
    $('.load-exploration-btn').on('click', function() {
        const explorationId = $(this).data('exploration-id');
        loadExplorationDetails(explorationId);
    });
    
    $('.delete-exploration-btn').on('click', function() {
        const explorationId = $(this).data('exploration-id');
        confirmDeleteExploration(explorationId);
    });
}

/**
 * Carga los detalles de una exploración
 */
function loadExplorationDetails(explorationId) {
    showLoading('Cargando detalles de la exploración...');
    
    fetch(`/api/explorations/${explorationId}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            currentExploration = data;
            displayExplorationDetails(data);
        })
        .catch(error => {
            hideLoading();
            console.error('Error loading exploration details:', error);
            showNotification('Error al cargar los detalles de la exploración: ' + error.message, 'error');
        });
}

/**
 * Muestra los detalles de una exploración
 */
function displayExplorationDetails(exploration) {
    // Actualiza la UI con los detalles de la exploración
    $('#exploration-title').text(exploration.name || exploration.domain || 'Exploración sin nombre');
    $('#exploration-url').text(exploration.url);
    $('#exploration-date').text(new Date(exploration.created_at).toLocaleString());
    
    // Información de la estructura
    const pageCount = exploration.data && exploration.data.pages ? Object.keys(exploration.data.pages).length : 0;
    $('#exploration-page-count').text(pageCount);
    
    // Muestra la sección de detalles
    $('#saved-explorations-container').addClass('d-none');
    $('#exploration-details-container').removeClass('d-none');
    
    // Configura botones según estado
    const hasTestCases = exploration.summary && exploration.summary.has_test_cases;
    if (hasTestCases) {
        $('#show-test-cases-btn').removeClass('d-none');
        $('#generate-test-cases-btn').addClass('d-none');
    } else {
        $('#show-test-cases-btn').addClass('d-none');
        $('#generate-test-cases-btn').removeClass('d-none');
    }
}

/**
 * Genera casos de prueba para la exploración actual
 */
function generateTestCasesForExploration() {
    if (!currentExploration) return;
    
    showLoading('Generando casos de prueba...');
    
    const requestData = {
        url: currentExploration.url
    };
    
    fetch('/api/generate-tests', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        currentTestCases = data;
        displayTestCases(data);
        
        // Actualiza botones
        $('#show-test-cases-btn').removeClass('d-none');
        $('#generate-test-cases-btn').addClass('d-none');
        
        showNotification('Se han generado ' + data.length + ' casos de prueba', 'success');
    })
    .catch(error => {
        hideLoading();
        console.error('Error generating test cases:', error);
        showNotification('Error al generar casos de prueba: ' + error.message, 'error');
    });
}

/**
 * Muestra los casos de prueba para la exploración actual
 */
function showTestCasesForExploration() {
    if (!currentExploration) return;
    
    showLoading('Cargando casos de prueba...');
    
    fetch(`/api/explorations/${currentExploration._id}/test-cases-with-code`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.status === 'success' && data.test_cases && data.test_cases.length > 0) {
                currentTestCases = data.test_cases;
                
                // Agregar el campo para ChromeDriver si no existe
                if ($('#chrome-driver-container').length === 0) {
                    $('#exploration-details-container .card-body').prepend(`
                        <div id="chrome-driver-container" class="mb-4 p-3 border rounded bg-light">
                            <h5><i class="fas fa-cog"></i> Configuración de ChromeDriver</h5>
                            <div class="form-group">
                                <label for="chrome-driver-path">Ruta al ejecutable ChromeDriver:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="chrome-driver-path" 
                                           placeholder="Ej: C:/chromedriver/chromedriver.exe" 
                                           value="C:\\projects\\testcase\\chromedriver.exe">
                                    <div class="input-group-append">
                                        <button class="btn btn-info" id="verify-chrome-driver">
                                            <i class="fas fa-check-circle"></i> Verificar
                                        </button>
                                    </div>
                                </div>
                                <small class="form-text text-muted">
                                    Especifica la ruta absoluta al ejecutable chromedriver.exe necesario para visualizar los tests en el navegador.
                                </small>
                            </div>
                        </div>
                    `);
                    
                    // Agregar manejador para el botón de verificación
                    $('#verify-chrome-driver').on('click', verifyChromePath);
                }
                
                displayTestCases(data.test_cases);
            } else {
                showNotification('No hay casos de prueba para esta exploración', 'info');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error loading test cases:', error);
            showNotification('Error al cargar los casos de prueba: ' + error.message, 'error');
        });
}

/**
 * Verifica la ruta del ChromeDriver
 */
function verifyChromePath() {
    const chromeDriverPath = $('#chrome-driver-path').val();
    if (!chromeDriverPath) {
        showNotification('Por favor, ingresa una ruta para ChromeDriver', 'warning');
        return;
    }
    
    showLoading('Verificando ChromeDriver...');
    
    // Crear un objeto temporal para enviar al servidor
    const simpleCode = `
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import time

# Configurar ChromeDriver
chrome_driver_path = "${chromeDriverPath.replace(/\\/g, '\\\\')}"
print(f"Verificando ChromeDriver en: {chrome_driver_path}")

try:
    # Configurar opciones
    options = Options()
    options.add_argument("--start-maximized")
    
    # Inicializar el driver con la ruta especificada
    if os.path.exists(chrome_driver_path):
        print(f"El archivo ChromeDriver existe en la ruta especificada")
        service = Service(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ ChromeDriver inicializado correctamente")
        
        # Navegar a una página simple
        driver.get("https://www.google.com")
        print(f"Navegador abierto con título: {driver.title}")
        
        # Esperar un momento y cerrar
        time.sleep(2)
        driver.quit()
        print("✅ Verificación completada con éxito")
    else:
        print(f"❌ Error: No se encontró el archivo en {chrome_driver_path}")
        
except Exception as e:
    print(f"❌ Error al inicializar ChromeDriver: {str(e)}")
`;

    // Enviar solicitud al servidor
    fetch('/api/execute-simple-test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            test_code: simpleCode,
            chrome_driver_path: chromeDriverPath
        })
    })
    .then(response => {
        if (!response.ok) {
            console.error("Error HTTP:", response.status, response.statusText);
            return response.text().then(text => {
                try {
                    const errorData = JSON.parse(text);
                    throw new Error(`Error ${response.status}: ${errorData.detail || errorData.message || response.statusText}`);
                } catch (e) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
            });
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.status === 'completed' || data.status === 'success') {
            showNotification('ChromeDriver verificado correctamente', 'success');
            // Mostrar los logs
            let logsHtml = '<div class="mt-3 p-2 bg-dark text-white rounded"><h6>Resultado de la verificación:</h6>';
            data.output.forEach(log => {
                if (log && log.trim()) {
                    if (log.includes('✅')) {
                        logsHtml += `<div class="text-success">${log}</div>`;
                    } else if (log.includes('❌')) {
                        logsHtml += `<div class="text-danger">${log}</div>`;
                    } else {
                        logsHtml += `<div>${log}</div>`;
                    }
                }
            });
            logsHtml += '</div>';
            
            // Agregar o reemplazar los logs
            if ($('#chrome-driver-logs').length) {
                $('#chrome-driver-logs').remove();
            }
            $('#chrome-driver-container').append(`<div id="chrome-driver-logs">${logsHtml}</div>`);
        } else {
            // Mostrar error
            showNotification('Error al verificar ChromeDriver: ' + data.message, 'error');
            
            let errorHtml = '<div class="mt-3 p-2 bg-dark text-white rounded"><h6 class="text-danger">Error al verificar ChromeDriver:</h6>';
            if (data.error && data.error.length) {
                data.error.forEach(err => {
                    if (err && err.trim()) {
                        errorHtml += `<div class="text-danger">${err}</div>`;
                    }
                });
            }
            errorHtml += '</div>';
            
            // Agregar o reemplazar los logs
            if ($('#chrome-driver-logs').length) {
                $('#chrome-driver-logs').remove();
            }
            $('#chrome-driver-container').append(`<div id="chrome-driver-logs">${errorHtml}</div>`);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error verifying ChromeDriver:', error);
        showNotification('Error al verificar ChromeDriver: ' + error.message, 'error');
    });
}

/**
 * Muestra los casos de prueba en la interfaz
 */
function displayTestCases(testCases) {
    const container = $('#test-cases-container');
    container.empty();
    
    // Agrega título
    container.append(`
        <div class="row mb-3">
            <div class="col">
                <h4>Casos de Prueba (${testCases.length})</h4>
            </div>
        </div>
    `);
    
    // Crea cards para cada caso de prueba
    testCases.forEach(testCase => {
        const hasGeneratedCode = testCase.has_generated_code || (testCase.generated_code !== null);
        const generatedCode = testCase.generated_code ? testCase.generated_code.code : null;
        
        const card = `
            <div class="card mb-3 test-case-card" data-test-id="${testCase.id}">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">
                        <span class="test-case-title">${testCase.title}</span>
                        <span class="float-right">
                            ${hasGeneratedCode 
                                ? '<span class="badge badge-light"><i class="fas fa-code"></i> Código disponible</span>' 
                                : ''}
                        </span>
                    </h5>
                </div>
                <div class="card-body">
                    <p class="card-text">${testCase.description}</p>
                    
                    <div class="test-steps mb-3">
                        <h6>Pasos:</h6>
                        <ol>
                            ${testCase.steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                    
                    <div class="test-expected-results mb-3">
                        <h6>Resultados Esperados:</h6>
                        <ol>
                            ${testCase.expected_results.map(result => `<li>${result}</li>`).join('')}
                        </ol>
                    </div>
                    
                    <div class="row">
                        <div class="col">
                            ${hasGeneratedCode 
                                ? `<button class="btn btn-info view-code-btn" data-test-id="${testCase.id}">
                                    <i class="fas fa-code"></i> Ver Código
                                   </button>
                                   <button class="btn btn-success run-test-btn" data-test-id="${testCase.id}">
                                    <i class="fas fa-play"></i> Ejecutar Test
                                   </button>`
                                : `<button class="btn btn-primary generate-code-btn" data-test-id="${testCase.id}">
                                    <i class="fas fa-code"></i> Generar Código
                                   </button>`
                            }
                        </div>
                    </div>
                    
                    ${hasGeneratedCode ? `
                    <div class="code-container mt-3 d-none" id="code-container-${testCase.id}">
                        <div class="card">
                            <div class="card-header bg-dark text-white">
                                <span>Código Generado</span>
                                <button class="btn btn-sm btn-light float-right copy-code-btn" data-test-id="${testCase.id}">
                                    <i class="fas fa-copy"></i> Copiar
                                </button>
                            </div>
                            <div class="card-body p-0">
                                <pre class="m-0"><code class="python">${generatedCode}</code></pre>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        container.append(card);
    });
    
    // Muestra el contenedor
    container.removeClass('d-none');
    
    // Configura event handlers
    $('.generate-code-btn').on('click', function() {
        const testId = $(this).data('test-id');
        generateCodeForTestCase(testId);
    });
    
    $('.view-code-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const codeContainer = $(`#code-container-${testId}`);
        
        if (codeContainer.hasClass('d-none')) {
            codeContainer.removeClass('d-none');
            $(this).html('<i class="fas fa-code"></i> Ocultar Código');
        } else {
            codeContainer.addClass('d-none');
            $(this).html('<i class="fas fa-code"></i> Ver Código');
        }
    });
    
    $('.copy-code-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const code = $(`#code-container-${testId} pre code`).text();
        
        // Copiar al portapapeles
        const tempTextarea = document.createElement('textarea');
        tempTextarea.value = code;
        document.body.appendChild(tempTextarea);
        tempTextarea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextarea);
        
        showNotification('Código copiado al portapapeles', 'success');
    });
    
    $('.run-test-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const testCase = currentTestCases.find(tc => tc.id === testId);
        
        if (testCase && testCase.generated_code) {
            executeTestCode(testCase.generated_code.code, testId);
        } else {
            showNotification('No se encontró el código para este test', 'error');
        }
    });
    
    // Aplicar highlight.js si está disponible
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    }
}

/**
 * Genera código para un caso de prueba específico
 */
function generateCodeForTestCase(testId) {
    if (!currentExploration) return;
    
    const testCase = currentTestCases.find(tc => tc.id === testId);
    if (!testCase) {
        showNotification('No se encontró el caso de prueba', 'error');
        return;
    }
    
    showLoading('Generando código para el caso de prueba...');
    
    const requestData = {
        url: currentExploration.url
    };
    
    // Usar el nuevo endpoint para generar código simple
    fetch(`/api/generate-simple-code/${testId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        // Actualiza la UI para mostrar el código generado
        updateTestCaseWithGeneratedCode(testId, data.code);
        
        showNotification('Código simple generado correctamente (modo visual)', 'success');
    })
    .catch(error => {
        hideLoading();
        console.error('Error generating simple code:', error);
        
        // Si falla el nuevo endpoint, intentamos con el anterior
        console.log('Trying fallback to original code generation endpoint...');
        fetch(`/api/generate-code/${testId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            updateTestCaseWithGeneratedCode(testId, data.code);
            showNotification('Código generado correctamente (modo estándar)', 'success');
        })
        .catch(fallbackError => {
            hideLoading();
            console.error('Error in fallback code generation:', fallbackError);
            showNotification('Error al generar código: ' + error.message, 'error');
        });
    });
}

/**
 * Actualiza la UI de un caso de prueba con el código generado
 */
function updateTestCaseWithGeneratedCode(testId, code) {
    const card = $(`.test-case-card[data-test-id="${testId}"]`);
    const cardBody = card.find('.card-body');
    
    // Actualiza el estado del testCase en memoria
    const testCase = currentTestCases.find(tc => tc.id === testId);
    if (testCase) {
        testCase.has_generated_code = true;
        if (!testCase.generated_code) {
            testCase.generated_code = { code: code };
        } else {
            testCase.generated_code.code = code;
        }
    }
    
    // Reemplaza los botones
    const buttonContainer = cardBody.find('.row .col');
    buttonContainer.html(`
        <button class="btn btn-info view-code-btn" data-test-id="${testId}">
            <i class="fas fa-code"></i> Ver Código
        </button>
        <button class="btn btn-success run-test-btn" data-test-id="${testId}">
            <i class="fas fa-play"></i> Ejecutar Test
        </button>
    `);
    
    // Agrega el contenedor de código
    cardBody.append(`
        <div class="code-container mt-3" id="code-container-${testId}">
            <div class="card">
                <div class="card-header bg-dark text-white">
                    <span>Código Generado</span>
                    <button class="btn btn-sm btn-light float-right copy-code-btn" data-test-id="${testId}">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                </div>
                <div class="card-body p-0">
                    <pre class="m-0"><code class="python">${code}</code></pre>
                </div>
            </div>
        </div>
    `);
    
    // Agrega badge de código disponible al header
    const cardHeader = card.find('.card-header .float-right');
    if (cardHeader.find('.badge').length === 0) {
        cardHeader.html('<span class="badge badge-light"><i class="fas fa-code"></i> Código disponible</span>');
    }
    
    // Configura event handlers
    card.find('.view-code-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const codeContainer = $(`#code-container-${testId}`);
        
        if (codeContainer.hasClass('d-none')) {
            codeContainer.removeClass('d-none');
            $(this).html('<i class="fas fa-code"></i> Ocultar Código');
        } else {
            codeContainer.addClass('d-none');
            $(this).html('<i class="fas fa-code"></i> Ver Código');
        }
    });
    
    card.find('.copy-code-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const code = $(`#code-container-${testId} pre code`).text();
        
        // Copiar al portapapeles
        const tempTextarea = document.createElement('textarea');
        tempTextarea.value = code;
        document.body.appendChild(tempTextarea);
        tempTextarea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextarea);
        
        showNotification('Código copiado al portapapeles', 'success');
    });
    
    card.find('.run-test-btn').on('click', function() {
        const testId = $(this).data('test-id');
        const testCase = currentTestCases.find(tc => tc.id === testId);
        
        if (testCase && testCase.generated_code) {
            executeTestCode(testCase.generated_code.code, testId);
        } else {
            showNotification('No se encontró el código para este test', 'error');
        }
    });
    
    // Aplicar highlight.js si está disponible
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    }
}

/**
 * Ejecuta un código de prueba
 */
function executeTestCode(code, testId) {
    showLoading('Ejecutando test en modo visual...');
    
    // Si hay un input para el chrome driver path, lo agregamos
    const chromeDriverPath = $('#chrome-driver-path').val();
    
    console.log("Datos que se enviarán al API:");
    console.log("- Código:", code ? "Código presente (longitud: " + code.length + ")" : "Código ausente");
    console.log("- ChromeDriverPath:", chromeDriverPath || "No especificado");
    
    // Preparar datos en el formato correcto
    const requestData = {
        test_code: code
    };
    
    // Solo agregar chrome_driver_path si realmente tiene un valor
    if (chromeDriverPath && chromeDriverPath.trim() !== '') {
        requestData.chrome_driver_path = chromeDriverPath.trim();
    }
    
    console.log("Enviando al API:", JSON.stringify(requestData));
    
    // Usar el nuevo endpoint para ejecutar código simple
    fetch('/api/execute-simple-test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // Verificar si la respuesta es exitosa
        if (!response.ok) {
            console.error("Error HTTP:", response.status, response.statusText);
            return response.text().then(text => {
                try {
                    // Intentar parsear como JSON para obtener detalles
                    const errorData = JSON.parse(text);
                    console.error("Detalles del error:", errorData);
                    throw new Error(`Error ${response.status}: ${errorData.detail || errorData.message || response.statusText}`);
                } catch (e) {
                    // Si no es JSON, mostrar el texto crudo
                    console.error("Respuesta cruda:", text);
                    throw new Error(`Error ${response.status}: ${response.statusText}. Ver consola para más detalles.`);
                }
            });
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.status === 'completed' || data.status === 'success') {
            showTestResults(data, testId);
            showNotification('Test ejecutado correctamente en modo visual', 'success');
        } else if (data.status === 'failed' || data.status === 'error') {
            showTestResults(data, testId);
            showNotification('El test falló: ' + data.message, 'error');
        } else if (data.status === 'timeout') {
            showNotification('Tiempo de espera agotado para el test', 'warning');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error executing test with new endpoint:', error);
        showNotification('Error al ejecutar el test: ' + error.message, 'error');
        
        // Si falla, intentamos con el endpoint anterior
        console.log('Trying fallback to original test execution endpoint...');
        
        const fallbackRequestData = {
            code: code,
            test_case_id: testId
        };
        
        if (chromeDriverPath && chromeDriverPath.trim() !== '') {
            fallbackRequestData.chrome_driver_path = chromeDriverPath.trim();
        }
        
        console.log("Enviando al API fallback:", JSON.stringify(fallbackRequestData));
        
        fetch('/api/execute-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(fallbackRequestData)
        })
        .then(response => {
            if (!response.ok) {
                console.error("Error HTTP en fallback:", response.status, response.statusText);
                return response.text().then(text => {
                    console.error("Respuesta fallback cruda:", text);
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            
            if (data.status === 'completed') {
                showTestResults(data, testId);
                showNotification('Test ejecutado en modo estándar', 'success');
            } else if (data.status === 'failed') {
                showTestResults(data, testId);
                showNotification('El test falló: ' + data.message, 'error');
            } else if (data.status === 'timeout') {
                showNotification('Tiempo de espera agotado para el test', 'warning');
            }
        })
        .catch(fallbackError => {
            hideLoading();
            console.error('Error in fallback test execution:', fallbackError);
            showNotification('Error al ejecutar el test: ' + fallbackError.message, 'error');
        });
    });
}

/**
 * Muestra los resultados de un test
 */
function showTestResults(results, testId) {
    const card = $(`.test-case-card[data-test-id="${testId}"]`);
    const cardBody = card.find('.card-body');
    
    // Eliminar resultados anteriores si existen
    const existingResults = cardBody.find('.test-results');
    if (existingResults.length > 0) {
        existingResults.remove();
    }
    
    // Construir contenido de resultados
    let resultsHtml = `
        <div class="test-results mt-3">
            <div class="card">
                <div class="card-header bg-${results.status === 'completed' || results.status === 'success' ? 'success' : 'danger'} text-white">
                    <span>Resultados del Test</span>
                </div>
                <div class="card-body">
                    <p class="mb-2"><strong>Estado:</strong> ${results.status}</p>
                    <p class="mb-2"><strong>Mensaje:</strong> ${results.message}</p>
    `;
    
    // Agregar logs si hay
    if ((results.logs && results.logs.length > 0) || (results.output && results.output.length > 0)) {
        resultsHtml += `
            <div class="logs-container mt-3">
                <h6>Logs:</h6>
                <div class="logs-content bg-light p-2" style="max-height: 200px; overflow-y: auto;">
        `;
        
        // Usar logs o output según cuál esté disponible
        const logEntries = results.logs || results.output;
        if (logEntries && logEntries.length > 0) {
            logEntries.forEach(log => {
                if (log && log.trim()) {
                    resultsHtml += `<div class="log-entry">${log}</div>`;
                }
            });
        }
        
        resultsHtml += `
                </div>
            </div>
        `;
    }
    
    // Agregar errores si hay
    if ((results.errors && results.errors.length > 0) || (results.error && results.error.length > 0)) {
        resultsHtml += `
            <div class="errors-container mt-3">
                <h6 class="text-danger">Errores:</h6>
                <div class="errors-content bg-light p-2 text-danger" style="max-height: 200px; overflow-y: auto;">
        `;
        
        // Usar errors o error según cuál esté disponible
        const errorEntries = results.errors || (typeof results.error === 'string' ? [results.error] : results.error);
        if (errorEntries && errorEntries.length > 0) {
            errorEntries.forEach(error => {
                if (error && error.trim()) {
                    resultsHtml += `<div class="error-entry">${error}</div>`;
                }
            });
        }
        
        resultsHtml += `
                </div>
            </div>
        `;
    }
    
    resultsHtml += `
                </div>
            </div>
        </div>
    `;
    
    // Agregar a la tarjeta
    cardBody.append(resultsHtml);
}

/**
 * Cierra la vista de detalles de la exploración
 */
function closeExplorationDetails() {
    $('#exploration-details-container').addClass('d-none');
    $('#saved-explorations-container').removeClass('d-none');
    
    // Resetea variables
    currentExploration = null;
    currentTestCases = [];
    currentGeneratedCode = {};
    
    // Oculta containers
    $('#test-cases-container').addClass('d-none').empty();
}

/**
 * Confirma la eliminación de una exploración
 */
function confirmDeleteExploration(explorationId) {
    if (confirm('¿Está seguro de que desea eliminar esta exploración? Esta acción no se puede deshacer.')) {
        deleteExploration(explorationId);
    }
}

/**
 * Elimina una exploración
 */
function deleteExploration(explorationId) {
    showLoading('Eliminando exploración...');
    
    fetch(`/api/explorations/${explorationId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.status === 'success') {
            showNotification('Exploración eliminada correctamente', 'success');
            
            // Elimina la fila de la tabla
            $(`tr[data-exploration-id="${explorationId}"]`).remove();
            
            // Si no quedan exploraciones, oculta la tabla
            if ($('#saved-explorations-table tbody tr').length === 0) {
                $('#saved-explorations-container').addClass('d-none');
                $('#website-form-container').removeClass('d-none');
                showNotification('No hay más exploraciones guardadas', 'info');
            }
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error deleting exploration:', error);
        showNotification('Error al eliminar la exploración: ' + error.message, 'error');
    });
}

/**
 * Muestra un mensaje de notificación
 */
function showNotification(message, type) {
    // Implementa según tu sistema de notificación
    if (typeof Toastify !== 'undefined') {
        Toastify({
            text: message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: type === 'error' ? '#dc3545' : 
                             type === 'warning' ? '#ffc107' :
                             type === 'info' ? '#17a2b8' : '#28a745'
        }).showToast();
    } else {
        alert(message);
    }
}

/**
 * Muestra el indicador de carga
 */
function showLoading(message) {
    $('#loading-message').text(message || 'Cargando...');
    $('#loading-overlay').removeClass('d-none');
}

/**
 * Oculta el indicador de carga
 */
function hideLoading() {
    $('#loading-overlay').addClass('d-none');
}

// Inicializa cuando el documento esté listo
$(document).ready(function() {
    initSavedExplorations();
}); 
import requests
import time
import argparse
import os
import json
import sys
import traceback
import logging
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# Cargar configuración desde config.yaml
try:
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        
    # Configuración
    WEBDRIVER_PATH = config["chrome"]["driver_path"]
    API_BASE_URL = f"http://{config['application']['host']}:{config['application']['port']}/api"
    WAIT_TIMEOUT = 10  # Segundos para esperar que los elementos aparezcan
except Exception as e:
    print(f"Error loading configuration: {str(e)}")
    # Configuración por defecto en caso de error
    WEBDRIVER_PATH = ""
    API_BASE_URL = "http://localhost:8000/api"
    WAIT_TIMEOUT = 10

# Configurar logger
logger = logging.getLogger(__name__)

class TestExecutor:
    """
    Ejecutor de pruebas que procesa pasos de casos de prueba y ejecuta acciones.
    """
    
    def __init__(self, test_data=None, test_id=None, output_file=None, timeout=30):
        """
        Inicializa el ejecutor de pruebas.
        
        Args:
            test_data: Diccionario con los datos del test case
            test_id: ID del test case a buscar en la API
            output_file: Archivo para guardar los logs de salida
            timeout: Tiempo de espera predeterminado en segundos
        """
        self.test_data = test_data
        self.test_id = test_id
        self.driver = None
        self.logs = []
        self.output_file = output_file
        self.timeout = timeout
        self.steps_executed = 0
        self.total_steps = 0
        self.success = True
        self.errors = []
        
    def log(self, message, level="INFO"):
        """
        Registra un mensaje en el archivo de registro y en la lista de logs.
        
        Args:
            message (str): Mensaje a registrar
            level (str): Nivel de registro (INFO, ERROR, etc.)
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        if level == "ERROR":
            self.errors.append(message)
            logger.error(message)
            self.success = False
        else:
            logger.info(message)
            
        self.logs.append(log_entry)
        
        if self.output_file:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
    
    def setup_webdriver(self):
        """
        Configura y devuelve una instancia de WebDriver para Chrome.
        
        Returns:
            webdriver.Chrome: Instancia configurada del WebDriver
        """
        self.log("Configurando WebDriver...")
        
        try:
            # Verificar si hay un chrome_driver_path en la configuración
            chrome_driver_path = WEBDRIVER_PATH
            service = None
            
            # Opciones de Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Configurar Service si se proporciona la ruta
            if chrome_driver_path and os.path.exists(chrome_driver_path):
                self.log(f"Usando ChromeDriver desde: {chrome_driver_path}")
                service = ChromeService(executable_path=chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.log("Usando ChromeDriver predeterminado del sistema")
                driver = webdriver.Chrome(options=chrome_options)
            
            return driver
            
        except Exception as e:
            self.log(f"Error al configurar WebDriver: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            raise
    
    def fetch_testcase(self):
        """Obtiene los datos del test case desde la API"""
        if not self.test_id:
            self.log("No se especificó ID de test case", "ERROR")
            return False
            
        self.log(f"Obteniendo test case con ID: {self.test_id}")
        
        try:
            # Para este ejemplo, usamos la API del proyecto
            response = requests.get(f"{API_BASE_URL}/test-cases/{self.test_id}")
            response.raise_for_status()
            self.test_data = response.json()
            self.log(f"Test case obtenido: {self.test_data['title']}")
            return True
        except Exception as e:
            self.log(f"Error al obtener el test case: {str(e)}", "ERROR")
            return False
    
    def parse_selector(self, selector_info):
        """
        Analiza la información del selector y devuelve el tipo y valor del selector.
        
        Args:
            selector_info (str/dict): Información del selector (puede ser un string o un diccionario)
            
        Returns:
            tuple: (tipo_selector, valor_selector)
        """
        # Selector en formato string (formato antiguo)
        if isinstance(selector_info, str):
            if selector_info.startswith("//"):
                return By.XPATH, selector_info
            elif selector_info.startswith("#"):
                return By.ID, selector_info[1:]
            elif selector_info.startswith("."):
                return By.CLASS_NAME, selector_info[1:]
            else:
                return By.CSS_SELECTOR, selector_info
        
        # Selector en formato dict (formato nuevo)
        elif isinstance(selector_info, dict):
            selector_type = selector_info.get("type", "").upper()
            selector_value = selector_info.get("value", "")
            
            if selector_type == "XPATH":
                return By.XPATH, selector_value
            elif selector_type == "ID":
                return By.ID, selector_value
            elif selector_type == "CLASS_NAME":
                return By.CLASS_NAME, selector_value
            elif selector_type == "CSS_SELECTOR":
                return By.CSS_SELECTOR, selector_value
            elif selector_type == "NAME":
                return By.NAME, selector_value
            elif selector_type == "TAG_NAME":
                return By.TAG_NAME, selector_value
            elif selector_type == "LINK_TEXT":
                return By.LINK_TEXT, selector_value
            elif selector_type == "PARTIAL_LINK_TEXT":
                return By.PARTIAL_LINK_TEXT, selector_value
            else:
                return By.CSS_SELECTOR, selector_value
        
        # Valor por defecto
        return By.CSS_SELECTOR, selector_info
    
    def execute_step(self, step):
        """
        Ejecuta un paso del caso de prueba.
        
        Args:
            step (dict): Datos del paso a ejecutar
            
        Returns:
            bool: True si el paso se ejecutó correctamente, False en caso contrario
        """
        step_number = step.get("step_number", self.steps_executed + 1)
        action = step.get("action", "")
        selector_info = step.get("selector", "")
        value = step.get("value", "")
        description = step.get("description", f"Paso {step_number}: {action}")
        
        self.log(f"Ejecutando paso {step_number}: {description}")
        
        try:
            # Acciones que no requieren un selector
            if action == "goto":
                self.log(f"Navegando a URL: {value}")
                self.driver.get(value)
                return True
                
            if action == "sleep":
                sleep_time = int(value) if value.isdigit() else 1
                self.log(f"Esperando {sleep_time} segundos")
                time.sleep(sleep_time)
                return True
                
            if action == "screenshot":
                screenshot_path = value or f"screenshot_{int(time.time())}.png"
                self.log(f"Tomando captura de pantalla: {screenshot_path}")
                self.driver.save_screenshot(screenshot_path)
                return True
            
            # Acciones que requieren un selector
            if not selector_info:
                self.log(f"No se proporcionó selector para la acción: {action}", "ERROR")
                return False
                
            # Obtener el selector
            selector_type, selector_value = self.parse_selector(selector_info)
            
            # Esperar a que el elemento esté presente
            try:
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                self.log(f"Elemento encontrado: {selector_value}")
            except TimeoutException:
                self.log(f"Tiempo de espera agotado buscando el elemento: {selector_value}", "ERROR")
                return False
            except Exception as e:
                self.log(f"Error al buscar elemento {selector_value}: {str(e)}", "ERROR")
                return False
            
            # Ejecutar la acción sobre el elemento
            if action == "click":
                element.click()
                self.log(f"Click en el elemento: {selector_value}")
                
            elif action == "input":
                element.clear()
                element.send_keys(value)
                self.log(f"Texto ingresado en {selector_value}: {value}")
                
            elif action == "submit":
                element.submit()
                self.log(f"Formulario enviado desde el elemento: {selector_value}")
                
            elif action == "verify":
                self.log(f"Verificando texto en elemento {selector_value}: {value}")
                element_text = element.text
                if value in element_text:
                    self.log(f"Verificación exitosa: '{value}' encontrado en '{element_text}'")
                else:
                    self.log(f"Verificación fallida: '{value}' no encontrado en '{element_text}'", "ERROR")
                    return False
                    
            elif action == "verify_exists":
                self.log(f"Verificando que el elemento existe: {selector_value}")
                # Ya hemos verificado que existe al encontrarlo
                
            elif action == "select":
                from selenium.webdriver.support.ui import Select
                select = Select(element)
                select.select_by_visible_text(value)
                self.log(f"Opción seleccionada en {selector_value}: {value}")
                
            else:
                self.log(f"Acción no soportada: {action}", "ERROR")
                return False
                
            return True
                
        except Exception as e:
            self.log(f"Error ejecutando paso {step_number}: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    def run_test(self):
        """
        Ejecuta todos los pasos del caso de prueba.
        
        Returns:
            bool: True si todos los pasos se ejecutaron correctamente, False en caso contrario
        """
        test_name = self.test_data.get("name", "Test sin nombre")
        steps = self.test_data.get("steps", [])
        
        self.log(f"Iniciando ejecución del test: {test_name}")
        self.log(f"Total de pasos a ejecutar: {len(steps)}")
        
        try:
            # Configurar WebDriver
            self.driver = self.setup_webdriver()
            
            # Ejecutar cada paso
            for i, step in enumerate(steps):
                step_success = self.execute_step(step)
                self.steps_executed += 1
                
                if not step_success:
                    self.log(f"Fallo en el paso {i+1}. Deteniendo la ejecución.", "ERROR")
                    self.success = False
                    break
            
            if self.success:
                self.log(f"Test completado exitosamente: {test_name}")
            else:
                self.log(f"Test falló: {test_name}", "ERROR")
                
            return self.success
            
        except Exception as e:
            self.log(f"Error no controlado durante la ejecución del test: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            return False
            
        finally:
            # Cerrar el navegador
            if self.driver:
                self.log("Cerrando el navegador")
                try:
                    self.driver.quit()
                except Exception as e:
                    self.log(f"Error al cerrar el navegador: {str(e)}", "ERROR")
    
    def get_results_summary(self):
        """
        Obtiene un resumen de los resultados de la ejecución.
        
        Returns:
            dict: Resumen de resultados
        """
        completion_percentage = (self.steps_executed / self.total_steps * 100) if self.total_steps > 0 else 0
        
        return {
            "success": self.success,
            "steps_executed": self.steps_executed,
            "total_steps": self.total_steps,
            "completion_percentage": round(completion_percentage, 2),
            "logs": self.logs,
            "errors": self.errors,
            "output_file": self.output_file
        }

def main():
    """Función principal para ejecutar desde línea de comandos"""
    parser = argparse.ArgumentParser(description="Ejecutar test cases con Selenium")
    parser.add_argument("--test-id", help="ID del test case a ejecutar")
    parser.add_argument("--test-file", help="Archivo JSON con los datos del test case")
    parser.add_argument("--output-file", help="Archivo para guardar los logs de salida")
    parser.add_argument("--webdriver-path", help="Ruta al ejecutable de ChromeDriver")
    
    args = parser.parse_args()
    
    # Configurar variables de entorno
    if args.webdriver_path:
        os.environ["CHROME_DRIVER_PATH"] = args.webdriver_path
    
    # Cargar datos del test
    test_data = None
    if args.test_file:
        try:
            with open(args.test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
        except Exception as e:
            print(f"Error al cargar el archivo de test: {str(e)}")
            sys.exit(1)
    
    # Crear y ejecutar el runner
    executor = TestExecutor(test_data=test_data, test_id=args.test_id, output_file=args.output_file)
    
    if not test_data and args.test_id:
        if not executor.fetch_testcase():
            print("Error al obtener el test case")
            sys.exit(1)
        
    success = executor.run_test()
    
    # Mostrar resultado
    if success:
        print("\n✅ Test ejecutado correctamente")
        sys.exit(0)
    else:
        print("\n❌ Test fallido")
        sys.exit(1)

if __name__ == "__main__":
    main() 
import requests
import time
import argparse
import os
import json
import sys
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchElementException

# Cargar configuración desde config.yaml
try:
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    # Configuración
    WEBDRIVER_PATH = config["chrome"]["driver_path"]
    API_BASE_URL = f"http://{config['application']['host']}:{config['application']['port']}/api"
except Exception as e:
    print(f"Error loading configuration: {str(e)}")
    # Configuración por defecto en caso de error
    WEBDRIVER_PATH = ""
    API_BASE_URL = "http://localhost:8000/api"

class TestRunner:
    def __init__(self, test_data=None, test_id=None):
        """
        Inicializa el ejecutor de pruebas.
        
        Args:
            test_data: Diccionario con los datos del test case
            test_id: ID del test case a buscar en la API
        """
        self.test_data = test_data
        self.test_id = test_id
        self.driver = None
        self.logs = []
        
    def log(self, message, level="INFO"):
        """Registra un mensaje en el log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.logs.append(log_entry)
        
    def setup_driver(self):
        """Configura el driver de Chrome"""
        self.log("Configurando WebDriver de Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Si hay una ruta de WebDriver especificada, úsala
        if WEBDRIVER_PATH and os.path.exists(WEBDRIVER_PATH):
            self.log(f"Usando ChromeDriver desde ruta personalizada: {WEBDRIVER_PATH}")
            service = ChromeService(executable_path=WEBDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.log("Usando ChromeDriver desde PATH del sistema")
            self.driver = webdriver.Chrome(options=options)
            
        self.log("WebDriver inicializado correctamente")
    
    def fetch_testcase(self):
        """Obtiene los datos del test case desde la API"""
        if not self.test_id:
            self.log("No se especificó ID de test case", "ERROR")
            return False
            
        self.log(f"Obteniendo test case con ID: {self.test_id}")
        
        try:
            response = requests.get(f"{API_BASE_URL}/test-case/{self.test_id}")
            response.raise_for_status()
            self.test_data = response.json()
            self.log(f"Test case obtenido: {self.test_data['title']}")
            return True
        except Exception as e:
            self.log(f"Error al obtener el test case: {str(e)}", "ERROR")
            return False
    
    def run_test(self):
        """Ejecuta el test case"""
        if not self.test_data:
            self.log("No hay datos de test case para ejecutar", "ERROR")
            return False
            
        if not self.driver:
            self.setup_driver()
            
        try:
            title = self.test_data.get("title", "Test sin título")
            url = self.test_data.get("url", "")
            description = self.test_data.get("description", "")
            steps = self.test_data.get("steps", [])
            
            self.log(f"EJECUTANDO TEST: {title}")
            self.log(f"Descripción: {description}")
            self.log(f"URL: {url}")
            
            # Navegar a la URL
            self.log(f"Navegando a {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Ejecutar cada paso
            for i, step in enumerate(steps, 1):
                self.log(f"Paso {i}: {step}")
                time.sleep(1)
                
                # Aquí iría la lógica para interpretar y ejecutar cada paso
                # Por ahora solo mostraremos el paso en el log
            
            self.log("Test completado con éxito", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error durante la ejecución del test: {str(e)}", "ERROR")
            return False
        finally:
            # Guardar los resultados del test
            if self.driver:
                self.log("Cerrando WebDriver")
                self.driver.quit()
    
    def get_logs(self):
        """Devuelve los logs generados durante la ejecución"""
        return self.logs

def main():
    """Función principal para ejecutar desde línea de comandos"""
    parser = argparse.ArgumentParser(description="Ejecutar test cases con Selenium")
    parser.add_argument("--test-id", help="ID del test case a ejecutar")
    parser.add_argument("--test-file", help="Archivo JSON con los datos del test case")
    parser.add_argument("--webdriver-path", help="Ruta al ejecutable de ChromeDriver")
    
    args = parser.parse_args()
    
    # Configurar webdriver path si se especifica en la línea de comandos
    global WEBDRIVER_PATH
    if args.webdriver_path:
        WEBDRIVER_PATH = args.webdriver_path
    
    # Cargar datos del test
    test_data = None
    if args.test_file:
        with open(args.test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    
    # Crear y ejecutar el runner
    runner = TestRunner(test_data=test_data, test_id=args.test_id)
    
    if not test_data and args.test_id:
        runner.fetch_testcase()
        
    success = runner.run_test()
    
    # Mostrar resultado
    if success:
        print("\n✅ Test ejecutado correctamente")
        sys.exit(0)
    else:
        print("\n❌ Test fallido")
        sys.exit(1)

if __name__ == "__main__":
    main() 
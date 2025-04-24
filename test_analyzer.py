#!/usr/bin/env python
"""
Script para probar el análisis de sitios web con mayor profundidad
"""
import os
import sys
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("test-analyzer")

# Agregar la carpeta raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el analizador
from app.core.web_analyzer import WebAnalyzer

def analyze_website(url):
    """Analizar un sitio web y mostrar estadísticas"""
    logger.info(f"Iniciando análisis de: {url}")
    
    # Crear analizador y ejecutar análisis
    analyzer = WebAnalyzer(url)
    result = analyzer.analyze()
    
    # Mostrar estadísticas
    logger.info("Análisis completado:")
    logger.info(f"URL: {result['url']}")
    logger.info(f"Dominio: {result['domain']}")
    logger.info(f"Categoría: {result['category']}")
    logger.info(f"Número de páginas: {result['node_count']}")
    logger.info(f"Número de enlaces: {result['edge_count']}")
    logger.info(f"Visualización generada en: {result['visualization_path']}")
    
    # Mostrar la jerarquía de primer nivel
    logger.info("Primer nivel de jerarquía:")
    for child in result['hierarchy'].get('children', []):
        logger.info(f"  - {child['title']} ({child['url']})")
    
    return result

if __name__ == "__main__":
    # URL para analizar (puedes cambiarla o pasarla como parámetro)
    test_url = "https://www.example.com"
    
    # Si se proporciona una URL como argumento, usarla
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    # Ejecutar análisis
    analyze_website(test_url)
    logger.info("Prueba completada. Revisa los archivos generados en app/static/") 
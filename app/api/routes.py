from fastapi import APIRouter, HTTPException, Form, Depends
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from app.core.web_analyzer import WebAnalyzer
from app.core.test_generator import TestCaseGenerator
from app.core.code_generator import CodeGenerator
import json
import os
import time
import sys

# Set up logger
logger = logging.getLogger("web-analysis-framework.api")

router = APIRouter()

class UrlInput(BaseModel):
    url: HttpUrl

class NodeInput(BaseModel):
    url: HttpUrl
    node_url: Optional[str] = None

class TestCase(BaseModel):
    id: int
    title: str
    description: str
    steps: List[str]
    expected_results: List[str]

class GeneratedCode(BaseModel):
    test_case_id: int
    code: str

@router.post("/analyze")
async def analyze_website(url_input: UrlInput):
    logger.info(f"API request: Analyze website {url_input.url}")
    try:
        analyzer = WebAnalyzer(str(url_input.url))
        result = analyzer.analyze()
        logger.info(f"Analysis completed successfully for {url_input.url}")
        return result
    except Exception as e:
        logger.error(f"Analysis failed for {url_input.url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/website-structure")
async def get_website_structure():
    """Get the stored website structure"""
    logger.info("API request: Get website structure")
    try:
        structure_file = "app/static/website_structure.json"
        if not os.path.exists(structure_file):
            raise HTTPException(status_code=404, detail="No website structure available. Please analyze a website first.")
            
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)
            
        return structure
    except Exception as e:
        logger.error(f"Error retrieving website structure: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving website structure: {str(e)}")

@router.post("/generate-tests")
async def generate_test_cases(node_input: NodeInput):
    logger.info(f"API request: Generate test cases for {node_input.url}")
    try:
        # Check if we need to do a full analysis or can use existing data
        website_structure_path = os.path.join("app", "static", "website_structure.json")
        
        if os.path.exists(website_structure_path):
            logger.info(f"Using existing website structure from {website_structure_path}")
            
            # Load existing structure
            with open(website_structure_path, "r", encoding="utf-8") as f:
                analysis_result = json.load(f)
                
            # Check if this is for the same URL - if not, do a new analysis
            if analysis_result.get("url") != str(node_input.url):
                logger.info(f"Existing structure is for different URL, doing new analysis")
                analyzer = WebAnalyzer(str(node_input.url))
                analysis_result = analyzer.analyze()
        else:
            # No existing data, do a full analysis
            logger.info(f"No existing structure found, doing new analysis")
            analyzer = WebAnalyzer(str(node_input.url))
            analysis_result = analyzer.analyze()
        
        test_generator = TestCaseGenerator(analysis_result)
        
        # If node_url is provided, generate tests for that specific node
        if node_input.node_url:
            logger.info(f"Generating test cases for specific node: {node_input.node_url}")
            test_cases = test_generator.generate_test_cases_for_node(node_input.node_url)
        else:
            # Otherwise, generate tests for the entire site
            test_cases = test_generator.generate_test_cases()
            
        logger.info(f"Generated {len(test_cases)} test cases")
        return test_cases
    except Exception as e:
        logger.error(f"Test case generation failed for {node_input.url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test case generation failed: {str(e)}")

@router.post("/generate-code/{test_case_id}")
async def generate_code(test_case_id: int, node_input: NodeInput):
    logger.info(f"API request: Generate code for test case {test_case_id} on {node_input.url}")
    try:
        analyzer = WebAnalyzer(str(node_input.url))
        analysis_result = analyzer.analyze()
        test_generator = TestCaseGenerator(analysis_result)
        
        # Generate test cases based on node if provided
        if node_input.node_url:
            test_cases = test_generator.generate_test_cases_for_node(node_input.node_url)
        else:
            test_cases = test_generator.generate_test_cases()
        
        # Find the requested test case
        test_case = next((tc for tc in test_cases if tc["id"] == test_case_id), None)
        if not test_case:
            logger.warning(f"Test case {test_case_id} not found")
            raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found")
        
        code_generator = CodeGenerator()
        code = code_generator.generate_code(test_case, str(node_input.url))
        logger.info(f"Code generated successfully for test case {test_case_id}")
        return {"test_case_id": test_case_id, "code": code["code"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code generation failed for test case {test_case_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

@router.get("/preview-page")
async def preview_page(url: str):
    """Generate a preview/screenshot of a page if possible
    
    In a production system, this would use a headless browser to capture a screenshot.
    For this demo, we'll simply redirect to the URL, but in a real application you would:
    1. Use a library like Playwright or Puppeteer to capture screenshots
    2. Cache screenshots to improve performance
    3. Include security checks for the URLs
    4. Add rate limiting to prevent abuse
    """
    logger.info(f"API request: Preview page {url}")
    
    try:
        # In a real implementation, you would return a screenshot
        # For the demo, we'll return a JSON with the original URL
        return {"url": url, "message": "In a production system, this would return a screenshot"}
    except Exception as e:
        logger.error(f"Error generating page preview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@router.get("/page-info/{encoded_url:path}")
async def get_page_info(encoded_url: str):
    """Get detailed information about a specific page from website structure
    
    This endpoint returns metadata and analysis for a single page
    """
    import base64
    import urllib.parse
    
    logger.info(f"API request: Get page info {encoded_url}")
    
    try:
        # Decode the URL
        decoded_url = base64.b64decode(encoded_url).decode('utf-8')
        url = urllib.parse.unquote(decoded_url)
        
        # Load website structure
        structure_file = "app/static/website_structure.json"
        if not os.path.exists(structure_file):
            raise HTTPException(status_code=404, detail="No website structure available")
            
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)
            
        # Find the page in the structure
        if url not in structure["pages"]:
            raise HTTPException(status_code=404, detail=f"Page {url} not found in website structure")
            
        # Return page info
        page_info = structure["pages"][url]
        
        # Enhance with path information
        paths = []
        for page_url, info in structure["pages"].items():
            if info.get("parent") == url:
                paths.append({
                    "url": page_url,
                    "title": info.get("title", "Unknown"),
                    "path": info.get("path", "/")
                })
        
        # Add child pages
        return {
            "url": url,
            "info": page_info,
            "child_pages": paths
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving page info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving page info: {str(e)}")

@router.post("/execute-test")
async def execute_test_code(request: dict):
    """Execute generated test code using Selenium WebDriver
    
    This endpoint accepts generated code and executes it in a controlled environment
    """
    logger.info(f"API request: Execute test code")
    
    try:
        code_to_execute = request.get("code", "")
        test_id = request.get("test_case_id")
        chrome_driver_path = request.get("chrome_driver_path", "")
        should_execute = request.get("execute", False)
        
        if not code_to_execute:
            raise HTTPException(status_code=400, detail="No code provided")
            
        # Create a temporary Python file with the code
        temp_file_path = os.path.join("app", "static", "temp", f"test_{test_id}_{int(time.time())}.py")
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        # Add environment variable for ChromeDriver if provided
        env_vars = os.environ.copy()
        if chrome_driver_path and os.path.exists(chrome_driver_path):
            # Add a comment at the top of the file for visibility
            chrome_driver_comment = f"# Using ChromeDriver from: {chrome_driver_path}\n"
            code_to_execute = chrome_driver_comment + code_to_execute
            logger.info(f"Using custom ChromeDriver path: {chrome_driver_path}")
            env_vars["CHROME_DRIVER_PATH"] = chrome_driver_path
        
        with open(temp_file_path, "w") as f:
            f.write(code_to_execute)
            
        logger.info(f"Test code saved to {temp_file_path}")
        
        # Actually execute the test if requested
        execution_info = {}
        if should_execute:
            try:
                import subprocess
                
                # Run the Python file in a separate process
                logger.info(f"Executing test file: {temp_file_path}")
                process = subprocess.Popen(
                    [sys.executable, temp_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env_vars
                )
                
                # Store process ID for future reference
                execution_info = {
                    "pid": process.pid,
                    "started_at": time.time(),
                    "status": "running"
                }
                logger.info(f"Test process started with PID: {process.pid}")
                
            except Exception as exec_error:
                logger.error(f"Error starting test process: {str(exec_error)}", exc_info=True)
                execution_info = {
                    "error": str(exec_error),
                    "status": "failed_to_start"
                }
        
        return {
            "status": "success", 
            "message": "Test execution initiated" if should_execute else "Test code saved", 
            "test_id": test_id,
            "file_path": temp_file_path,
            "execution": execution_info,
            "view_instructions": "The test will run in a visible Chrome browser window. If you don't see it, make sure Chrome is installed and ChromeDriver path is correctly configured."
        }
    except Exception as e:
        logger.error(f"Error executing test code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing test code: {str(e)}")

@router.get("/test-status/{test_id}")
async def test_execution_status(test_id: str):
    """Get the status of a running test
    
    This endpoint would poll the status of a running test and return logs/progress
    """
    logger.info(f"API request: Get test execution status for test {test_id}")
    
    try:
        # In a real implementation, this would check the actual test status
        # For the demo, we'll return a simulated status
        import random
        
        status_options = ["running", "completed", "failed"]
        weights = [0.3, 0.6, 0.1]  # 30% running, 60% completed, 10% failed
        status = random.choices(status_options, weights)[0]
        
        logs = []
        if status == "running":
            logs = [
                {"type": "log", "message": "Starting WebDriver session..."},
                {"type": "log", "message": "Navigating to target website..."},
                {"type": "log", "message": "Page loaded successfully"},
                {"type": "log", "message": "Executing test steps..."}
            ]
        elif status == "completed":
            logs = [
                {"type": "log", "message": "Starting WebDriver session..."},
                {"type": "log", "message": "Navigating to target website..."},
                {"type": "log", "message": "Page loaded successfully"},
                {"type": "log", "message": "Executing test steps..."},
                {"type": "log", "message": "All steps completed"},
                {"type": "status", "message": "Test completed successfully"}
            ]
        else:
            logs = [
                {"type": "log", "message": "Starting WebDriver session..."},
                {"type": "log", "message": "Navigating to target website..."},
                {"type": "log", "message": "Page loaded successfully"},
                {"type": "log", "message": "Executing test steps..."},
                {"type": "error", "message": "Error: Element not found: CSS selector '.invalid-selector'"}
            ]
            
        return {
            "test_id": test_id,
            "status": status,
            "logs": logs,
            "completion": 100 if status != "running" else random.randint(10, 90)
        }
    except Exception as e:
        logger.error(f"Error getting test status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting test status: {str(e)}") 
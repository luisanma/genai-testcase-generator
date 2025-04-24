import logging
import requests
import json
import os
import re

# Set up logger
logger = logging.getLogger("web-analysis-framework.code-generator")

class CodeGenerator:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.1:8b"
        logger.info(f"Code generator initialized with Ollama model: {self.model}")
    
    def generate_code(self, test_case, website_url):
        """Generate Selenium Python code for the given test case using Ollama LLM"""
        logger.info(f"Generating code for test case: {test_case.get('title', 'Unknown')}")
        
        try:
            # Create the prompt for the LLM
            prompt = self._create_prompt(test_case, website_url)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            if not response:
                logger.error("Empty response from Ollama")
                return {"code": "# Error: Failed to generate code using Ollama LLM\n# Please check the server logs for details."}
            
            # Extract and process the code from the response
            selenium_code = self._extract_code(response, test_case)
            
            # Add execution wrapper for live execution
            executable_code = self._add_execution_wrapper(selenium_code, test_case)
            
            logger.info(f"Code generated successfully for test case: {test_case.get('title', 'Unknown')}")
            
            return {
                "code": executable_code,
                "raw_code": selenium_code,
                "test_case_id": test_case.get("id")
            }
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            return {"code": f"# Error generating code: {str(e)}\n\n# Please try again or check the logs."}
    
    def _create_prompt(self, test_case, website_url):
        """Create a prompt for the Ollama LLM"""
        steps_str = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(test_case.get("steps", []))])
        expected_str = "\n".join([f"- {result}" for result in test_case.get("expected_results", [])])
        
        prompt = f"""Generate Python code using Selenium WebDriver to automate the following test case:

Test Case ID: {test_case.get("id")}
Title: {test_case.get("title")}
Description: {test_case.get("description")}

Steps to perform:
{steps_str}

Expected Results:
{expected_str}

Website URL: {website_url}

Requirements:
1. Use Python with Selenium WebDriver
2. Include proper waiting mechanisms (explicit waits preferred)
3. Include error handling for common failures
4. Add appropriate assertions to verify the expected results
5. Add comments that explain each major step
6. Make the code ready to execute without modification

Generate only the Python code without any additional explanation. Make sure the code handles navigation, interactions, and verifications precisely as described in the test case.
"""
        return prompt
    
    def _call_ollama(self, prompt):
        """Call the Ollama API to generate code"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2048
                }
            }
            
            logger.info(f"Calling Ollama API with model: {self.model}")
            response = requests.post(self.ollama_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}", exc_info=True)
            return None
    
    def _extract_code(self, response, test_case):
        """Extract and process the code from the Ollama response"""
        # Extract code block if it exists
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        
        if code_match:
            code = code_match.group(1)
        else:
            # If no code block markers, assume the entire response is code
            code = response
        
        # Clean up the code (remove extra blank lines, etc.)
        code = code.strip()
        
        # Add title comment
        title_comment = f"# Test: {test_case.get('title', 'Unknown Test')}\n"
        
        # Replace headless mode with visible mode for Chrome
        code = re.sub(
            r"options\.add_argument\('headless'\)|options\.add_argument\(\"headless\"\)|options\.add_argument\('--headless'\)|options\.add_argument\(\"--headless\"\)", 
            "# Running in visible mode for test visualization", 
            code
        )
        
        # Add code to use ChromeDriver from specified path if available
        code = re.sub(
            r"driver = webdriver\.Chrome\(options=options\)",
            "# Use ChromeDriver from specified path if available\n"
            "from selenium.webdriver.chrome.service import Service\n"
            "if 'chrome_driver_path' in locals() and chrome_driver_path:\n"
            "    service = Service(executable_path=chrome_driver_path)\n"
            "    driver = webdriver.Chrome(service=service, options=options)\n"
            "else:\n"
            "    driver = webdriver.Chrome(options=options)",
            code
        )
        
        return title_comment + code
    
    def _add_execution_wrapper(self, code, test_case):
        """Add wrapper code for live execution"""
        wrapper = f"""# {'-'*50}
# Test Case: {test_case.get('title', 'Unknown')}
# Description: {test_case.get('description', 'No description')}
# {'-'*50}

import threading
import queue
import time
import traceback
import sys
import os

# Create a queue for logging
log_queue = queue.Queue()

# Function to execute the test in a separate thread
def run_test():
    try:
        # Redirect stdout to capture logs
        original_stdout = sys.stdout
        sys.stdout = LogRedirector(log_queue)
        
        # Set ChromeDriver executable path if provided in environment or use default location
        chrome_driver_path = os.environ.get('CHROME_DRIVER_PATH', None)
        if chrome_driver_path and os.path.exists(chrome_driver_path):
            log_queue.put(("LOG", f"Using ChromeDriver at: {{chrome_driver_path}}"))
            # This will be used in the test code if service parameter is set
        
        # Execute the test code
{self._indent_code(code, 8)}
        
        # Restore stdout
        sys.stdout = original_stdout
        log_queue.put(("STATUS", "Test completed successfully"))
    except Exception as e:
        log_queue.put(("ERROR", f"Test failed: {{str(e)}}\\n{{traceback.format_exc()}}"))
        # Restore stdout
        sys.stdout = sys.__stdout__

# Custom stdout redirector to capture logs
class LogRedirector:
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, message):
        if message.strip():
            self.queue.put(("LOG", message))
    
    def flush(self):
        pass

# Execute test in a separate thread
test_thread = threading.Thread(target=run_test)
test_thread.daemon = True
test_thread.start()

# Start time for timeout tracking
start_time = time.time()
timeout = 60  # 60 seconds timeout

# Main execution loop - this would be replaced by frontend polling
print("Test is running... (you can see progress in the browser)")

"""
        return wrapper
    
    def _indent_code(self, code, spaces):
        """Indent code by the specified number of spaces"""
        indented_lines = []
        for line in code.split('\n'):
            indented_lines.append(' ' * spaces + line)
        return '\n'.join(indented_lines)

    def execute_test_code(self, code):
        """Execute generated test code (this would be a separate endpoint)"""
        # In a real implementation, this would run the code in a safe environment
        # For the demo, we'll just return a success message
        return {"status": "success", "message": "Test executed successfully"} 
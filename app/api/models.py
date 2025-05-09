from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class WebsiteInfo(BaseModel):
    url: str
    reuse_analysis: Optional[bool] = True

class TestStep(BaseModel):
    id: int
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None

class TestCase(BaseModel):
    id: int
    name: str
    description: str
    steps: List[TestStep]
    url: str

class GeneratedCode(BaseModel):
    test_case_id: int
    code: str

class TestExecutionRequest(BaseModel):
    test_code: str
    test_case_data: Optional[Dict[str, Any]] = None
    use_executor: bool = True
    chrome_driver_path: Optional[str] = None

class TestExecutionResponse(BaseModel):
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None
    logs: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    completion_percentage: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None

class SimpleCodeRequest(BaseModel):
    test_id: int
    url: str
    node_url: Optional[str] = None

class SimpleTestRequest(BaseModel):
    test_code: str
    chrome_driver_path: Optional[str] = None
    
class SimpleTestResponse(BaseModel):
    status: str
    message: str
    output: List[str] = []
    error: List[str] = []
    temp_file: Optional[str] = None

class ExplorationDelete(BaseModel):
    exploration_id: str 
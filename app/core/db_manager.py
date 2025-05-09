import logging
import os
import json
import yaml
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict, List, Optional, Any

# Set up logger
logger = logging.getLogger("web-analysis-framework.db-manager")

# JSON Encoder to handle ObjectId and dates
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)

class DatabaseManager:
    def __init__(self):
        """Initialize MongoDB connection"""
        # Load configuration from config.yaml
        try:
            with open("config.yaml", "r") as file:
                config = yaml.safe_load(file)
                
            # Get MongoDB connection settings from config
            mongo_uri = config["mongodb"]["uri"]
            db_name = config["mongodb"]["database"]
            
            # Establish connection
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.explorations = self.db["explorations"]
            self.test_cases = self.db["test_cases"]
            self.generated_code = self.db["generated_code"]
            logger.info(f"Connected to MongoDB database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
            raise
    
    def save_exploration(self, url: str, data: Dict[str, Any]) -> str:
        """Save website exploration data to MongoDB
        
        Args:
            url: The URL of the explored website
            data: The exploration data (structure, pages, etc.)
            
        Returns:
            str: The ID of the saved exploration
        """
        try:
            # Add metadata
            exploration = {
                "url": url,
                "domain": data.get("domain", ""),
                "name": data.get("domain", url),
                "created_at": datetime.now(),
                "data": data,
                "summary": {
                    "page_count": len(data.get("pages", {})),
                    "has_test_cases": False,
                    "has_generated_code": False,
                    "test_case_count": 0
                }
            }
            
            # Insert into database
            result = self.explorations.insert_one(exploration)
            exploration_id = str(result.inserted_id)
            
            logger.info(f"Saved exploration for {url} with ID: {exploration_id}")
            return exploration_id
        except Exception as e:
            logger.error(f"Error saving exploration for {url}: {str(e)}", exc_info=True)
            raise
    
    def get_exploration(self, exploration_id: str) -> Optional[Dict[str, Any]]:
        """Get exploration by ID
        
        Args:
            exploration_id: The ID of the exploration to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The exploration data or None if not found
        """
        try:
            # Find exploration by ID
            exploration = self.explorations.find_one({"_id": ObjectId(exploration_id)})
            
            if exploration:
                # Convert ObjectId to string for serialization
                exploration["_id"] = str(exploration["_id"])
                logger.info(f"Retrieved exploration with ID: {exploration_id}")
                return exploration
            
            logger.warning(f"Exploration with ID {exploration_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving exploration {exploration_id}: {str(e)}", exc_info=True)
            raise
    
    def get_exploration_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get the most recent exploration for a URL
        
        Args:
            url: The URL to look for
            
        Returns:
            Optional[Dict[str, Any]]: The exploration data or None if not found
        """
        try:
            # Find exploration by URL, sorted by creation date (most recent first)
            exploration = self.explorations.find_one(
                {"url": url},
                sort=[("created_at", -1)]  # -1 means descending order
            )
            
            if exploration:
                # Convert ObjectId to string for serialization
                exploration["_id"] = str(exploration["_id"])
                logger.info(f"Retrieved most recent exploration for URL: {url}")
                return exploration
            
            logger.info(f"No exploration found for URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving exploration for URL {url}: {str(e)}", exc_info=True)
            raise
    
    def list_explorations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List saved explorations, most recent first
        
        Args:
            limit: Maximum number of explorations to return
            
        Returns:
            List[Dict[str, Any]]: List of explorations
        """
        try:
            # Get explorations, sorted by creation date
            cursor = self.explorations.find(
                {},
                projection={
                    "url": 1, 
                    "domain": 1, 
                    "name": 1, 
                    "created_at": 1,
                    "summary": 1
                },
                sort=[("created_at", -1)],
                limit=limit
            )
            
            # Convert ObjectId to string for serialization
            explorations = []
            for exploration in cursor:
                exploration["_id"] = str(exploration["_id"])
                explorations.append(exploration)
            
            logger.info(f"Retrieved {len(explorations)} explorations")
            return explorations
        except Exception as e:
            logger.error(f"Error listing explorations: {str(e)}", exc_info=True)
            raise
    
    def delete_exploration(self, exploration_id: str) -> bool:
        """Delete an exploration by ID
        
        Args:
            exploration_id: The ID of the exploration to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Delete exploration by ID
            result = self.explorations.delete_one({"_id": ObjectId(exploration_id)})
            
            # Also delete associated test cases and generated code
            self.test_cases.delete_many({"exploration_id": exploration_id})
            self.generated_code.delete_many({"exploration_id": exploration_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted exploration with ID: {exploration_id}")
                return True
            
            logger.warning(f"Exploration with ID {exploration_id} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Error deleting exploration {exploration_id}: {str(e)}", exc_info=True)
            raise

    def save_test_cases(self, exploration_id: str, test_cases: List[Dict[str, Any]]) -> List[str]:
        """Save test cases for an exploration
        
        Args:
            exploration_id: The ID of the exploration
            test_cases: List of test cases to save
            
        Returns:
            List[str]: List of test case IDs
        """
        try:
            # Verificar que la exploración existe
            exploration = self.explorations.find_one({"_id": ObjectId(exploration_id)})
            if not exploration:
                logger.warning(f"Exploration {exploration_id} not found when saving test cases")
                return []
                
            # Guardar cada test case como documento individual
            test_case_ids = []
            for test_case in test_cases:
                test_case_data = {
                    "exploration_id": exploration_id,
                    "created_at": datetime.now(),
                    "title": test_case.get("title", "Untitled Test Case"),
                    "description": test_case.get("description", ""),
                    "steps": test_case.get("steps", []),
                    "expected_results": test_case.get("expected_results", []),
                    "id": test_case.get("id"),  # ID numérico para referencia en el frontend
                    "status": "created",
                    "has_generated_code": False
                }
                
                result = self.test_cases.insert_one(test_case_data)
                test_case_ids.append(str(result.inserted_id))
            
            # Actualizar el resumen en la exploración
            self.explorations.update_one(
                {"_id": ObjectId(exploration_id)},
                {
                    "$set": {
                        "summary.has_test_cases": True,
                        "summary.test_case_count": len(test_cases)
                    }
                }
            )
            
            logger.info(f"Saved {len(test_cases)} test cases for exploration {exploration_id}")
            return test_case_ids
        except Exception as e:
            logger.error(f"Error saving test cases for exploration {exploration_id}: {str(e)}", exc_info=True)
            raise

    def save_generated_code(self, exploration_id: str, test_case_id: int, code: str) -> str:
        """Save generated code for a test case
        
        Args:
            exploration_id: The ID of the exploration
            test_case_id: The ID of the test case
            code: The generated code
            
        Returns:
            str: The ID of the saved code
        """
        try:
            # Verificar que la exploración existe
            exploration = self.explorations.find_one({"_id": ObjectId(exploration_id)})
            if not exploration:
                logger.warning(f"Exploration {exploration_id} not found when saving generated code")
                return ""
                
            # Buscar el test case por su ID numérico
            test_case = self.test_cases.find_one({
                "exploration_id": exploration_id,
                "id": test_case_id
            })
            
            test_case_mongo_id = None
            if test_case:
                test_case_mongo_id = str(test_case["_id"])
                
                # Actualizar el test case para indicar que tiene código generado
                self.test_cases.update_one(
                    {"_id": test_case["_id"]},
                    {"$set": {"has_generated_code": True}}
                )
            
            # Guardar el código generado como documento independiente
            code_data = {
                "exploration_id": exploration_id,
                "test_case_id": test_case_id,
                "test_case_mongo_id": test_case_mongo_id,
                "created_at": datetime.now(),
                "code": code,
                "language": "python",
                "status": "created"
            }
            
            result = self.generated_code.insert_one(code_data)
            code_id = str(result.inserted_id)
            
            # Actualizar el resumen en la exploración
            self.explorations.update_one(
                {"_id": ObjectId(exploration_id)},
                {"$set": {"summary.has_generated_code": True}}
            )
            
            logger.info(f"Saved generated code for test case {test_case_id} in exploration {exploration_id}")
            return code_id
        except Exception as e:
            logger.error(f"Error saving generated code for exploration {exploration_id}: {str(e)}", exc_info=True)
            raise

    def get_test_cases(self, exploration_id: str) -> List[Dict[str, Any]]:
        """Get test cases for an exploration
        
        Args:
            exploration_id: The ID of the exploration
            
        Returns:
            List[Dict[str, Any]]: List of test cases
        """
        try:
            # Buscar todos los test cases para esta exploración
            cursor = self.test_cases.find(
                {"exploration_id": exploration_id},
                sort=[("created_at", 1)]  # Ordenar por fecha de creación
            )
            
            # Convertir ObjectId a string para serialización
            test_cases = []
            for test_case in cursor:
                test_case["_id"] = str(test_case["_id"])
                test_cases.append(test_case)
                
            logger.info(f"Retrieved {len(test_cases)} test cases for exploration {exploration_id}")
            return test_cases
        except Exception as e:
            logger.error(f"Error retrieving test cases for exploration {exploration_id}: {str(e)}", exc_info=True)
            raise

    def get_generated_code(self, exploration_id: str, test_case_id: int) -> Optional[Dict[str, Any]]:
        """Get generated code for a test case
        
        Args:
            exploration_id: The ID of the exploration
            test_case_id: The ID of the test case
            
        Returns:
            Optional[Dict[str, Any]]: The generated code or None if not found
        """
        try:
            # Buscar el código más reciente para este test case
            code = self.generated_code.find_one(
                {
                    "exploration_id": exploration_id,
                    "test_case_id": test_case_id
                },
                sort=[("created_at", -1)]  # Más reciente primero
            )
            
            if code:
                code["_id"] = str(code["_id"])
                return code
                
            return None
        except Exception as e:
            logger.error(f"Error retrieving generated code for exploration {exploration_id}, test case {test_case_id}: {str(e)}", exc_info=True)
            raise
            
    def get_all_generated_code(self, exploration_id: str) -> List[Dict[str, Any]]:
        """Get all generated code for an exploration
        
        Args:
            exploration_id: The ID of the exploration
            
        Returns:
            List[Dict[str, Any]]: List of generated code
        """
        try:
            # Buscar todo el código generado para esta exploración
            cursor = self.generated_code.find(
                {"exploration_id": exploration_id},
                sort=[("test_case_id", 1), ("created_at", -1)]  # Ordenar por test case ID y luego por fecha
            )
            
            # Convertir ObjectId a string para serialización
            code_list = []
            for code in cursor:
                code["_id"] = str(code["_id"])
                code_list.append(code)
                
            logger.info(f"Retrieved {len(code_list)} generated code items for exploration {exploration_id}")
            return code_list
        except Exception as e:
            logger.error(f"Error retrieving all generated code for exploration {exploration_id}: {str(e)}", exc_info=True)
            raise
            
    def get_test_cases_with_code(self, exploration_id: str) -> List[Dict[str, Any]]:
        """Get test cases with their associated generated code
        
        Args:
            exploration_id: The ID of the exploration
            
        Returns:
            List[Dict[str, Any]]: List of test cases with code
        """
        try:
            # Obtener todos los test cases
            test_cases = self.get_test_cases(exploration_id)
            
            # Obtener todo el código generado
            all_code = self.get_all_generated_code(exploration_id)
            
            # Crear un diccionario para mapear test_case_id a código
            code_map = {}
            for code in all_code:
                test_id = code["test_case_id"]
                if test_id not in code_map:
                    code_map[test_id] = code
            
            # Asociar el código con cada test case
            for test_case in test_cases:
                test_id = test_case["id"]
                if test_id in code_map:
                    test_case["generated_code"] = code_map[test_id]
                else:
                    test_case["generated_code"] = None
            
            return test_cases
        except Exception as e:
            logger.error(f"Error retrieving test cases with code for exploration {exploration_id}: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
db_manager = DatabaseManager() 
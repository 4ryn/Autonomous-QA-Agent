import logging
import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from llm_client import OllamaClient
from vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumScriptGenerator:
    def __init__(self, llm_client: OllamaClient, vector_store: VectorStore):
        self.llm_client = llm_client
        self.vector_store = vector_store
    
    def extract_html_structure(self, html_content: str) -> Dict[str, Any]:
        """Extract HTML structure and selectors"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            structure = {
                "forms": [],
                "buttons": [],
                "inputs": [],
                "selects": [],
                "links": []
            }
            
            # Extract forms
            for form in soup.find_all('form'):
                structure["forms"].append({
                    "id": form.get('id', ''),
                    "name": form.get('name', ''),
                    "class": form.get('class', []),
                    "action": form.get('action', '')
                })
            
            # Extract buttons
            for button in soup.find_all(['button', 'input']):
                if button.name == 'input' and button.get('type') not in ['button', 'submit']:
                    continue
                structure["buttons"].append({
                    "id": button.get('id', ''),
                    "name": button.get('name', ''),
                    "class": button.get('class', []),
                    "text": button.get_text(strip=True) if button.name == 'button' else button.get('value', ''),
                    "type": button.get('type', '')
                })
            
            # Extract inputs
            for inp in soup.find_all('input'):
                structure["inputs"].append({
                    "id": inp.get('id', ''),
                    "name": inp.get('name', ''),
                    "class": inp.get('class', []),
                    "type": inp.get('type', 'text'),
                    "placeholder": inp.get('placeholder', '')
                })
            
            # Extract selects
            for select in soup.find_all('select'):
                options = [opt.get_text(strip=True) for opt in select.find_all('option')]
                structure["selects"].append({
                    "id": select.get('id', ''),
                    "name": select.get('name', ''),
                    "class": select.get('class', []),
                    "options": options
                })
            
            # Extract links
            for link in soup.find_all('a'):
                structure["links"].append({
                    "id": link.get('id', ''),
                    "class": link.get('class', []),
                    "text": link.get_text(strip=True),
                    "href": link.get('href', '')
                })
            
            return structure
        except Exception as e:
            logger.error(f"Error extracting HTML structure: {str(e)}")
            return {}
    
    def get_html_content(self) -> Optional[str]:
        """Retrieve HTML content from vector store"""
        try:
            # Search for HTML documents without filter (search by content instead)
            results = self.vector_store.search(
                query="HTML structure checkout form button input select",
                top_k=20  # Get more results to find HTML
            )
            
            if not results:
                logger.warning("No documents found in vector store")
                return None
            
            # Find the chunk containing full HTML
            for result in results:
                content = result['content']
                metadata = result.get('metadata', {})
                
                # Check if this is HTML content
                if metadata.get('file_type') == 'html' or 'HTML Structure' in content or '<!DOCTYPE' in content or '<html' in content:
                    # If it contains the HTML structure marker
                    if '--- HTML Structure ---' in content:
                        parts = content.split('--- HTML Structure ---')
                        if len(parts) > 1:
                            html_content = parts[1].strip()
                            logger.info(f"Found HTML content in chunk (length: {len(html_content)})")
                            return html_content
                    # If it's raw HTML
                    elif '<!DOCTYPE' in content or '<html' in content:
                        logger.info(f"Found raw HTML content (length: {len(content)})")
                        return content
            
            # If no HTML structure found, try to reconstruct from all chunks
            logger.info("Attempting to reconstruct HTML from multiple chunks")
            html_chunks = []
            for result in results:
                content = result['content']
                metadata = result.get('metadata', {})
                if metadata.get('source', '').endswith('.html'):
                    html_chunks.append(content)
            
            if html_chunks:
                reconstructed = '\n'.join(html_chunks)
                logger.info(f"Reconstructed HTML from {len(html_chunks)} chunks")
                return reconstructed
            
            logger.warning("No HTML content found in any results")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving HTML content: {str(e)}")
            return None
    
    def generate_selenium_script(self, test_case: Dict[str, Any]) -> Optional[str]:
        """Generate Selenium script for a test case"""
        try:
            logger.info(f"Generating Selenium script for: {test_case.get('test_name', 'Unknown')}")
            
            # Get HTML content
            html_content = self.get_html_content()
            if not html_content:
                logger.error("No HTML content available")
                return None
            
            # Extract HTML structure
            html_structure = self.extract_html_structure(html_content)
            
            # Create prompt
            system_prompt = """You are an expert Selenium test automation engineer. Generate a complete, executable Python Selenium script based on the test case and HTML structure provided.

REQUIREMENTS:
1. Use ONLY the selectors and elements present in the provided HTML structure
2. Include proper error handling with try-except blocks
3. Add explicit waits using WebDriverWait
4. Include logging statements
5. Use the ChromeDriver with webdriver_manager
6. Generate complete, runnable code
7. Do NOT use placeholder selectors - use actual IDs, names, or XPath from the HTML
8. Return ONLY Python code without markdown formatting"""
            
            prompt = f"""Generate a complete Selenium test script for the following test case:

TEST CASE:
Test ID: {test_case.get('test_id', 'N/A')}
Test Name: {test_case.get('test_name', 'N/A')}
Description: {test_case.get('description', 'N/A')}

Steps:
{chr(10).join([f"{i}. {step}" for i, step in enumerate(test_case.get('steps', []), 1)])}

Expected Result: {test_case.get('expected_result', 'N/A')}

HTML STRUCTURE:
Forms: {json.dumps(html_structure.get('forms', []), indent=2)}
Buttons: {json.dumps(html_structure.get('buttons', []), indent=2)}
Inputs: {json.dumps(html_structure.get('inputs', []), indent=2)}
Selects: {json.dumps(html_structure.get('selects', []), indent=2)}

Generate a complete Python Selenium script with:
1. Proper imports (selenium, webdriver_manager, logging)
2. WebDriver setup using webdriver_manager
3. Test execution with error handling
4. Explicit waits
5. Assertions for validation
6. Proper cleanup
7. Use actual element selectors from the HTML structure above

Generate the script:"""
            
            # Generate script
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2500
            )
            
            if not response:
                logger.error("Failed to generate Selenium script")
                return None
            
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                lines = cleaned_response.split('\n')
                # Remove first and last lines if they contain ```
                if lines[0].strip().startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith('```'):
                    lines = lines[:-1]
                cleaned_response = '\n'.join(lines)
            
            logger.info("Selenium script generated successfully")
            return cleaned_response
        except Exception as e:
            logger.error(f"Error generating Selenium script: {str(e)}")
            return None
    
    def validate_script(self, script: str) -> Dict[str, Any]:
        """Basic validation of generated script"""
        try:
            required_imports = ['selenium', 'webdriver', 'WebDriverWait']
            required_methods = ['find_element', 'click', 'send_keys']
            
            validation_results = {
                "valid": True,
                "warnings": [],
                "errors": []
            }
            
            # Check for required imports
            for imp in required_imports:
                if imp not in script:
                    validation_results["warnings"].append(f"Missing import: {imp}")
            
            # Check for basic Selenium methods
            has_methods = any(method in script for method in required_methods)
            if not has_methods:
                validation_results["errors"].append("No Selenium methods found")
                validation_results["valid"] = False
            
            # Check for try-except
            if 'try:' not in script or 'except' not in script:
                validation_results["warnings"].append("Missing error handling")
            
            return validation_results
        except Exception as e:
            logger.error(f"Error validating script: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)]
            }
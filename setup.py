"""
Setup and verification script for Autonomous QA Agent
Run this script to verify all dependencies and services are properly configured
"""

import sys
import subprocess
import requests
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    
    print("SUCCESS: Python version is compatible")
    return True

def check_pip_packages():
    """Check if required packages are installed"""
    print_header("Checking Required Packages")
    
    required_packages = [
        'streamlit',
        'fastapi',
        'langchain',
        'sentence-transformers',
        'qdrant-client',
        'ollama',
        'pymupdf',
        'selenium',
        'python-dotenv',
        'beautifulsoup4'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nERROR: Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\nSUCCESS: All required packages are installed")
    return True

def check_ollama():
    """Check if Ollama is running and model is available"""
    print_header("Checking Ollama Service")
    
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print(f"✓ Ollama service is running at {ollama_url}")
            
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            if models:
                print(f"✓ Available models: {', '.join(models)}")
                
                if any(ollama_model in model for model in models):
                    print(f"✓ Model '{ollama_model}' is available")
                    return True
                else:
                    print(f"✗ Model '{ollama_model}' not found")
                    print(f"Run: ollama pull {ollama_model}")
                    return False
            else:
                print(f"✗ No models installed")
                print(f"Run: ollama pull {ollama_model}")
                return False
        else:
            print(f"✗ Ollama service returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to Ollama at {ollama_url}")
        print("\nPlease ensure Ollama is installed and running:")
        print("  1. Download from https://ollama.ai/download")
        print("  2. Install and start the service")
        print(f"  3. Run: ollama pull {ollama_model}")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama: {str(e)}")
        return False

def check_qdrant():
    """Check if Qdrant is running"""
    print_header("Checking Qdrant Service")
    
    qdrant_url = os.getenv("QDRANT_URL", "")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
    qdrant_use_cloud = os.getenv("QDRANT_USE_CLOUD", "True").lower() == "true"
    
    if qdrant_use_cloud or qdrant_url:
        # Cloud mode
        if not qdrant_url or not qdrant_api_key:
            print("✗ Qdrant Cloud credentials missing")
            print("\nPlease set in .env file:")
            print("  QDRANT_URL=https://your-cluster.cloud.qdrant.io")
            print("  QDRANT_API_KEY=your_api_key")
            print("\nSign up at: https://cloud.qdrant.io/")
            return False
        
        try:
            headers = {"api-key": qdrant_api_key}
            response = requests.get(f"{qdrant_url}/collections", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ Qdrant Cloud connected: {qdrant_url}")
                return True
            elif response.status_code == 401:
                print(f"✗ Qdrant Cloud authentication failed")
                print("Check your QDRANT_API_KEY in .env file")
                return False
            else:
                print(f"✗ Qdrant Cloud returned status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to Qdrant Cloud at {qdrant_url}")
            print("Check your QDRANT_URL in .env file")
            return False
        except Exception as e:
            print(f"✗ Error checking Qdrant Cloud: {str(e)}")
            return False
    else:
        # Local mode
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = os.getenv("QDRANT_PORT", "6333")
        
        try:
            response = requests.get(f"http://{qdrant_host}:{qdrant_port}/", timeout=5)
            
            if response.status_code == 200:
                print(f"✓ Qdrant service is running at {qdrant_host}:{qdrant_port}")
                return True
            else:
                print(f"✗ Qdrant service returned status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to Qdrant at {qdrant_host}:{qdrant_port}")
            print("\nPlease start Qdrant:")
            print("  Docker: docker run -p 6333:6333 qdrant/qdrant")
            print("  Or use Qdrant Cloud (set QDRANT_USE_CLOUD=True in .env)")
            return False
        except Exception as e:
            print(f"✗ Error checking Qdrant: {str(e)}")
            return False

def check_env_file():
    """Check if .env file exists"""
    print_header("Checking Environment Configuration")
    
    if Path(".env").exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file not found")
        print("\nPlease create a .env file with the following content:")
        print("""
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=qa_agent_docs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
        """)
        return False

def check_sample_files():
    """Check if sample files exist"""
    print_header("Checking Sample Files")
    
    sample_files = [
        'checkout.html',
        'product_specs.md',
        'ui_ux_guide.txt',
        'test_data.json'
    ]
    
    all_exist = True
    for file in sample_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            all_exist = False
    
    if not all_exist:
        print("\nWARNING: Some sample files are missing")
        print("You can still use the system with your own files")
    else:
        print("\nSUCCESS: All sample files are present")
    
    return True

def check_project_structure():
    """Check if all required Python files exist"""
    print_header("Checking Project Structure")
    
    required_files = [
        'config.py',
        'document_processor.py',
        'vector_store.py',
        'llm_client.py',
        'test_case_generator.py',
        'selenium_generator.py',
        'app.py'
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            all_exist = False
    
    if not all_exist:
        print("\nERROR: Some required files are missing")
        return False
    
    print("\nSUCCESS: All required files are present")
    return True

def main():
    """Main setup verification"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         Autonomous QA Agent - Setup Verification         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    results = {
        'Python Version': check_python_version(),
        'Project Structure': check_project_structure(),
        'Environment File': check_env_file(),
        'Python Packages': check_pip_packages(),
        'Ollama Service': check_ollama(),
        'Qdrant Service': check_qdrant(),
        'Sample Files': check_sample_files()
    }
    
    # Summary
    print_header("Setup Verification Summary")
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: All checks passed!")
        print("\nYou can now run the application:")
        print("  streamlit run app.py")
    else:
        print("WARNING: Some checks failed")
        print("\nPlease fix the issues above before running the application")
        print("Refer to README.md for detailed setup instructions")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
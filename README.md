# Autonomous QA Agent

An intelligent system that generates test cases and Selenium automation scripts by learning from project documentation using RAG (Retrieval-Augmented Generation).

## Overview

This system creates a "testing brain" that understands your application through documentation and generates grounded, non-hallucinated test scenarios. It uses:
- Grok LLM for text generation
- Qdrant vector database for document storage
- Sentence Transformers for embeddings
- Streamlit for user interface

## Features

- Upload and parse multiple document formats (MD, TXT, JSON, PDF, HTML)
- Build vector database from documentation
- Generate comprehensive test cases using RAG
- Create executable Selenium scripts with accurate selectors
- All test cases grounded in source documents (no hallucinations)

## Architecture

```
User Documents -> Document Processor -> Vector Store (Qdrant)
                                              |
                                              v
User Query -> RAG Pipeline -> LLM (Grok) -> Test Cases
                                              |
                                              v
Selected Test Case -> Script Generator -> Selenium Script
```

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

### Required Software

1. **Grok**
   - Sign up: https://www.grok.com
   - Get your API key

2. **Qdrant Cloud** (Vector Database)
   - Sign up: https://cloud.qdrant.io/
   - Create a free cluster
   - Get your cluster URL and API key
   - See detailed setup: [QDRANT_CLOUD_SETUP.md](QDRANT_CLOUD_SETUP.md)

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd autonomous-qa-agent
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

1. Copy the `.env` file to your project root
2. Update with your Qdrant Cloud credentials:

```env
# Update these with your Qdrant Cloud details
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_api_key_here
QDRANT_USE_CLOUD=True

# These work as-is for GROQ
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

**Getting Qdrant Cloud credentials:**
- See detailed guide: [QDRANT_CLOUD_SETUP.md](QDRANT_CLOUD_SETUP.md)
- Quick steps:
  1. Sign up at https://cloud.qdrant.io/
  2. Create a cluster
  3. Copy the cluster URL
  4. Generate and copy API key
  5. Update .env file


## Project Structure

```
autonomous-qa-agent/
├── .env                        # Environment configuration
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration management
├── document_processor.py       # Document parsing and chunking
├── vector_store.py            # Qdrant vector database operations
├── llm_client.py              # Grok LLM client
├── test_case_generator.py     # RAG-based test case generation
├── selenium_generator.py      # Selenium script generation
├── app.py                     # Streamlit UI application
├── checkout.html              # Sample e-shop checkout page
├── product_specs.md           # Sample product specifications
├── ui_ux_guide.txt            # Sample UI/UX guidelines
├── test_data.json             # Sample test data
└── README.md                  # This file
```

## Usage

### Step 1: Start the Application

```bash
streamlit run app.py
```

The application will open in your browser at http://ost:8501

### Step 2: Build Knowledge Base

1. Navigate to Tab 1: "Build Knowledge Base"
2. Upload support documents (product_specs.md, ui_ux_guide.txt, test_data.json)
3. Upload the HTML file (checkout.html)
4. Click "Build Knowledge Base"
5. Wait for processing to complete (shows progress)

### Step 3: Generate Test Cases

1. Navigate to Tab 2: "Generate Test Cases"
2. Enter a query (e.g., "Test discount code feature")
3. Adjust the number of documents to retrieve (default: 5)
4. Click "Generate Test Cases"
5. Review generated test cases with document references
6. Select a test case for script generation

### Step 4: Generate Selenium Scripts

1. Navigate to Tab 3: "Generate Selenium Scripts"
2. Verify your selected test case is displayed
3. Click "Generate Selenium Script"
4. Review the generated Python Selenium script
5. Download the script using the "Download Script" button

### Step 5: Run Generated Scripts

```bash
# Save the downloaded script as test_script.py
python test_script.py
```

## Sample Queries

Try these queries to test the system:

1. "Generate test cases for adding products to cart"
2. "Test discount code validation"
3. "Create tests for customer form validation"
4. "Test shipping option selection"
5. "Generate tests for complete checkout flow"

## API Keys Required

**Only 2 API Key Needed: Qdrant Cloud and Grok**

- **Qdrant Cloud API Key**: Required for vector storage
  - Get it from: https://cloud.qdrant.io/
  - Free tier available (1GB storage)
  - See setup guide: [QDRANT_CLOUD_SETUP.md](QDRANT_CLOUD_SETUP.md)

- **Grok**: API key 
- **Sentence Transformers**: No API key (downloads models y)

### Optional: Using Qdrant Instead

If you prefer to run Qdrant y instead of using the cloud:

1. Install Docker: https://www.docker.com/
2. Run: `docker run -p 6333:6333 qdrant/qdrant`
3. Update .env:
   ```env
   QDRANT_USE_CLOUD=False
   QDRANT_HOST=ost
   QDRANT_PORT=6333
   ```


### Qdrant Connection Error

```
Error: Failed to connect to Qdrant
```

**For Qdrant Cloud:**
1. Verify your cluster URL is correct (no trailing slash)
2. Check your API key is valid
3. Test connection: `curl -H "api-key: YOUR_KEY" YOUR_URL/collections`
4. Ensure cluster is running in Qdrant Cloud dashboard
5. Check internet connection

**For Qdrant:**
1. Set `QDRANT_USE_CLOUD=False` in .env
2. Ensure Docker is running
3. Run: `docker run -p 6333:6333 qdrant/qdrant`
4. Check port 6333 is not in use: `netstat -an | grep 6333`


## Performance Optimization

### For Faster Embeddings
```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Fast, 384 dim
```

### For Better Quality
```env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Better, 768 dim
```

## Advanced Configuration

### Custom Chunking Strategy

Edit `config.py`:
```python
CHUNK_SIZE=500  # Smaller chunks = more precise retrieval
CHUNK_OVERLAP=50  # Higher overlap = better context
```

### Adjust RAG Parameters

In `test_case_generator.py`:
```python
# More documents = more context but slower
retrieve_top_k = 10

# Lower temperature = more deterministic
temperature = 0.2
```

## Testing the System

### Quick Test

```bash

# 1. Verify Qdrant Cloud connection
python setup.py

# 2. Run app
streamlit run app.py

# 3. Upload sample files and follow the UI
```

### Verify Components

```python
# Test document processor
from document_processor import DocumentProcessor
processor = DocumentProcessor()
text = processor.extract_text_from_file("test.md", "md")

# Test vector store
from vector_store import VectorStore
store = VectorStore()
info = store.get_collection_info()

# Test LLM client
from llm_client import GrokClient
client = GrokClient()
response = client.generate("Hello, world!")
```

## Common Issues and Solutions

### Issue: Script generation uses wrong selectors

**Cause:** HTML structure not properly indexed

**Solution:**
1. Ensure checkout.html is uploaded
2. Rebuild knowledge base
3. Check HTML document appears in source documents list

### Issue: Test cases include non-existent features

**Cause:** LLM hallucinating beyond documentation

**Solution:**
1. Increase retrieve_top_k value
2. Lower LLM temperature (0.2-0.3)
3. Add more specific documentation
4. Verify all features are documented

### Issue: Cannot parse generated test cases

**Cause:** LLM returning malformed JSON

**Solution:**
1. Check Grok model is properly loaded
2. Increase max_tokens in generator
3. Use a more capable model (llama2:13b)
4. Review raw response in expander

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the Troubleshooting section
2. Review Grok documentation: https://Grok.ai/
3. Review Qdrant documentation: https://qdrant.tech/
4. Open an issue in the repository

## Acknowledgments

- Grok for LLM capabilities
- Qdrant for vector database
- Sentence Transformers for embeddings
- Streamlit for UI framework
- Selenium for browser automation

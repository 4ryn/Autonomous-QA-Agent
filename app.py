import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from config import settings
from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_client import LLMClient
from test_case_generator import TestCaseGenerator
from selenium_generator import SeleniumScriptGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    :root {
        --primary-color: #ad10e6e0;         /* Purple accent */
        --background-dark: #0D0F13;
        --background-light: #1A1D24;
        --card-bg: #1C1F26;
        --border-color: #2B2F36;
        --text-color: #F5F5F5;
        --muted-text: #9CA3AF;
        --success-color: #22C55E;
        --error-color: #F87171;
    }

    html, body, [class*="css"] {
        background-color: var(--background-dark);
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        color: #FFFFFF; /* White header text */
        letter-spacing: 1px;
        text-shadow: 0 0 12px rgba(173, 16, 230, 0.35);
        margin: 2rem 0 0.5rem 0;
    }

    .sub-header {
        text-align: center;
        color: var(--muted-text);
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #13161C 0%, #0D0F13 100%);
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] h3 {
        color: var(--text-color);
        font-weight: 700;
    }

    .status-card {
        background: #1A1D24;
        border-left: 4px solid var(--primary-color);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        color: var(--text-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }

    .status-card-error {
        background: #2A1B1B;
        border-left: 4px solid var(--error-color);
    }

    .config-box {
        padding: 1rem;
        background-color: #15181E;
        border-left: 3px solid var(--primary-color);
        border-radius: 0.4rem;
        margin-bottom: 0.5rem;
        color: var(--muted-text);
    }

    /* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    border-bottom: 1px solid var(--border-color);
}

/* Normal tab */
.stTabs [data-baseweb="tab"] {
    color: var(--muted-text) !important;
    font-weight: 600;
    border-bottom: 3px solid transparent !important;
    transition: all 0.2s ease-in-out;
}

/* Selected tab (active) */
.stTabs [aria-selected="true"] {
    color: var(--primary-color) !important;
    border-bottom: 3px solid var(--primary-color) !important;
    background: none !important;
    box-shadow: none !important;
}

/* Hover state */
.stTabs [data-baseweb="tab"]:hover {
    color: var(--primary-color) !important;
    border-bottom: 3px solid var(--primary-color) !important;
    background: none !important;
    box-shadow: none !important;
}


    /* Info and success boxes */
    .info-box {
        padding: 1rem 1.25rem;
        background: rgba(173, 16, 230, 0.08);
        border-left: 4px solid var(--primary-color);
        border-radius: 0.5rem;
        margin: 1.25rem 0;
        color: var(--text-color);
    }

    .success-box {
        background: linear-gradient(90deg, #ad10e6e0, #d07ef7);
        color: #fff;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: 700;
        text-align: center;
        margin-top: 1rem;
        box-shadow: 0 4px 8px rgba(173,16,230,0.4);
    }

    /* Buttons */
    .stButton > button {
        background-color: #1A1D24 !important;
        color: #FFFFFF !important;
        font-weight: 600;
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        transition: all 0.3s ease-in-out;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-color), #d07ef7) !important;
        color: #FFFFFF !important;
        border: none;
        box-shadow: 0 4px 10px rgba(173,16,230,0.5);
    }

    /* Inputs */
    .stTextArea textarea, .stTextInput input {
        background-color: #13161C;
        color: var(--text-color);
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 1px var(--primary-color);
    }

    /* File uploaders */
    .uploadedFile, [data-testid="stFileUploaderDropzone"] {
        background-color: var(--background-light);
        border: 1px dashed var(--border-color);
        color: var(--muted-text);
    }

    /* Metrics */
    .metric-container {
        background: #13161C;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid #1F232A;
    }

    .metric-value {
        font-size: 2.3rem;
        font-weight: 800;
        color: var(--primary-color);
    }

    .metric-label {
        color: var(--muted-text);
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--text-color);
    }

    /* Footer — minimalist */
    .footer-content {
        background: none;
        border-top: 1px solid #1C1F26;
        text-align: center;
        color: var(--muted-text);
        padding: 1rem 0;
        font-size: 0.85rem;
        margin-top: 3rem;
    }

    .footer-title {
        color: var(--primary-color);
        font-weight: 700;
        font-size: 0.95rem;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)






# Initialize session state
if 'knowledge_base_built' not in st.session_state:
    st.session_state.knowledge_base_built = False
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = None
if 'selected_test_case' not in st.session_state:
    st.session_state.selected_test_case = None
if 'generated_script' not in st.session_state:
    st.session_state.generated_script = None

# Initialize components
@st.cache_resource
def initialize_components():
    try:
        doc_processor = DocumentProcessor()
        vector_store = VectorStore()
        llm_client = LLMClient()
        test_generator = TestCaseGenerator(vector_store, llm_client)
        script_generator = SeleniumScriptGenerator(llm_client, vector_store)
        
        return doc_processor, vector_store, llm_client, test_generator, script_generator
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        st.stop()

doc_processor, vector_store, llm_client, test_generator, script_generator = initialize_components()

# Header
st.markdown('<h1 class="main-header">Autonomous QA Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Test Case and Selenium Script Generation</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### System Status")
    
    # Check LLM status
    if llm_client.is_available():
        llm_type = "Groq API" if llm_client.use_groq else "Ollama"
        st.markdown(f"""
        <div class="status-card">
            <strong>{llm_type}</strong><br>
            <small>Connected and Ready</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-card status-card-error">
            <strong>LLM Not Connected</strong><br>
            <small>Check configuration</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Check vector store status
    try:
        info = vector_store.get_collection_info()
        if info and info.get('points_count', 0) > 0:
            st.markdown(f"""
            <div class="status-card">
                <strong>Qdrant Cloud</strong><br>
                <small>{info.get('points_count', 0)} documents indexed</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card">
                <strong>Qdrant Cloud</strong><br>
                <small>Connected - No data yet</small>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
        <div class="status-card status-card-error">
            <strong>Qdrant Cloud</strong><br>
            <small>Connection issue</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### Configuration")
    llm_model = settings.GROQ_MODEL if settings.USE_GROQ else settings.OLLAMA_MODEL
    
    st.markdown(f"""
    <div class="config-box">
        <strong>LLM Model:</strong><br>
        {llm_model}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="config-box">
        <strong>Embeddings:</strong><br>
        all-MiniLM-L6-v2
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="config-box">
        <strong>Storage:</strong><br>
        Qdrant Cloud
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("Clear Knowledge Base", use_container_width=True):
        try:
            vector_store.clear_collection()
            st.session_state.knowledge_base_built = False
            st.session_state.test_cases = None
            st.session_state.selected_test_case = None
            st.session_state.generated_script = None
            st.success("Knowledge base cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Resources")
    st.markdown("- Documentation")
    st.markdown("- Quick Start Guide")
    st.markdown("- GitHub Repository")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Knowledge Base", "Test Cases", "Selenium Scripts"])

# Tab 1: Document Upload and Knowledge Base Building
with tab1:
    st.markdown('<div class="section-header">Build Knowledge Base</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>How it works:</strong> Upload your project documentation and HTML files. 
        The system will process, chunk, and embed them into a searchable knowledge base.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Support Documents")
        st.caption("Upload specification files (MD, TXT, JSON, PDF)")
        
        support_files = st.file_uploader(
            "Drop files here",
            type=['md', 'txt', 'json', 'pdf'],
            accept_multiple_files=True,
            key="support_files",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("#### HTML File")
        st.caption("Upload the application HTML for selector extraction")
        
        html_file = st.file_uploader(
            "Drop HTML here",
            type=['html'],
            accept_multiple_files=False,
            key="html_file",
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    if st.button("Build Knowledge Base", type="primary", use_container_width=True, disabled=not (support_files or html_file)):
        if not support_files and not html_file:
            st.error("Please upload at least one file")
        else:
            with st.spinner("Processing documents..."):
                try:
                    all_documents = []
                    file_list = []
                    
                    # Create temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Process support files
                        if support_files:
                            progress_bar = st.progress(0)
                            for idx, file in enumerate(support_files):
                                file_path = os.path.join(temp_dir, file.name)
                                with open(file_path, 'wb') as f:
                                    f.write(file.getbuffer())
                                
                                file_ext = file.name.split('.')[-1].lower()
                                file_list.append({
                                    'path': file_path,
                                    'name': file.name,
                                    'type': file_ext
                                })
                                progress_bar.progress((idx + 1) / len(support_files))
                            progress_bar.empty()
                        
                        # Process HTML file
                        if html_file:
                            file_path = os.path.join(temp_dir, html_file.name)
                            with open(file_path, 'wb') as f:
                                f.write(html_file.getbuffer())
                            
                            file_list.append({
                                'path': file_path,
                                'name': html_file.name,
                                'type': 'html'
                            })
                        
                        # Process documents
                        st.info("Extracting text from documents...")
                        all_documents = doc_processor.process_multiple_documents(file_list)
                    
                    if not all_documents:
                        st.error("Failed to process documents")
                    else:
                        st.success(f"Processed {len(all_documents)} document chunks")
                        
                        # Create collection
                        st.info("Creating vector database collection...")
                        if not vector_store.create_collection(force_recreate=True):
                            st.error("Failed to create collection")
                        else:
                            # Add documents to vector store
                            st.info("Generating embeddings and storing...")
                            if vector_store.add_documents(all_documents):
                                st.session_state.knowledge_base_built = True
                                st.session_state.uploaded_files = [f.name for f in (support_files or [])] + ([html_file.name] if html_file else [])
                                
                                st.markdown("""
                                <div class="success-box">
                                    Knowledge Base Built Successfully
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show metrics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown(f"""
                                    <div class="metric-container">
                                        <div class="metric-value">{len(file_list)}</div>
                                        <div class="metric-label">Files Uploaded</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div class="metric-container">
                                        <div class="metric-value">{len(all_documents)}</div>
                                        <div class="metric-label">Document Chunks</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col3:
                                    info = vector_store.get_collection_info()
                                    st.markdown(f"""
                                    <div class="metric-container">
                                        <div class="metric-value">{info.get('points_count', 0)}</div>
                                        <div class="metric-label">Vectors Stored</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.error("Failed to add documents to vector store")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Error: {str(e)}", exc_info=True)
    
    if st.session_state.knowledge_base_built:
        st.markdown("""
        <div class="success-box">
            Knowledge Base Ready
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Uploaded Files"):
            for file_name in st.session_state.uploaded_files:
                st.markdown(f"- {file_name}")

# Tab 2: Test Case Generation
with tab2:
    st.markdown('<div class="section-header">Generate Test Cases</div>', unsafe_allow_html=True)
    
    if not st.session_state.knowledge_base_built:
        st.markdown("""
        <div class="info-box">
            <strong>Knowledge base not built yet.</strong><br>
            Please upload documents in the Knowledge Base tab first.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
            <strong>Tip:</strong> Be specific in your query. Example: Generate test cases for discount code validation with valid and invalid inputs
        </div>
        """, unsafe_allow_html=True)
        
        query = st.text_area(
            "What would you like to test?",
            placeholder="Example: Generate comprehensive test cases for the checkout discount code feature",
            height=100,
            help="Describe what functionality you want to test"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            retrieve_k = st.slider("Documents to retrieve", 3, 10, 5, help="More documents = more context")
        
        if st.button("Generate Test Cases", type="primary", use_container_width=True, disabled=not query):
            with st.spinner("AI is analyzing documentation and generating test cases..."):
                try:
                    result = test_generator.generate_test_cases(query, retrieve_top_k=retrieve_k)
                    
                    if result.get('success'):
                        st.session_state.test_cases = result
                        
                        st.markdown(f"""
                        <div class="success-box">
                            Generated {len(result.get('test_cases', []))} Test Cases
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                        if 'raw_response' in result:
                            with st.expander("View Raw Response"):
                                st.code(result['raw_response'])
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Error: {str(e)}", exc_info=True)
        
        # Display test cases
        if st.session_state.test_cases and st.session_state.test_cases.get('success'):
            st.markdown("---")
            st.markdown("### Generated Test Cases")
            
            # Show source documents
            with st.expander("Source Documents Used"):
                for doc in st.session_state.test_cases.get('source_documents', []):
                    st.markdown(f"- {doc}")
            
            # Display each test case
            test_cases = st.session_state.test_cases.get('test_cases', [])
            for i, tc in enumerate(test_cases):
                with st.expander(f"{tc.get('test_id', f'TC{i+1}')} - {tc.get('test_name', 'Unnamed Test')}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Type:** `{tc.get('test_type', 'N/A')}`")
                        st.markdown(f"**Description:** {tc.get('description', 'N/A')}")
                        
                        st.markdown("**Preconditions:**")
                        for precond in tc.get('preconditions', []):
                            st.markdown(f"- {precond}")
                        
                        st.markdown("**Steps:**")
                        for j, step in enumerate(tc.get('steps', []), 1):
                            st.markdown(f"{j}. {step}")
                        
                        st.markdown(f"**Expected Result:** {tc.get('expected_result', 'N/A')}")
                        
                        st.markdown("**References:**")
                        for ref in tc.get('document_references', []):
                            st.markdown(f"- `{ref}`")
                    
                    with col2:
                        if st.button(f"Select", key=f"select_{i}", use_container_width=True):
                            st.session_state.selected_test_case = tc
                            st.success("Selected!")
                            st.rerun()

# Tab 3: Selenium Script Generation
with tab3:
    st.markdown('<div class="section-header">Generate Selenium Script</div>', unsafe_allow_html=True)
    
    if not st.session_state.knowledge_base_built:
        st.markdown("""
        <div class="info-box">
            <strong>Knowledge base not built yet.</strong><br>
            Please upload documents in the Knowledge Base tab first.
        </div>
        """, unsafe_allow_html=True)
    elif not st.session_state.test_cases:
        st.markdown("""
        <div class="info-box">
            <strong>No test cases generated yet.</strong><br>
            Please generate test cases in the Test Cases tab first.
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.session_state.selected_test_case:
            tc = st.session_state.selected_test_case
            
            st.markdown(f"""
            <div class="info-box">
                <strong>Selected Test Case:</strong> {tc.get('test_name', 'Unknown')}<br>
                <strong>ID:</strong> {tc.get('test_id', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Test Case Details"):
                st.json(tc)
            
            if st.button("Generate Selenium Script", type="primary", use_container_width=True):
                with st.spinner("AI is generating executable Python script..."):
                    try:
                        script = script_generator.generate_selenium_script(tc)
                        
                        if script:
                            st.session_state.generated_script = script
                            
                            st.markdown("""
                            <div class="success-box">
                                Selenium Script Generated Successfully
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("Failed to generate script")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        logger.error(f"Error: {str(e)}", exc_info=True)
        else:
            st.markdown("""
            <div class="info-box">
                <strong>No test case selected.</strong><br>
                Please select a test case from the Test Cases tab.
            </div>
            """, unsafe_allow_html=True)
        
        # Display generated script
        if st.session_state.generated_script:
            st.markdown("---")
            st.markdown("### Generated Python Script")
            
            # Validate script
            validation = script_generator.validate_script(st.session_state.generated_script)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if validation.get('valid'):
                    st.success("Script validation passed")
                else:
                    st.error("Script validation has warnings")
            
            with col2:
                st.download_button(
                    label="Download Script",
                    data=st.session_state.generated_script,
                    file_name=f"test_{st.session_state.selected_test_case.get('test_id', 'script')}.py",
                    mime="text/plain",
                    use_container_width=True
                )
            
            if validation.get('warnings'):
                with st.expander("Validation Warnings"):
                    for warning in validation['warnings']:
                        st.warning(warning)
            
            # Display script
            st.code(st.session_state.generated_script, language='python', line_numbers=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer-content">
    <p>Powered by Groq API, Qdrant Cloud and Sentence Transformers</p>
    <p class="footer-subtitle">Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
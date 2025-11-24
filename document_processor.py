import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import fitz
import markdown
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> Optional[str]:
        """Extract text from various file formats"""
        try:
            if file_type == "txt":
                return self._extract_txt(file_path)
            elif file_type == "md":
                return self._extract_markdown(file_path)
            elif file_type == "json":
                return self._extract_json(file_path)
            elif file_type == "pdf":
                return self._extract_pdf(file_path)
            elif file_type == "html":
                return self._extract_html(file_path)
            else:
                logger.error(f"Unsupported file type: {file_type}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading TXT file: {str(e)}")
            raise
    
    def _extract_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            # Convert markdown to plain text
            html = markdown.markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            logger.error(f"Error reading Markdown file: {str(e)}")
            raise
    
    def _extract_json(self, file_path: str) -> str:
        """Extract text from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error reading JSON file: {str(e)}")
            raise
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num, page in enumerate(doc):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error reading PDF file: {str(e)}")
            raise
    
    def _extract_html(self, file_path: str) -> str:
        """Extract text and structure from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text while preserving some structure
            text_parts = []
            
            # Extract title
            title = soup.find('title')
            if title:
                text_parts.append(f"Title: {title.get_text(strip=True)}")
            
            # Extract all text content
            text_parts.append("\nContent:")
            text_parts.append(soup.get_text(separator='\n', strip=True))
            
            # Store original HTML for selector generation
            text_parts.append("\n--- HTML Structure ---")
            text_parts.append(html_content)
            
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Error reading HTML file: {str(e)}")
            raise
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        try:
            chunks = self.text_splitter.split_text(text)
            
            chunked_documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                }
                chunked_documents.append(doc)
            
            logger.info(f"Created {len(chunked_documents)} chunks from document")
            return chunked_documents
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []
    
    def process_document(self, file_path: str, file_name: str, file_type: str) -> List[Dict[str, Any]]:
        """Process a single document and return chunks with metadata"""
        try:
            logger.info(f"Processing document: {file_name}")
            
            # Extract text
            text = self.extract_text_from_file(file_path, file_type)
            if not text:
                logger.error(f"Failed to extract text from {file_name}")
                return []
            
            # Create metadata
            metadata = {
                "source": file_name,
                "file_type": file_type,
                "file_path": file_path
            }
            
            # Chunk text
            chunks = self.chunk_text(text, metadata)
            
            logger.info(f"Successfully processed {file_name}: {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error processing document {file_name}: {str(e)}")
            return []
    
    def process_multiple_documents(self, file_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Process multiple documents"""
        all_chunks = []
        
        for file_info in file_list:
            try:
                chunks = self.process_document(
                    file_info['path'],
                    file_info['name'],
                    file_info['type']
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {file_info['name']}: {str(e)}")
                continue
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks
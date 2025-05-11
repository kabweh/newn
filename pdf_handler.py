#!/usr/bin/env python
# coding: utf-8
"""
PDF upload and text extraction module for AI Tutor application.
Handles PDF files and extracts text using PyPDF2 and poppler-utils.
Aims to extract text from the entire document.
"""
import os
import subprocess
import tempfile
from typing import Tuple, Optional
import PyPDF2

class PDFHandler:
    """Handles PDF uploads and text extraction."""
    
    def __init__(self, upload_folder: str = "uploads/pdfs"):
        """
        Initialize the PDF handler.
        
        Args:
            upload_folder: Directory to store uploaded PDFs
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_pdf(self, pdf_file, filename: str) -> str:
        """
        Save an uploaded PDF file to disk.
        
        Args:
            pdf_file: The uploaded PDF file object
            filename: Name to save the file as
            
        Returns:
            Path to the saved PDF file
        """
        file_path = os.path.join(self.upload_folder, filename)
        
        # Save the PDF file
        # Ensure the file cursor is at the beginning if it has been read before
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        with open(file_path, 'wb') as f:
            f.write(pdf_file.read())
            
        return file_path
    
    def extract_text_with_pypdf2(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text from a PDF using PyPDF2.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple (extracted_text, error_message). Text is None if extraction fails.
        """
        try:
            text = ""
            num_pages = 0
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check if the PDF is encrypted
                if reader.is_encrypted:
                    return None, "This PDF is encrypted and requires a password for text extraction."
                
                num_pages = len(reader.pages)
                # Add diagnostic info about page count
                text += f"(PyPDF2 attempting to process {num_pages} pages)\n\n" 
                
                # Extract text from each page
                for page_num in range(num_pages):
                    try:
                        page = reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text: # Only append if text was actually extracted
                            text += page_text.strip() + "\n\n" # Use strip() and double newline
                    except Exception as page_e:
                        # Log error for specific page and continue if possible
                        text += f"\n[Error extracting page {page_num + 1}: {str(page_e)}]\n"
                        continue # Try next page
            
            # Check if any meaningful text was extracted besides the diagnostic info
            if len(text.replace(f"(PyPDF2 attempting to process {num_pages} pages)\n\n", "").strip()) == 0:
                 return None, f"PyPDF2 processed {num_pages} pages but extracted no text."

            return text.strip(), None # Return stripped text and no error
        except Exception as e:
            return None, f"Error extracting text with PyPDF2: {str(e)}"
    
    def extract_text_with_pdftotext(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text from a PDF using poppler-utils' pdftotext.
        Ensures it tries to process the whole document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple (extracted_text, error_message). Text is None if extraction fails.
        """
        temp_path = None
        try:
            # Create a temporary file to store the extracted text
            # Use delete=False and manual cleanup in finally block
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Run pdftotext command, ensuring no page limits are set by default
            # Using -layout to preserve structure which might help segmentation later
            command = ['pdftotext', '-layout', pdf_path, temp_path]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False, # Don't raise exception on non-zero exit
                timeout=60 # Add a timeout to prevent hangs
            )
            
            if result.returncode != 0:
                # Check stderr for common errors like encryption
                stderr_lower = result.stderr.lower()
                if "command not found" in stderr_lower:
                     return None, "pdftotext command not found. Please ensure poppler-utils is installed."
                if "pdf is encrypted" in stderr_lower:
                     return None, "pdftotext failed: PDF is encrypted."
                return None, f"pdftotext failed (code {result.returncode}): {result.stderr}"
            
            # Read the extracted text
            with open(temp_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text or text.isspace():
                return None, "pdftotext ran successfully but extracted no text."

            return text.strip(), None # Return stripped text and no error
        except subprocess.TimeoutExpired:
             return None, "pdftotext command timed out after 60 seconds."
        except FileNotFoundError:
             return None, "pdftotext command not found. Please ensure poppler-utils is installed."
        except Exception as e:
            return None, f"Error during pdftotext execution: {str(e)}"
        finally:
            # Ensure temporary file is deleted
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass # Ignore deletion errors

    
    def process_pdf(self, pdf_file, filename: str) -> Tuple[str, Optional[str]]:
        """
        Process an uploaded PDF: save it and extract text from the entire document.
        Prioritizes pdftotext, falls back to PyPDF2.
        
        Args:
            pdf_file: The uploaded PDF file object
            filename: Name to save the file as
            
        Returns:
            Tuple containing (file_path, extracted_text or error_message)
        """
        file_path = self.save_pdf(pdf_file, filename)
        final_text = None
        error_message = "No text extraction method succeeded."

        # 1. Try pdftotext
        text_pdt, err_pdt = self.extract_text_with_pdftotext(file_path)
        if text_pdt:
            final_text = text_pdt
            error_message = None # Success
        else:
            # Record pdftotext error if it occurred
            error_message = f"pdftotext failed: {err_pdt}. " if err_pdt else "pdftotext extracted no text. "

        # 2. If pdftotext failed or returned no text, try PyPDF2
        if final_text is None:
            text_pypdf, err_pypdf = self.extract_text_with_pypdf2(file_path)
            if text_pypdf:
                final_text = text_pypdf
                error_message = None # Success with fallback
            elif err_pypdf:
                # Append PyPDF2 error to the previous message
                error_message += f"PyPDF2 also failed: {err_pypdf}"
            else:
                 error_message += "PyPDF2 also extracted no text."

        # If still no text, return the combined error message
        if final_text is None:
             return file_path, error_message
        else:
             return file_path, final_text

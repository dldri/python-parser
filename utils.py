from io import BytesIO
import pymupdf
import streamlit as st


def extract_text_from_pdf(pdf_file: BytesIO) -> dict[int, str]:
    """
    Extract text content from a PDF file using PyMuPDF.

    Args:
        pdf_file: Uploaded PDF file object

    Returns:
        Dict[int, str]: Dictionary with page numbers as keys and text content as values
    """
    try:
        # Read the file content into bytes
        pdf_bytes = pdf_file.read()

        # Open PDF from bytes
        pdf_document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        page_texts: dict[int, str] = {}

        # Extract text from each page
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            page_text = page.get_textpage().extractText()
            if page_text:
                page_texts[page_num + 1] = page_text  # 1-based page numbering

        pdf_document.close()
        return page_texts
    except Exception as e:
        _ = st.error(f"Error extracting text from PDF: {str(e)}")
        return {}

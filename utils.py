from io import BytesIO
import re
import pymupdf
import streamlit as st
import os
from streamlit.runtime.uploaded_file_manager import UploadedFile


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


def apply_regex_pattern(text: str, pattern: str) -> list[str]:
    """
    Apply regex pattern to text and return all matches.

    Args:
        text: Text content to search
        pattern: Regex pattern to apply

    Returns:
        List of matched strings
    """
    try:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        return matches
    except re.error as e:
        _ = st.error(f"Invalid regex pattern: {str(e)}")
        return []


def process_pdf_files(uploaded_files: list[UploadedFile], regex_pattern: str) -> str:
    """
    Process multiple PDF files and extract matches based on regex pattern.

    Args:
        uploaded_files: List of uploaded PDF files
        regex_pattern: Regex pattern to apply

    Returns:
        str: Formatted results
    """
    results: list[str] = []

    # Create progress bar for bulk processing
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        file_name = uploaded_file.name
        _ = progress_bar.progress(progress)
        _ = status_text.text(
            f"Processing {file_name}... ({i + 1}/{len(uploaded_files)})"
        )

        # Validate file type
        if not uploaded_file.name.lower().endswith(".pdf"):
            _ = st.warning(f"Skipping {uploaded_file.name}: Not a PDF file")
            continue

        # Validate file size (200MB limit)
        if uploaded_file.size > 200 * 1024 * 1024:
            _ = st.warning(
                f"Skipping {uploaded_file.name}: File too large (>200MB)")
            continue

        try:
            # Extract text from PDF (returns dict with page numbers)
            page_texts = extract_text_from_pdf(uploaded_file)

            if not page_texts:
                _ = st.warning(
                    f"No text content found in {uploaded_file.name}")
                continue

            # Process each page separately
            document_name = os.path.splitext(uploaded_file.name)[0]

            for page_num, page_text in page_texts.items():
                # Apply regex pattern to this page
                matches = apply_regex_pattern(page_text, regex_pattern)

                # Format results: document_name, page_number, matched_pattern
                for match in matches:
                    # Handle tuple matches (when regex has groups)
                    if isinstance(match, tuple):
                        match_str = " ".join(str(m) for m in match if m)
                    else:
                        match_str = str(match)

                    results.append(f"{document_name}\t{page_num}\t{match_str}")

        except Exception as e:
            _ = st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue

    # Clear progress indicators
    _ = progress_bar.empty()
    _ = status_text.empty()

    if results:
        # Add header row for Excel compatibility
        header = "Document\tPage\tMatch"
        return header + "\n" + "\n".join(results)
    else:
        return ""

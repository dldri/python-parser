from io import BytesIO
import io
import re
import zipfile
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


def process_pdf_files(uploaded_files: list[UploadedFile], regex_pattern: str, create_highlighted_pdfs: bool = False) -> tuple[str, bytes | None]:
    """
    Process multiple PDF files and extract matches based on regex pattern.

    Args:
        uploaded_files: List of uploaded PDF files
        regex_pattern: Regex pattern to apply
        create_highlighted_pdfs: Whether to create highlighted PDFs

    Returns:
        tuple[str, bytes | None]: Formatted results and zip file with highlighted PDFs
    """
    results: list[str] = []
    highlighted_pdfs = {}

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
        tag_count = 1

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
            # Read PDF bytes for potential highlighting
            _ = uploaded_file.seek(0)  # Reset file pointer
            pdf_bytes = uploaded_file.read()

            # Extract text from PDF (returns dict with page numbers)
            # Reset file pointer for text extraction
            _ = uploaded_file.seek(0)
            page_texts = extract_text_from_pdf(uploaded_file)

            if not page_texts:
                _ = st.warning(
                    f"No text content found in {uploaded_file.name}")
                continue

            # Process each page separately
            document_name = os.path.splitext(uploaded_file.name)[0]
            has_matches = False

            for page_num, page_text in page_texts.items():
                # Apply regex pattern to this page
                matches = apply_regex_pattern(page_text, regex_pattern)

                # Format results: document_name, page_number, matched_pattern
                for match in matches:
                    has_matches = True
                    # Handle tuple matches (when regex has groups)
                    if isinstance(match, tuple):
                        match_str = " ".join(str(m) for m in match if m)
                    else:
                        match_str = str(match)

                    results.append(
                        f"{tag_count}\t{document_name}\t{page_num}\t{match_str}")
                    tag_count += 1

            # Create highlighted PDF if requested and matches were found
            if create_highlighted_pdfs and has_matches:
                highlighted_pdf_bytes = highlight_matches_in_pdf(
                    pdf_bytes, regex_pattern, uploaded_file.name)
                highlighted_pdfs[f"{document_name}_highlighted.pdf"] = highlighted_pdf_bytes

        except Exception as e:
            _ = st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue

    # Clear progress indicators
    _ = progress_bar.empty()
    _ = status_text.empty()

    # Create zip file with highlighted PDFs if an exist
    zip_bytes = None
    if highlighted_pdfs:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, pdf_content in highlighted_pdfs.items():
                zip_file.writestr(filename, pdf_content)
        zip_bytes = zip_buffer.getvalue()

    if results:
        # Add header row for Excel compatibility
        header = "Index\tDocument\tPage\tMatch"
        return header + "\n" + "\n".join(results), zip_bytes
    else:
        return "", zip_bytes


def highlight_matches_in_pdf(pdf_bytes: bytes, regex_pattern: str, filename: str) -> bytes:
    """
    Create a new PDF with highlighted matches.

    Args:
        pdf_bytes: Original PDF content as bytes
        regex_pattern: Regex pattern to search for
        filename: Name of the file for error reporting

    Returns:
        bytes: New PDF with highlighted matches
    """

    try:
        # Open the original PDF
        pdf_document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        tag_count = 1

        # Process each page
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]

            # Get text instances that match the pattern
            page_text = page.get_textpage().extractText()
            matches = re.finditer(regex_pattern, page_text,
                                  re.MULTILINE | re.IGNORECASE)

            # For each match, find its location on the page and highlight it
            for match in matches:
                match_text = match.group()
                # Search for text instances on the page
                text_instances = page.get_textpage().search(match_text)

                # Highlight each instance
                for inst in text_instances:
                    # Create a highlight annotation
                    highlight = page.add_highlight_annot(inst)
                    # Yellow highlight
                    highlight.set_colors({"stroke": [1, 1, 0]})
                    highlight.update()
                    # Update annotation to have identify the tag index
                    annot_info = highlight.info
                    annot_info["subject"] = str(tag_count)
                    highlight.set_info(annot_info)
                    tag_count += 1

        # Get the modified PDF as bytes
        modified_pdf_bytes = pdf_document.write()
        pdf_document.close()

        return modified_pdf_bytes

    except Exception as e:
        _ = st.error(f"Error highlighting matches in {filename}: {str(e)}")
        return pdf_bytes  # Return original if highlighting fails

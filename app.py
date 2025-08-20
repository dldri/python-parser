import streamlit as st
import pymupdf
import re
import io
import tempfile
import os
from typing import List, Tuple, Dict


def extract_text_from_pdf(pdf_file) -> Dict[int, str]:
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
        page_texts = {}

        # Extract text from each page
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            page_text = page.get_text()
            if page_text:
                page_texts[page_num + 1] = page_text  # 1-based page numbering

        pdf_document.close()
        return page_texts
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return {}


def apply_regex_pattern(text: str, pattern: str) -> List[str]:
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
        st.error(f"Invalid regex pattern: {str(e)}")
        return []


def process_pdf_files(uploaded_files, regex_pattern: str) -> str:
    """
    Process multiple PDF files and extract matches based on regex pattern.

    Args:
        uploaded_files: List of uploaded PDF files
        regex_pattern: Regex pattern to apply

    Returns:
        str: Formatted results
    """
    results = []

    # Create progress bar for bulk processing
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(
            f"Processing {uploaded_file.name}... ({i + 1}/{len(uploaded_files)})"
        )

        # Validate file type
        if not uploaded_file.name.lower().endswith(".pdf"):
            st.warning(f"Skipping {uploaded_file.name}: Not a PDF file")
            continue

        # Validate file size (200MB limit)
        if uploaded_file.size > 200 * 1024 * 1024:
            st.warning(f"Skipping {uploaded_file.name}: File too large (>200MB)")
            continue

        try:
            # Extract text from PDF (returns dict with page numbers)
            page_texts = extract_text_from_pdf(uploaded_file)

            if not page_texts:
                st.warning(f"No text content found in {uploaded_file.name}")
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
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    if results:
        # Add header row for Excel compatibility
        header = "Document\tPage\tMatch"
        return header + "\n" + "\n".join(results)
    else:
        return ""


def main():
    """Main Streamlit application"""

    st.title("📄 PDF Text Extraction Tool")
    st.markdown("Upload PDF files and extract text patterns using regex")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Regex pattern input
        st.subheader("Regex Pattern")
        regex_pattern = st.text_input(
            "Enter regex pattern:",
            value=r"\b\d{4}-\d{4}-\d{4}\b",
            help="Example: \\b\\d{4}-\\d{4}-\\d{4}\\b for patterns like 1234-5678-9012",
        )

        # Pattern examples
        with st.expander("Common Pattern Examples"):
            st.code("\\b\\d{4}-\\d{4}-\\d{4}\\b", language="regex")
            st.caption("Matches: 1234-5678-9012")

            st.code("\\b[A-Z]{2}\\d{6}\\b", language="regex")
            st.caption("Matches: AB123456")

            st.code("\\$\\d+\\.\\d{2}", language="regex")
            st.caption("Matches: $123.45")

            st.code("\\b\\w+@\\w+\\.\\w+\\b", language="regex")
            st.caption("Matches: email@domain.com")

        # File size limit info
        st.info("📋 File Limits:\n- Max size: 200MB per file\n- Format: PDF only")

        # Excel compatibility info
        st.success(
            "📊 Excel Ready:\nResults use tabs - copy & paste directly into Excel!"
        )

    # Main content area
    st.header("Upload PDF Files")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more PDF files to process",
    )

    if uploaded_files and regex_pattern:
        st.success(f"Uploaded {len(uploaded_files)} file(s)")

        # Display uploaded files
        with st.expander("Uploaded Files"):
            for file in uploaded_files:
                file_size_mb = file.size / (1024 * 1024)
                st.write(f"📄 {file.name} ({file_size_mb:.2f} MB)")

        # Process button
        if st.button("🔍 Extract Text Patterns", type="primary"):
            if not regex_pattern.strip():
                st.error("Please enter a regex pattern")
                return

            with st.spinner("Processing PDF files..."):
                results = process_pdf_files(uploaded_files, regex_pattern)

            if results:
                st.success("✅ Processing completed!")

                # Display results
                st.subheader("Results")
                st.text_area(
                    "Extracted patterns:",
                    value=results,
                    height=300,
                    help="Format: document_name [TAB] page_number [TAB] matched_pattern (Excel-ready)",
                )

                # Download button
                st.download_button(
                    label="💾 Download Results (TSV)",
                    data=results,
                    file_name="pdf_extraction_results.tsv",
                    mime="text/tab-separated-values",
                )

                # Statistics
                num_matches = len(results.split("\n")) if results else 0
                st.metric("Total Matches Found", num_matches)

            else:
                st.warning("No matches found in the uploaded files")
                st.info(
                    "Try adjusting your regex pattern or check if the PDFs contain the expected text"
                )

    elif uploaded_files and not regex_pattern:
        st.warning("Please enter a regex pattern to process the files")

    elif not uploaded_files:
        st.info("👆 Upload PDF files to get started")

        # Sample usage instructions
        with st.expander("How to Use"):
            st.markdown(
                """
            1. **Upload PDFs**: Select one or more PDF files using the file uploader
            2. **Set Pattern**: Enter a regex pattern to match specific text patterns
            3. **Process**: Click the 'Extract Text Patterns' button
            4. **Review**: Check the results and download as needed
            
            **Output Format**: Each line contains tab-separated values:
            `document_name [TAB] page_number [TAB] matched_pattern`
            
            **Excel Copy-Paste**: You can copy the results and paste directly into Excel - each tab will create a new column.
            
            **Tips**:
            - Use the sidebar examples for common patterns
            - Test your regex pattern with a single file first
            - Files larger than 200MB will be skipped
            """
            )


if __name__ == "__main__":
    main()

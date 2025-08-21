import streamlit as st
from utils import process_pdf_files


def main():
    """Main Streamlit application"""

    _ = st.title("📄 PDF Text Extraction Tool")
    _ = st.markdown("Upload PDF files and extract text patterns using regex")

    # Sidebar for configuration
    with st.sidebar:
        _ = st.header("Configuration")

        # Regex pattern input
        _ = st.subheader("Regex Pattern")
        regex_pattern = st.text_input(
            "Enter regex pattern:",
            value=r"^\d{4}-.*",
            help="Example: ^\\d{4}-.* for patterns like 2100-BDG-0001",
        )

        # Pattern examples
        with st.expander("Common Pattern Examples"):
            _ = st.code("\\b\\d{4}-\\d{4}-\\d{4}\\b", language="regex")
            _ = st.caption("Matches: 1234-5678-9012")

            _ = st.code("\\b[A-Z]{2}\\d{6}\\b", language="regex")
            _ = st.caption("Matches: AB123456")

            _ = st.code("\\$\\d+\\.\\d{2}", language="regex")
            _ = st.caption("Matches: $123.45")

            _ = st.code("\\b\\w+@\\w+\\.\\w+\\b", language="regex")
            _ = st.caption("Matches: email@domain.com")

        # File size limit info
        _ = st.info("📋 File Limits:\n- Max size: 200MB per file\n- Format: PDF only")

        # Excel compatibility info
        _ = st.success(
            "📊 Excel Ready:\nResults use tabs - copy & paste directly into Excel!"
        )

    # Main content area
    _ = st.header("Upload PDF Files")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more PDF files to process",
    )

    if uploaded_files and regex_pattern:
        _ = st.success(f"Uploaded {len(uploaded_files)} file(s)")

        # Display uploaded files
        with st.expander("Uploaded Files"):
            for file in uploaded_files:
                file_size_mb = file.size / (1024 * 1024)
                st.write(f"📄 {file.name} ({file_size_mb:.2f} MB)")

        # Options for processing
        col1, col2 = st.columns([3, 1])

        with col1:
            process_button = st.button("🔍 Extract Text Patterns", type="primary")

        with col2:
            create_highlights = st.checkbox("🔰 Highlight matches", help="Create highlighted PDFs for download")

        # Process button
        if process_button:
            if not regex_pattern.strip():
                _ = st.error("Please enter a regex pattern")
                return

            with st.spinner("Processing PDF files..."):
                results, highlighted_zip = process_pdf_files(uploaded_files, regex_pattern, create_highlights)

            if results:
                _ = st.success("✅ Processing completed!")

                # Display results
                _ = st.subheader("Results")
                _ = st.text_area(
                    "Extracted patterns:",
                    value=results,
                    height=300,
                    help="Format: document_name [TAB] page_number [TAB] matched_pattern (Excel-ready)",
                )

                # Download button
                col1, col2 = st.columns(2)

                with col1:
                    _ = st.download_button(
                        label="💾 Download Results (TSV)",
                        data=results,
                        file_name="pdf_extraction_results.tsv",
                        mime="text/tab-separated-values",
                    )

                with col2:
                    if highlighted_zip:
                        _ = st.download_button(
                            label="🔰 Download Highlighted PDFs",
                            data=highlighted_zip,
                            file_name="highlighted_pdfs.zip",
                            mime="application/zip",
                            help="ZIP file containing PDFs with highlighted matches"
                        )
                    else:
                        st.info("No highlighted PDFs (no matches or highlighting disabled)")


                # Statistics - results - 1 to account for header
                num_matches = len(results.split("\n")) if results else 0
                _ = st.metric("Total Matches Found", num_matches - 1)

            else:
                _ = st.warning("No matches found in the uploaded files")
                _ = st.info(
                    "Try adjusting your regex pattern or check if the PDFs contain the expected text"
                )

    elif uploaded_files and not regex_pattern:
        _ = st.warning("Please enter a regex pattern to process the files")

    elif not uploaded_files:
        _ = st.info("👆 Upload PDF files to get started")

        # Sample usage instructions
        with st.expander("How to Use"):
            _ = st.markdown(
                """
            1. **Upload PDFs**: Select one or more PDF files using the file uploader
            2. **Set Pattern**: Enter a regex pattern to match specific text patterns
            3. **Process**: Click the 'Extract Text Patterns' button
            4. **Review**: Check the results and download as needed
            
            **Output Format**: Each line contains tab-separated values:
            `document_name [TAB] page_number [TAB] matched_pattern`
            
            **Excel Copy-Paste**: You can copy the results and paste directly into Excel - each tab will create a new column.

            **Highlighting Feature**: Enable 'Highlight matches' to create downloadable PDFs with fellow highlighting on all matched patterns.
            
            **Tips**:
            - Use the sidebar examples for common patterns
            - Test your regex pattern with a single file first
            - Files larger than 200MB will be skipped
            """
            )


if __name__ == "__main__":
    main()

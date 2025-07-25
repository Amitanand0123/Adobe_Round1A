# main.py

import json
import time
import logging
import sys
from pathlib import Path
from pdf_processor import PDFProcessor
from hierarchy_builder import HierarchyBuilder

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

def process_single_pdf(pdf_path: Path, output_path: Path) -> bool:
    """
    Processes a single PDF file to extract its title and hierarchical outline.
    """
    logger.info(f"--- Starting processing for: {pdf_path.name} ---")
    start_time = time.time()
    
    try:
        # Initialize the core components
        processor = PDFProcessor()
        builder = HierarchyBuilder()
        
        # Step 1: Use PDFProcessor to extract structured data from the PDF.
        processed_pages = processor.process_pdf(str(pdf_path))
        if not processed_pages:
            logger.error(f"Could not extract any data from PDF: {pdf_path.name}")
            return False

        # Step 2: Use HierarchyBuilder to analyze the data and build the final outline.
        result = builder.build(processed_pages)
        
        # Step 3: Save the resulting dictionary as a JSON file.
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
            
        processing_time = time.time() - start_time
        logger.info(f"Successfully processed {pdf_path.name} in {processing_time:.2f} seconds.")
        return True
        
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {pdf_path.name}: {e}", exc_info=True)
        return False

def main():
    """
    Main function to run the PDF processing pipeline.
    """
    # Define input and output directories within the Docker container
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure the output directory exists
    output_dir.mkdir(exist_ok=True, parents=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF(s) to process in '{input_dir}'.")
    
    # Process each PDF file found in the input directory
    for pdf_file in pdf_files:
        output_file = output_dir / f"{pdf_file.stem}.json"
        process_single_pdf(pdf_file, output_file)
            
    logger.info("--- All processing complete ---")

if __name__ == "__main__":
    main()
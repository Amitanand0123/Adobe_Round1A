# pdf_processor.py

import logging
import pdfplumber
from pdf2image import convert_from_path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Processes a PDF to extract text elements and their properties.
    """

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts structured text data from each page of a PDF.
        """
        pages_data = []
        
        try:
            # Using pdfplumber to open and parse the PDF
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    logger.info(f"Processing Page {page_num}...")
                    
                    # Extract words with detailed attributes for robust analysis
                    words = page.extract_words(
                        x_tolerance=1.5,
                        y_tolerance=3,
                        keep_blank_chars=False,
                        use_text_flow=True,
                        horizontal_ltr=True,
                        extra_attrs=["fontname", "size"]
                    )
                    
                    # Group individual words into logical text blocks (lines/paragraphs)
                    text_blocks = self._group_words_into_blocks(words, page_num)
                    
                    pages_data.append({
                        'page_num': page_num,
                        'width': float(page.width),
                        'height': float(page.height),
                        'text_blocks': text_blocks,
                    })
            
            logger.info(f"Finished processing all pages for '{pdf_path}'.")
            return pages_data
        except Exception as e:
            logger.error(f"Failed to process PDF '{pdf_path}'. Error: {e}", exc_info=True)
            return []

    def _unify_bbox(self, bboxes: List[Tuple]) -> Tuple[float, float, float, float]:
        """Calculates a single bounding box that encompasses all given boxes."""
        if not bboxes:
            return (0, 0, 0, 0)
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)
        return (x0, y0, x1, y1)

    def _group_words_into_blocks(self, words: List[Dict], page_num: int) -> List[Dict]:
        """
        Groups individual words into logical text blocks using a heuristic approach.
        """
        if not words:
            return []
        
        # Group words into lines based on vertical position
        lines = []
        if words:
            sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
            current_line = [sorted_words[0]]
            for word in sorted_words[1:]:
                if abs(word['top'] - current_line[-1]['top']) < 2: # Tolerance for same-line words
                    current_line.append(word)
                else:
                    lines.append(sorted(current_line, key=lambda w: w['x0']))
                    current_line = [word]
            lines.append(sorted(current_line, key=lambda w: w['x0']))

        # Group lines into blocks based on font properties and spacing
        blocks = []
        if lines:
            current_block_lines = [lines[0]]
            for line in lines[1:]:
                prev_line = current_block_lines[-1]
                
                vertical_gap = line[0]['top'] - prev_line[0]['top']
                font_name_match = line[0]['fontname'] == prev_line[0]['fontname']
                font_size_match = abs(line[0]['size'] - prev_line[0]['size']) < 1

                # A new block starts if there's a large vertical gap or font properties change
                is_new_block = (vertical_gap > prev_line[0]['size'] * 1.6) or not font_name_match or not font_size_match

                if is_new_block:
                    text = " ".join(" ".join(w['text'] for w in ln) for ln in current_block_lines)
                    all_words_in_block = [w for ln in current_block_lines for w in ln]
                    bboxes = [(w['x0'], w['top'], w['x1'], w['bottom']) for w in all_words_in_block]
                    
                    blocks.append({
                        "text": text,
                        "bbox": self._unify_bbox(bboxes),
                        "font_name": all_words_in_block[0]['fontname'],
                        "font_size": round(all_words_in_block[0]['size'], 2),
                        "page_num": page_num
                    })
                    current_block_lines = [line]
                else:
                    current_block_lines.append(line)

            # Append the last remaining block
            text = " ".join(" ".join(w['text'] for w in ln) for ln in current_block_lines)
            all_words_in_block = [w for ln in current_block_lines for w in ln]
            bboxes = [(w['x0'], w['top'], w['x1'], w['bottom']) for w in all_words_in_block]
            
            blocks.append({
                "text": text,
                "bbox": self._unify_bbox(bboxes),
                "font_name": all_words_in_block[0]['fontname'],
                "font_size": round(all_words_in_block[0]['size'], 2),
                "page_num": page_num
            })

        return blocks
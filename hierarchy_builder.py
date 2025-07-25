# hierarchy_builder.py

import logging
import re
from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

class HierarchyBuilder:
    """
    Builds a hierarchical outline (Title, H1, H2, H3) from processed PDF data.
    """

    def _is_header_or_footer(self, block: Dict, page_height: float) -> bool:
        """Checks if a text block is likely a header or footer."""
        y_pos = block['bbox'][1]
        # Considers top 8% and bottom 8% of the page as header/footer zones
        return y_pos < page_height * 0.08 or y_pos > page_height * 0.92

    def _is_toc_entry(self, text: str) -> bool:
        """Checks if text is likely a table of contents entry."""
        # Looks for patterns like "......... 5"
        return bool(re.search(r'\.{4,}\s*\d+\s*$', text))

    def _get_block_features(self, block: Dict, page_width: float) -> Dict:
        """Extracts key features from a text block for classification."""
        text = block['text'].strip()
        x0, _, x1, _ = block['bbox']
        word_count = len(text.split())

        return {
            "text": text,
            "font_size": block.get('font_size', 0),
            "is_bold": "bold" in block.get('font_name', '').lower() or "black" in block.get('font_name', '').lower(),
            "is_all_caps": text.isupper() and word_count > 0,
            "starts_with_number": bool(re.match(r'^\d+(\.\d+)*\s+', text)),
            "is_centered": abs(((x0 + x1) / 2) - (page_width / 2)) < (page_width * 0.15), # 15% tolerance for centering
            "word_count": word_count,
            "is_toc": self._is_toc_entry(text),
            "original_block": block
        }

    def _is_potential_heading(self, features: Dict) -> bool:
        """Determines if a block is a potential heading based on its features."""
        # Basic disqualifiers
        if not features['text'] or features['word_count'] > 20 or features['is_toc'] or features['text'].isdigit():
            return False
        
        # Strong indicators of a heading
        if features['font_size'] > 14 and features['word_count'] < 15:
            return True
        if features['starts_with_number'] and features['word_count'] < 15:
            return True
        if features['is_bold'] and features['word_count'] < 15:
            return True
        if features['is_all_caps'] and features['font_size'] > 11 and features['word_count'] < 15:
            return True

        return False

    def _extract_title(self, text_blocks: List[Dict], page_width: float) -> str:
        """Extracts the document title, focusing on the top of the first page."""
        first_page_blocks = [b for b in text_blocks if b.get('page_num', 1) == 1 and b['text'].strip()]
        
        if not first_page_blocks:
            return "Untitled Document"

        candidates = []
        for block in first_page_blocks:
            # Only consider blocks in the top 40% of the first page
            if block['bbox'][1] > 400: continue

            features = self._get_block_features(block, page_width)
            if not features['text'] or features['word_count'] > 25: continue
            
            # Score candidates based on font size and centeredness
            score = features['font_size']
            if features['is_centered']:
                score *= 1.5
            if features['is_bold']:
                score *= 1.2
            
            candidates.append((score, features['text']))

        return max(candidates, key=lambda item: item[0])[1] if candidates else "Untitled Document"

    def _assign_heading_levels(self, heading_candidates: List[Dict]) -> List[Dict]:
        """Assigns H1, H2, H3 levels using KMeans clustering on font sizes."""
        if not heading_candidates:
            return []

        if len(heading_candidates) == 1:
            block = heading_candidates[0]['original_block']
            return [{"level": 'H1', "text": heading_candidates[0]['text'], "page": block['page_num']}]

        font_sizes = np.array([[h['font_size']] for h in heading_candidates])
        unique_sizes = np.unique(font_sizes)
        
        # Cluster into at most 3 levels (H1, H2, H3)
        n_clusters = min(len(unique_sizes), 3)
        if n_clusters == 0: return []

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto').fit(font_sizes)
        # Map larger font sizes to higher heading levels
        cluster_centers = sorted(kmeans.cluster_centers_.flatten(), reverse=True)
        size_to_level = {center: f"H{i+1}" for i, center in enumerate(cluster_centers)}
        
        outline = []
        for i, features in enumerate(heading_candidates):
            cluster_label = kmeans.labels_[i]
            cluster_center = kmeans.cluster_centers_[cluster_label][0]
            level = size_to_level.get(cluster_center, f'H{n_clusters}') # Default to lowest level
            
            block = features['original_block']
            outline.append({
                "level": level,
                "text": features['text'],
                "page": block['page_num'],
                "y_pos": block['bbox'][1] # Keep for sorting
            })
        return outline

    def build(self, processed_pages: List[Dict]) -> Dict[str, Any]:
        """The main build method to create the final JSON structure."""
        if not processed_pages:
            return {"title": "No Content Found", "outline": []}

        all_blocks = [block for page in processed_pages for block in page.get('text_blocks', [])]
        page_height = processed_pages[0].get('height', 842) # Default A4 height
        page_width = processed_pages[0].get('width', 595)   # Default A4 width
        
        # Filter out headers and footers to create a clean list of content blocks
        core_content_blocks = [b for b in all_blocks if not self._is_header_or_footer(b, page_height)]
        
        title = self._extract_title(core_content_blocks, page_width)
        
        # Identify potential headings from the core content
        block_features = [self._get_block_features(b, page_width) for b in core_content_blocks]
        heading_candidates = [f for f in block_features if self._is_potential_heading(f)]
        # Ensure the title itself is not also listed as a heading
        heading_candidates = [h for h in heading_candidates if h['text'] != title]
        
        # Assign levels and sort the final outline
        outline = self._assign_heading_levels(heading_candidates)
        outline.sort(key=lambda x: (x['page'], x['y_pos']))
        
        # Clean up temporary keys before returning
        for item in outline:
            del item['y_pos']
        
        return {"title": title.replace("\n", " ").strip(), "outline": outline}
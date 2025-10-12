"""
LLM response processing module:
1. text extraction: extract text segments from LLM response in various modes
2. embedding generation: convert extracted text segments into vectors

Supported modes:
- full: full response text
- think_tail: <think> tag after the content
- bullet: numbered bullet points
"""

import re
from typing import List, Dict, Literal, Optional, Tuple
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# define supported extraction modes
EmbeddingMode = Literal['full', 'think_tail', 'bullet']

class TextExtractor:
    @staticmethod
    def extract_full(response: str) -> Optional[str]:
        """Return the full response text for embedding."""
        return response.strip() if response else None

    @staticmethod
    def extract_think_tail(response: str) -> Optional[str]:
        """
        Extract the part after '</think>' tag.
        If not found, return None.
        """
        if not response:
            return None
        parts = response.split("</think>", 1)
        return parts[1].strip() if len(parts) > 1 else None

    @staticmethod
    def extract_bullets(response: str) -> List[Tuple[str, str, str]]:
        """
        Extract bullet point segments in the form:
        1. **Title** Description (across lines)
        Return list of tuples, one per bullet.
        """
        if not response:
            return []

        # Only use content after </think> if present
        tail = TextExtractor.extract_think_tail(response) or response

        # Match patterns like 1. **Title** Description (across lines)
        pattern = r"\n?\s*(\d+)\.\s+\*\*(.+?)\*\*\s*(.*?)(?=(\n\s*\d+\.\s+\*\*|$))"
        matches = re.finditer(pattern, tail, re.DOTALL)

        bullets = []
        for match in matches:
            index, title, desc = match.group(1), match.group(2), match.group(3)
            bullets.append((index, title, desc.strip()))

        return bullets

    @staticmethod
    def format_bullet(bullet_tuple: Tuple[str, str, str]) -> str:
        """convert (number, title, description) tuple to formatted string"""
        number, title, desc = bullet_tuple
        return f"{number}. **{title}** {desc.strip()}"

class EmbeddingProcessor:
    """
    LLM response processing module:
    1. text extraction: extract text segments from LLM response in various modes
    2. embedding generation: convert extracted text segments into vectors
    """
    
    def __init__(self, model_name: str = 'Qodo/Qodo-Embed-1-1.5B', max_tokens: int = 2048):
        """
        Args:
            model_name: name of the embedding model to use
            max_tokens: maximum number of text tokens
        """
        self.model = SentenceTransformer(model_name)
        self.extractor = TextExtractor()
        self.max_tokens = max_tokens
        self.tokenizer = self.model.tokenizer
        
    def _truncate_text(self, text: str) -> str:
        """limit the text to the maximum number of tokens"""
        tokens = self.tokenizer.encode(text, add_special_tokens=True)
        if len(tokens) <= self.max_tokens:
            return text
            
        print(f"warning: text exceeds maximum number of tokens ({self.max_tokens}). truncating {len(tokens)} tokens.")
        truncated_tokens = tokens[:self.max_tokens]
        truncated_text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
        return truncated_text
        
    def encode(self, text: str) -> np.ndarray:
        """encode single text into embedding"""
        truncated_text = self._truncate_text(text)
        return self.model.encode(truncated_text, convert_to_numpy=True)
        
    def encode_segments(self, response: str, mode: EmbeddingMode, analysis_id: str=None) -> List[Dict]:
        """
        extract text segments from response and encode them.
        
        Args:
            response: LLM response text
            mode: extraction mode ('full', 'think_tail', 'bullet')
            
        Returns:
            text, vector, mode, index, analysis_id
        """
        # extract text segments according to the mode
        if mode == 'full':
            segments = [self.extractor.extract_full(response)]
        elif mode == 'think_tail':
            segments = [self.extractor.extract_think_tail(response)]
        elif mode == 'bullet':
            segments = self.extractor.extract_bullets(response)
        else:
            raise ValueError(f"unsupported mode: {mode}")
            
        # filter out empty segments
        segments = [s for s in segments if s]
        if not segments:
            return []
            
        # format conversion: convert bullet tuples to strings (if needed)
        if mode == 'bullet':
            formatted_segments = [self.extractor.format_bullet(b) for b in segments]
        else:
            formatted_segments = segments
            
        # apply token limit
        truncated_segments = [self._truncate_text(s) for s in formatted_segments]
            
        # generate segment embeddings
        vectors = self.model.encode(truncated_segments, convert_to_numpy=True)
        
        # format the result
        result = []
        for idx, (segment, vec) in enumerate(zip(segments, vectors)):
            result.append({
                'text': segment,
                'vector': vec,
                'mode': mode,
                'index': idx if mode == 'bullet' else None,
                'analysis_id': analysis_id if analysis_id else None
            })
        return result


# 예제 사용법
if __name__ == '__main__':
    # file for testing
    analysis_id = 39
    analysis_file_path = f"data/analysis_results/analysis_{analysis_id}.json"


    open_file = open(analysis_file_path, "r")
    data = json.load(open_file)
    sample_response = data["response"]


    # Debugging for TextExtractor
    print("[Full Response]----------------------------------------")
    print(TextExtractor.extract_full(sample_response))

    print("\n[Think Tail]----------------------------------------")
    print(TextExtractor.extract_think_tail(sample_response))

    print("\n[Bullet Points]----------------------------------------")
    bullets = TextExtractor.extract_bullets(sample_response)
    for b in bullets:
        print("----------------------------------------")
        print(TextExtractor.format_bullet(b))


    # Debugging for EmbeddingProcessor
    processor = EmbeddingProcessor(model_name='Qodo/Qodo-Embed-1-1.5B')

    for mode in ['full', 'think_tail', 'bullet']:
        print(f"\n[Embedding Mode: {mode}]")
        results = processor.encode_segments(sample_response, mode, analysis_id=analysis_id)
        for r in results:
            print(f"- index: {r['index']}, text: {r['text'][:60]}...")

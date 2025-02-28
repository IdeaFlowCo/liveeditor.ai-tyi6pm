"""
Provides token optimization utilities for AI language model interactions, implementing
efficient token counting, context windowing, and prompt optimization strategies to manage
token limits and reduce API costs.
"""

import json
import hashlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import tiktoken  # tiktoken ~=0.5.1

from ...core.utils.logger import get_logger
from ...config import AI_CONFIG 
from ...data.redis.caching_service import cache_set, cache_get, get_content_hash_key

# Initialize logger
logger = get_logger(__name__)

# Configuration constants
DEFAULT_MODEL = AI_CONFIG.get('openai_default_model', 'gpt-4')
DEFAULT_MAX_TOKENS = AI_CONFIG.get('openai_max_tokens', 4096) 
DEFAULT_ENCODING = AI_CONFIG.get('encoding', 'cl100k_base')
TOKEN_LIMIT_BUFFER = AI_CONFIG.get('token_limit_buffer', 100)
CONTEXT_WINDOW_OVERLAP = AI_CONFIG.get('context_window_overlap', 50)
CACHE_TTL = AI_CONFIG.get('token_optimizer_cache_ttl', 3600)  # 1 hour default
CACHE_PREFIX = 'token_optimizer:'
DEFAULT_SIMILARITY_THRESHOLD = 0.8


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    Counts the number of tokens in a given text using the specified encoding.
    
    Args:
        text: Text to count tokens for
        encoding_name: Name of the encoding to use (default: from config)
        
    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0
        
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        # Fallback to rough estimation if tiktoken fails
        return len(text) // 4  # Rough estimate: ~4 chars per token for English
        
        
def truncate_text_to_token_limit(text: str, max_tokens: int, 
                                encoding_name: str = DEFAULT_ENCODING) -> str:
    """
    Truncates text to fit within a specified token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens allowed
        encoding_name: Name of the encoding to use
        
    Returns:
        Truncated text that fits within the token limit
    """
    if not text:
        return ""
        
    # Count tokens in current text
    current_tokens = count_tokens(text, encoding_name)
    
    # If already within limit, return unchanged
    if current_tokens <= max_tokens:
        return text
        
    try:
        # Get encoding
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Encode text to tokens
        tokens = encoding.encode(text)
        
        # Truncate tokens to max_tokens
        truncated_tokens = tokens[:max_tokens]
        
        # Decode truncated tokens back to text
        truncated_text = encoding.decode(truncated_tokens)
        
        logger.warning(
            f"Text truncated from {current_tokens} to {max_tokens} tokens"
        )
        
        return truncated_text
    except Exception as e:
        logger.error(f"Error truncating text: {str(e)}")
        # Fallback: rough truncation based on character count
        ratio = max_tokens / current_tokens
        char_limit = int(len(text) * ratio)
        return text[:char_limit]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculates the semantic similarity between two text strings.
    
    This is a simple implementation that can be improved with more sophisticated
    algorithms as needed.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
        
    # Normalize texts
    def normalize(text):
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
        
    text1 = normalize(text1)
    text2 = normalize(text2)
    
    # If either normalized text is empty, return 0
    if not text1 or not text2:
        return 0.0
        
    # Calculate token sets
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())
    
    # Jaccard similarity: intersection over union
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    if not union:
        return 0.0
        
    return len(intersection) / len(union)


def get_encoding_for_model(model_name: str = DEFAULT_MODEL):
    """
    Gets the appropriate tiktoken encoding for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Tiktoken encoding appropriate for the specified model
    """
    try:
        # For newer models like GPT-4 and GPT-3.5
        if "gpt-4" in model_name or "gpt-3.5" in model_name:
            return tiktoken.encoding_for_model(model_name)
        # For older models or fallback
        else:
            return tiktoken.get_encoding(DEFAULT_ENCODING)
    except Exception as e:
        logger.error(f"Error getting encoding for model {model_name}: {str(e)}")
        # Fallback to default encoding
        return tiktoken.get_encoding(DEFAULT_ENCODING)
        

def generate_cache_key(model: str, content: str, params: Dict = None) -> str:
    """
    Generates a cache key for storing optimization results.
    
    Args:
        model: Model name
        content: Content being optimized
        params: Additional parameters that affect optimization
        
    Returns:
        Cache key for storing/retrieving optimization results
    """
    # Generate a hash of the inputs
    params_str = json.dumps(params or {}, sort_keys=True)
    hash_input = f"{model}:{content}:{params_str}"
    content_hash = get_content_hash_key(hash_input)
    
    return f"{CACHE_PREFIX}{content_hash}"


class TokenOptimizer:
    """
    Provides token optimization utilities for efficient language model usage.
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, 
                max_tokens: int = DEFAULT_MAX_TOKENS,
                use_cache: bool = True):
        """
        Initializes a TokenOptimizer instance with model settings.
        
        Args:
            model: Model name (default: from config)
            max_tokens: Maximum tokens allowed (default: from config)
            use_cache: Whether to use caching (default: True)
        """
        self._model = model
        self._max_tokens = max_tokens
        self._encoding = get_encoding_for_model(model)
        self._use_cache = use_cache
        self.logger = get_logger(__name__)
        
    def count_tokens(self, text: str) -> int:
        """
        Counts tokens in text using the model's encoding.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        if not text:
            return 0
            
        try:
            return len(self._encoding.encode(text))
        except Exception as e:
            self.logger.error(f"Error counting tokens: {str(e)}")
            # Fallback to rough estimation
            return len(text) // 4
            
    def optimize_prompt(self, prompt: str, content: str, 
                       max_tokens: int = None, 
                       reserved_tokens: int = 0) -> str:
        """
        Optimizes a prompt with content to fit within token limits.
        
        Args:
            prompt: The prompt template
            content: The document content to include
            max_tokens: Maximum tokens allowed (default: instance max_tokens)
            reserved_tokens: Tokens to reserve for completion
            
        Returns:
            Optimized prompt with truncated content
        """
        if max_tokens is None:
            max_tokens = self._max_tokens
            
        # Check if result is already cached
        if self._use_cache:
            cache_key = generate_cache_key(
                self._model, 
                content, 
                {"prompt": prompt, "max_tokens": max_tokens, "reserved": reserved_tokens}
            )
            cached_result = cache_get(cache_key)
            if cached_result:
                self.logger.debug("Using cached optimized prompt")
                return cached_result
                
        # Count tokens in prompt
        prompt_tokens = self.count_tokens(prompt)
        
        # Calculate available tokens for content
        available_tokens = max_tokens - prompt_tokens - reserved_tokens - TOKEN_LIMIT_BUFFER
        
        if available_tokens <= 0:
            self.logger.warning("Not enough tokens available for content")
            return prompt
            
        # Optimize content to fit available tokens
        content_tokens = self.count_tokens(content)
        
        if content_tokens > available_tokens:
            self.logger.info(
                f"Content exceeds available tokens ({content_tokens} > {available_tokens}), optimizing..."
            )
            
            # If content is too large, apply windowing or truncation
            if content_tokens > 1.5 * available_tokens:
                # Content is much larger, use context window
                content = self.apply_context_window(content, available_tokens)
            else:
                # Content is slightly larger, just truncate
                content = truncate_text_to_token_limit(
                    content, available_tokens, DEFAULT_ENCODING
                )
                
        # Combine prompt and content
        optimized_prompt = prompt.replace("{content}", content) if "{content}" in prompt else f"{prompt}\n\n{content}"
        
        # Verify final prompt is within limits
        final_tokens = self.count_tokens(optimized_prompt)
        if final_tokens > max_tokens - reserved_tokens:
            self.logger.warning(
                f"Optimized prompt still exceeds token limit: {final_tokens} tokens"
            )
            # Truncate as last resort
            optimized_prompt = truncate_text_to_token_limit(
                optimized_prompt, max_tokens - reserved_tokens - TOKEN_LIMIT_BUFFER, DEFAULT_ENCODING
            )
            
        # Cache the result
        if self._use_cache:
            cache_set(cache_key, optimized_prompt, CACHE_TTL)
            
        return optimized_prompt
        
    def apply_context_window(self, content: str, window_size: int, 
                           query: str = None, 
                           relevance_threshold: float = 0.3) -> str:
        """
        Applies a sliding window approach to select most relevant content.
        
        Args:
            content: The document content
            window_size: Maximum tokens for windowed content
            query: Optional query to prioritize relevant content
            relevance_threshold: Threshold for relevance scoring
            
        Returns:
            Content processed through context window
        """
        # If content already fits in window, return as is
        content_tokens = self.count_tokens(content)
        if content_tokens <= window_size:
            return content
            
        # Split content into paragraphs
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        # If no paragraphs after splitting, split by newline
        if not paragraphs:
            paragraphs = [p for p in content.split('\n') if p.strip()]
            
        # If still no paragraphs, split by sentence
        if not paragraphs:
            paragraphs = [p for p in re.split(r'(?<=[.!?])\s+', content) if p.strip()]
            
        # If query provided, score paragraphs by relevance
        if query:
            scored_paragraphs = []
            for para in paragraphs:
                similarity = calculate_similarity(query, para)
                scored_paragraphs.append((para, similarity))
                
            # Sort by relevance score
            scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
            
            # Take paragraphs until we reach window size
            selected_paras = []
            current_tokens = 0
            
            # Always include highest relevance paragraph
            if scored_paragraphs:
                highest_relevance_para = scored_paragraphs[0][0]
                highest_relevance_tokens = self.count_tokens(highest_relevance_para)
                selected_paras.append(highest_relevance_para)
                current_tokens += highest_relevance_tokens
                
            # Add more paragraphs if they meet threshold and fit
            for para, score in scored_paragraphs[1:]:
                if score < relevance_threshold:
                    continue
                    
                para_tokens = self.count_tokens(para)
                if current_tokens + para_tokens <= window_size - CONTEXT_WINDOW_OVERLAP:
                    selected_paras.append(para)
                    current_tokens += para_tokens
                    
            # If we don't have enough content, add more paragraphs regardless of relevance
            if current_tokens < window_size * 0.5 and len(scored_paragraphs) > len(selected_paras):
                for para, _ in scored_paragraphs:
                    if para in selected_paras:
                        continue
                        
                    para_tokens = self.count_tokens(para)
                    if current_tokens + para_tokens <= window_size - CONTEXT_WINDOW_OVERLAP:
                        selected_paras.append(para)
                        current_tokens += para_tokens
                        
            # Join selected paragraphs
            windowed_content = '\n\n'.join(selected_paras)
        else:
            # Without query, use positional importance (start, end, middle)
            # Calculate tokens for each paragraph
            para_tokens = [(p, self.count_tokens(p)) for p in paragraphs]
            
            # Allocate tokens for the beginning (40%)
            beginning_allocation = int(window_size * 0.4)
            end_allocation = int(window_size * 0.3)
            middle_allocation = window_size - beginning_allocation - end_allocation
            
            # Take paragraphs from the beginning
            beginning_paras = []
            current_tokens = 0
            for para, tokens in para_tokens:
                if current_tokens + tokens <= beginning_allocation:
                    beginning_paras.append(para)
                    current_tokens += tokens
                else:
                    break
                    
            # Take paragraphs from the end
            end_paras = []
            current_tokens = 0
            for para, tokens in reversed(para_tokens):
                if para in beginning_paras:
                    continue
                if current_tokens + tokens <= end_allocation:
                    end_paras.insert(0, para)
                    current_tokens += tokens
                else:
                    break
                    
            # Take some from the middle if there's allocation left
            middle_para_candidates = [
                (para, tokens) for para, tokens in para_tokens 
                if para not in beginning_paras and para not in end_paras
            ]
            
            middle_paras = []
            current_tokens = 0
            
            # Prioritize middle paragraphs with appropriate weighting
            middle_start_idx = len(beginning_paras)
            middle_end_idx = len(paragraphs) - len(end_paras)
            
            if middle_start_idx < middle_end_idx:
                middle_slice = paragraphs[middle_start_idx:middle_end_idx]
                middle_indices = list(range(len(middle_slice)))
                
                # Sort indices to pick from middle outward
                middle_indices.sort(key=lambda i: abs(i - len(middle_slice)//2))
                
                for idx in middle_indices:
                    para = middle_slice[idx]
                    if para in beginning_paras or para in end_paras:
                        continue
                        
                    para_token_count = self.count_tokens(para)
                    if current_tokens + para_token_count <= middle_allocation:
                        middle_paras.append(para)
                        current_tokens += para_token_count
                        
            # Combine all sections (keep original order)
            all_selected_paras = set(beginning_paras + middle_paras + end_paras)
            windowed_content = '\n\n'.join(
                para for para in paragraphs if para in all_selected_paras
            )
            
        # Ensure we're within limits
        if self.count_tokens(windowed_content) > window_size:
            windowed_content = truncate_text_to_token_limit(
                windowed_content, window_size, DEFAULT_ENCODING
            )
            
        return windowed_content
        
    def optimize_document_chunks(self, document: str, 
                                chunk_size: int, 
                                overlap: int = CONTEXT_WINDOW_OVERLAP) -> List[str]:
        """
        Splits large documents into optimally sized chunks for processing.
        
        Args:
            document: Document content
            chunk_size: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of document chunks with appropriate overlap
        """
        # If document is small enough for single chunk, return as is
        document_tokens = self.count_tokens(document)
        if document_tokens <= chunk_size:
            return [document]
            
        # Encode document into tokens
        try:
            tokens = self._encoding.encode(document)
        except Exception as e:
            self.logger.error(f"Error encoding document: {str(e)}")
            # Fallback to simple chunking by paragraphs
            paragraphs = document.split('\n\n')
            chunks = []
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para_size = len(para) // 4  # Rough estimate
                if current_size + para_size > chunk_size:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk.append(para)
                    current_size += para_size
                    
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                
            return chunks
            
        # Calculate chunk boundaries with overlap
        chunk_boundaries = []
        start = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_boundaries.append((start, end))
            start = end - overlap
            
        # Create chunks by decoding token ranges
        chunks = []
        for start, end in chunk_boundaries:
            chunk = self._encoding.decode(tokens[start:end])
            
            # Ensure chunk boundaries maintain semantic integrity
            if start > 0:
                # Try to start at a sentence or paragraph boundary
                match = re.search(r'^[^\n]*?[.!?]\s+', chunk)
                if match:
                    # Remove partial sentence at beginning
                    chunk = chunk[match.end():]
                    
            if end < len(tokens):
                # Try to end at a sentence boundary
                match = re.search(r'[.!?]\s+[^\n]*$', chunk)
                if match:
                    # Keep the sentence boundary
                    chunk = chunk[:match.end()]
                    
            chunks.append(chunk)
            
        return chunks
        
    def detect_similar_request(self, request: Dict, 
                             previous_requests: List[Dict],
                             similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> Tuple[bool, int]:
        """
        Detects if a request is similar to previous requests.
        
        Args:
            request: Current request
            previous_requests: List of previous requests
            similarity_threshold: Threshold for considering requests similar
            
        Returns:
            (bool, int) - Whether similar request found and its index
        """
        if not previous_requests:
            return False, -1
            
        # Extract key content from request
        current_prompt = request.get('prompt', '')
        current_content = request.get('content', '')
        current_query = request.get('query', '')
        
        # Combine relevant fields for comparison
        current_text = f"{current_prompt} {current_query} {current_content[:500]}"
        
        # Compare with each previous request
        for i, prev_req in enumerate(previous_requests):
            prev_prompt = prev_req.get('prompt', '')
            prev_content = prev_req.get('content', '')
            prev_query = prev_req.get('query', '')
            
            prev_text = f"{prev_prompt} {prev_query} {prev_content[:500]}"
            
            similarity = calculate_similarity(current_text, prev_text)
            
            if similarity >= similarity_threshold:
                return True, i
                
        return False, -1
        
    def batch_requests(self, requests: List[Dict], 
                     similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> Tuple[List[Dict], Dict]:
        """
        Batches similar requests to reduce API calls and token usage.
        
        Args:
            requests: List of requests to potentially batch
            similarity_threshold: Threshold for considering requests similar
            
        Returns:
            (list, dict) - Batched requests and mapping to original requests
        """
        if not requests:
            return [], {}
            
        batched_requests = []
        request_mapping = {}  # Maps batched request index to list of original indices
        
        for i, request in enumerate(requests):
            # Check if similar to an existing batched request
            is_similar, similar_idx = self.detect_similar_request(
                request, batched_requests, similarity_threshold
            )
            
            if is_similar:
                # Add to mapping for existing batched request
                if similar_idx in request_mapping:
                    request_mapping[similar_idx].append(i)
                else:
                    request_mapping[similar_idx] = [i]
            else:
                # Add as new batched request
                batched_requests.append(request)
                request_mapping[len(batched_requests) - 1] = [i]
                
        return batched_requests, request_mapping
        
    def optimize_template(self, template: str, params: Dict) -> str:
        """
        Optimizes a template with parameters for token efficiency.
        
        Args:
            template: Template string
            params: Parameters to insert into template
            
        Returns:
            Optimized template
        """
        if not template:
            return ""
            
        # Check cache if enabled
        if self._use_cache:
            cache_key = generate_cache_key(
                self._model, 
                template, 
                params
            )
            cached_result = cache_get(cache_key)
            if cached_result:
                self.logger.debug("Using cached optimized template")
                return cached_result
                
        # Identify large text fields that might need optimization
        large_text_params = {}
        other_params = {}
        
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 500:
                large_text_params[key] = value
            else:
                other_params[key] = value
                
        # Calculate token budget for large text fields
        if large_text_params:
            # Calculate tokens in template without large fields
            template_with_placeholders = template
            for key in large_text_params:
                placeholder = "{" + key + "}"
                if placeholder in template_with_placeholders:
                    template_with_placeholders = template_with_placeholders.replace(
                        placeholder, f"__PLACEHOLDER_{key}__"
                    )
                    
            # Format with other params
            try:
                template_partial = template_with_placeholders.format(**other_params)
            except KeyError:
                # Not all parameters provided, use template as is
                template_partial = template_with_placeholders
                
            remaining_tokens = self._max_tokens - self.count_tokens(template_partial) - TOKEN_LIMIT_BUFFER
            
            # Distribute tokens proportionally among large text fields
            total_large_text_tokens = sum(
                self.count_tokens(text) for text in large_text_params.values()
            )
            
            optimized_large_text = {}
            
            if total_large_text_tokens > remaining_tokens:
                # Need to optimize large text fields
                for key, text in large_text_params.items():
                    text_tokens = self.count_tokens(text)
                    # Allocate tokens proportionally
                    allocated_tokens = int(remaining_tokens * (text_tokens / total_large_text_tokens))
                    if allocated_tokens < 50:  # Minimum sensible allocation
                        allocated_tokens = min(50, remaining_tokens // len(large_text_params))
                        
                    # Optimize this field to fit allocation
                    if text_tokens > allocated_tokens:
                        optimized_large_text[key] = truncate_text_to_token_limit(
                            text, allocated_tokens, DEFAULT_ENCODING
                        )
                    else:
                        optimized_large_text[key] = text
            else:
                # No optimization needed
                optimized_large_text = large_text_params
                
            # Combine optimized parameters
            optimized_params = {**other_params, **optimized_large_text}
        else:
            # No large text fields to optimize
            optimized_params = params
            
        # Format template with optimized parameters
        try:
            optimized_template = template.format(**optimized_params)
        except KeyError as e:
            self.logger.warning(f"Missing parameter in template: {str(e)}")
            # Replace missing parameters with placeholders
            for key in re.findall(r'\{(\w+)\}', template):
                if key not in optimized_params:
                    template = template.replace('{' + key + '}', f"[{key}]")
            optimized_template = template.format(**optimized_params)
            
        # Cache the result
        if self._use_cache:
            cache_set(cache_key, optimized_template, CACHE_TTL)
            
        return optimized_template
        
    def extract_key_sentences(self, text: str, max_sentences: int = 5, query: str = None) -> str:
        """
        Extracts key sentences from text based on importance heuristics.
        
        Args:
            text: Source text
            max_sentences: Maximum number of sentences to extract
            query: Optional query for relevance scoring
            
        Returns:
            Selected key sentences
        """
        if not text:
            return ""
            
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text
            
        if len(sentences) <= max_sentences:
            return text
            
        # Score sentences
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            # Base score: position-based importance
            position_score = 0
            if i == 0:  # First sentence
                position_score = 1.0
            elif i == len(sentences) - 1:  # Last sentence
                position_score = 0.8
            elif i < len(sentences) / 3:  # First third
                position_score = 0.6
            elif i < len(sentences) * 2 / 3:  # Middle third
                position_score = 0.4
            else:  # Last third
                position_score = 0.3
                
            # Length score: prefer medium-length sentences
            sentence_tokens = self.count_tokens(sentence)
            if sentence_tokens < 5:
                length_score = 0.3  # Too short
            elif sentence_tokens > 30:
                length_score = 0.5  # Too long
            else:
                length_score = 1.0  # Just right
                
            # Content score: presence of key terms
            content_score = 0.5
            important_terms = ["key", "important", "significant", "main", "critical", "crucial"]
            if any(term in sentence.lower() for term in important_terms):
                content_score = 1.0
                
            # Query relevance score
            relevance_score = 0.5
            if query:
                relevance_score = calculate_similarity(query, sentence)
                
            # Combine scores with appropriate weights
            total_score = (
                position_score * 0.3 +
                length_score * 0.1 +
                content_score * 0.2 +
                (relevance_score * 0.4 if query else 0)
            )
            
            scored_sentences.append((i, sentence, total_score))
            
        # Sort by score
        scored_sentences.sort(key=lambda x: x[2], reverse=True)
        
        # Take top N sentences
        top_sentences = scored_sentences[:max_sentences]
        
        # Sort by original position
        top_sentences.sort(key=lambda x: x[0])
        
        # Join selected sentences
        return " ".join(sentence for _, sentence, _ in top_sentences)
        
    def estimate_tokens_saved(self, original: str, optimized: str) -> Dict:
        """
        Estimates the token savings from optimization techniques.
        
        Args:
            original: Original text before optimization
            optimized: Optimized text after processing
            
        Returns:
            Dictionary with token usage statistics and savings
        """
        original_tokens = self.count_tokens(original)
        optimized_tokens = self.count_tokens(optimized)
        
        tokens_saved = original_tokens - optimized_tokens
        percentage_saved = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0
        
        return {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": tokens_saved,
            "percentage_saved": percentage_saved,
            "estimated_cost_saved": tokens_saved * 0.002 / 1000  # Assuming $0.002 per 1K tokens
        }
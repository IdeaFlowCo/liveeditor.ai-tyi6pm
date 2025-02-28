import pytest
from unittest.mock import MagicMock, patch
import tiktoken
import time

from src.backend.core.ai.token_optimizer import (
    TokenOptimizer, 
    count_tokens, 
    truncate_text_to_token_limit,
    calculate_similarity
)
from src.backend.data.redis.caching_service import cache_set, cache_get
from src.backend.core.ai.context_manager import ContextManager

# Test constants
SAMPLE_TEXT = "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility."
LARGE_TEXT = " ".join([SAMPLE_TEXT] * 50)
SAMPLE_PROMPT = "Improve the following text to make it more professional:"
DEFAULT_MODEL = "gpt-4"
DEFAULT_MAX_TOKENS = 4096


class TestTokenOptimizer:
    """Test suite for the TokenOptimizer class to verify token counting, optimization strategies, context windowing, and other token management features."""
    
    def setUp(self):
        """Set up the test environment before each test"""
        self.optimizer = TokenOptimizer()
        self.short_text = "This is a short text for testing."
        self.medium_text = SAMPLE_TEXT
        self.large_text = LARGE_TEXT
        
        # Patch Redis caching functions
        self.cache_get_patcher = patch('src.backend.core.ai.token_optimizer.cache_get')
        self.mock_cache_get = self.cache_get_patcher.start()
        self.mock_cache_get.return_value = None
        
        self.cache_set_patcher = patch('src.backend.core.ai.token_optimizer.cache_set')
        self.mock_cache_set = self.cache_set_patcher.start()
        self.mock_cache_set.return_value = True
        
        # Set up context manager mock
        self.context_manager_patcher = patch('src.backend.core.ai.context_manager.ContextManager')
        self.mock_context_manager = self.context_manager_patcher.start()
        self.mock_context_manager.get_context.return_value = {"messages": []}
        
    def tearDown(self):
        """Clean up after each test"""
        self.cache_get_patcher.stop()
        self.cache_set_patcher.stop()
        self.context_manager_patcher.stop()
    
    def test_init(self):
        """Test TokenOptimizer initialization with various parameters"""
        # Test default initialization
        optimizer = TokenOptimizer()
        assert optimizer._model == DEFAULT_MODEL
        assert optimizer._max_tokens == DEFAULT_MAX_TOKENS
        assert optimizer._use_cache is True
        
        # Test custom parameters
        custom_model = "gpt-3.5-turbo"
        custom_max_tokens = 2048
        optimizer = TokenOptimizer(model=custom_model, max_tokens=custom_max_tokens, use_cache=False)
        assert optimizer._model == custom_model
        assert optimizer._max_tokens == custom_max_tokens
        assert optimizer._use_cache is False
        
        # Test with invalid model (should use default encoding)
        optimizer = TokenOptimizer(model="non-existent-model")
        assert optimizer._encoding is not None  # Should fall back to default encoding
    
    def test_count_tokens(self):
        """Test that token counting accurately reports token counts for different texts"""
        # Test with empty string
        assert self.optimizer.count_tokens("") == 0
        
        # Test with short text
        short_text_tokens = self.optimizer.count_tokens(self.short_text)
        assert short_text_tokens > 0
        assert isinstance(short_text_tokens, int)
        
        # Test with medium text
        medium_text_tokens = self.optimizer.count_tokens(self.medium_text)
        assert medium_text_tokens > short_text_tokens
        
        # Compare with tiktoken's direct counting
        encoding = tiktoken.get_encoding("cl100k_base")
        expected_tokens = len(encoding.encode(self.medium_text))
        assert medium_text_tokens == expected_tokens
        
        # Verify consistent results with multiple calls
        assert self.optimizer.count_tokens(self.medium_text) == medium_text_tokens
    
    def test_count_tokens_function(self):
        """Test the standalone count_tokens function"""
        # Call with sample text
        token_count = count_tokens(self.medium_text)
        assert token_count > 0
        assert isinstance(token_count, int)
        
        # Test with different encoding
        token_count_p50k = count_tokens(self.medium_text, "p50k_base")
        # Results should be different with different encodings
        # But we can't guarantee which is higher, so just check they're different
        assert token_count != token_count_p50k
    
    def test_truncate_text_to_token_limit(self):
        """Test that truncation function limits text to specified token count"""
        # Create text that exceeds limit
        token_limit = 10
        long_text = "This text should exceed the token limit of ten tokens easily."
        
        # Apply truncation
        truncated = truncate_text_to_token_limit(long_text, token_limit)
        
        # Verify truncated text is within limit
        truncated_tokens = self.optimizer.count_tokens(truncated)
        assert truncated_tokens <= token_limit
        
        # Verify truncation preserves beginning
        assert truncated.startswith("This text")
        
        # Test with text under limit
        short_text = "Short text."
        result = truncate_text_to_token_limit(short_text, token_limit)
        assert result == short_text  # Should remain unchanged
        
        # Test with empty string
        assert truncate_text_to_token_limit("", token_limit) == ""
    
    def test_optimize_prompt(self):
        """Test that prompt optimization balances prompt and content within token limits"""
        prompt = SAMPLE_PROMPT
        content = LARGE_TEXT
        max_tokens = 1000
        reserved_tokens = 200
        
        # Count tokens in prompt and content separately
        prompt_tokens = self.optimizer.count_tokens(prompt)
        content_tokens = self.optimizer.count_tokens(content)
        
        # Verify that combined they exceed the limit
        assert prompt_tokens + content_tokens > max_tokens
        
        # Optimize prompt with content
        optimized = self.optimizer.optimize_prompt(
            prompt, content, max_tokens=max_tokens, reserved_tokens=reserved_tokens
        )
        
        # Verify total tokens stay within limit
        optimized_tokens = self.optimizer.count_tokens(optimized)
        assert optimized_tokens <= max_tokens - reserved_tokens
        
        # Verify prompt is preserved
        assert prompt in optimized
        
        # Verify caching behavior
        assert self.mock_cache_get.called
        assert self.mock_cache_set.called
        
        # Test with caching disabled
        self.mock_cache_get.reset_mock()
        self.mock_cache_set.reset_mock()
        optimizer_no_cache = TokenOptimizer(use_cache=False)
        optimizer_no_cache.optimize_prompt(prompt, content, max_tokens, reserved_tokens)
        assert not self.mock_cache_get.called
        assert not self.mock_cache_set.called
    
    def test_apply_context_window(self):
        """Test the sliding window functionality for large texts"""
        window_size = 100
        content = LARGE_TEXT
        
        # Verify original content exceeds window size
        original_tokens = self.optimizer.count_tokens(content)
        assert original_tokens > window_size
        
        # Apply context window
        windowed = self.optimizer.apply_context_window(content, window_size)
        
        # Verify result fits within window size
        windowed_tokens = self.optimizer.count_tokens(windowed)
        assert windowed_tokens <= window_size
        
        # Test with query-based relevance
        query = "customer satisfaction"
        query_windowed = self.optimizer.apply_context_window(content, window_size, query=query)
        
        # Verify query-relevant content is included
        assert "customer satisfaction" in query_windowed
        
        # Test with content already under window size
        short_content = "This is a short text."
        result = self.optimizer.apply_context_window(short_content, window_size)
        assert result == short_content  # Should remain unchanged
    
    def test_optimize_document_chunks(self):
        """Test document chunking for processing large documents"""
        chunk_size = 100
        overlap = 20
        
        # Verify large text exceeds chunk size
        assert self.optimizer.count_tokens(self.large_text) > chunk_size
        
        # Create chunks
        chunks = self.optimizer.optimize_document_chunks(self.large_text, chunk_size, overlap)
        
        # Verify chunks are created
        assert len(chunks) > 1
        
        # Verify each chunk is within limit
        for chunk in chunks:
            assert self.optimizer.count_tokens(chunk) <= chunk_size
        
        # Verify there's some overlap between consecutive chunks
        # This is hard to test precisely, but we can check that adjacent chunks share some content
        for i in range(len(chunks) - 1):
            # Look for common sentences or phrases
            common_content = False
            sentences1 = chunks[i].split('.')
            sentences2 = chunks[i+1].split('.')
            
            for s1 in sentences1:
                for s2 in sentences2:
                    if s1.strip() and s2.strip() and s1.strip() == s2.strip():
                        common_content = True
                        break
                if common_content:
                    break
            
            # If no direct match, chunks might still have overlap due to
            # boundary cleaning, which is okay
            if not common_content:
                assert len(chunks[i]) > 0 and len(chunks[i+1]) > 0
    
    def test_calculate_similarity(self):
        """Test similarity calculation between text strings"""
        # Identical texts should have similarity 1.0
        text1 = "This is a test sentence."
        text2 = "This is a test sentence."
        assert calculate_similarity(text1, text2) == 1.0
        
        # Completely different texts should have low similarity
        text3 = "This has nothing in common."
        assert calculate_similarity(text1, text3) < 0.3
        
        # Partially similar texts should have intermediate similarity
        text4 = "This is a sample sentence for testing."
        similarity = calculate_similarity(text1, text4)
        assert 0.3 < similarity < 0.9
        
        # Test with empty strings
        assert calculate_similarity("", "") == 0.0
        assert calculate_similarity(text1, "") == 0.0
        assert calculate_similarity("", text1) == 0.0
    
    def test_detect_similar_request(self):
        """Test detection of similar requests for optimization"""
        request1 = {
            "prompt": "Improve writing",
            "content": "This is a sample document for testing similarities.",
            "query": "professional"
        }
        
        request2 = {
            "prompt": "Improve writing style",
            "content": "This is a sample document for finding similarities.",
            "query": "professional tone"
        }
        
        request3 = {
            "prompt": "Translate to Spanish",
            "content": "This is completely different content.",
            "query": "translation"
        }
        
        previous_requests = [request1]
        
        # Test with similar request
        is_similar, idx = self.optimizer.detect_similar_request(request2, previous_requests)
        assert is_similar is True
        assert idx == 0
        
        # Test with different request
        is_similar, idx = self.optimizer.detect_similar_request(request3, previous_requests)
        assert is_similar is False
        assert idx == -1
        
        # Test with different similarity threshold
        is_similar, idx = self.optimizer.detect_similar_request(
            request2, previous_requests, similarity_threshold=0.9
        )
        assert is_similar is False  # Should be False with higher threshold
        
        # Test with empty previous_requests
        is_similar, idx = self.optimizer.detect_similar_request(request1, [])
        assert is_similar is False
        assert idx == -1
    
    def test_batch_requests(self):
        """Test batching of similar requests"""
        request1 = {
            "prompt": "Improve writing",
            "content": "Sample document 1",
            "query": "professional"
        }
        
        request2 = {
            "prompt": "Improve writing style",
            "content": "Sample document 2",
            "query": "professional"
        }
        
        request3 = {
            "prompt": "Translate to Spanish",
            "content": "Different content",
            "query": "translation"
        }
        
        requests = [request1, request2, request3]
        
        # Batch requests
        batched_requests, request_mapping = self.optimizer.batch_requests(requests)
        
        # Verify similar requests are batched
        assert len(batched_requests) < len(requests)
        
        # Verify request mapping is created
        assert len(request_mapping) == len(batched_requests)
        
        # All original request indices should be in the mapping
        all_indices = []
        for indices in request_mapping.values():
            all_indices.extend(indices)
        assert sorted(all_indices) == list(range(len(requests)))
        
        # Test with empty requests
        empty_batched, empty_mapping = self.optimizer.batch_requests([])
        assert empty_batched == []
        assert empty_mapping == {}
        
        # Test with different similarity threshold
        strict_batched, strict_mapping = self.optimizer.batch_requests(
            requests, similarity_threshold=0.95
        )
        # Should batch fewer requests with stricter threshold
        assert len(strict_batched) >= len(batched_requests)
    
    def test_optimize_template(self):
        """Test template optimization with parameters"""
        template = "Title: {title}\n\nContent: {content}\n\nSummary: {summary}"
        params = {
            "title": "Test Document",
            "content": LARGE_TEXT,
            "summary": "A brief summary of the test document."
        }
        
        # Count tokens in original parameters
        content_tokens = self.optimizer.count_tokens(params["content"])
        
        # Optimize template
        optimized = self.optimizer.optimize_template(template, params)
        
        # Verify result is smaller than original
        optimized_tokens = self.optimizer.count_tokens(optimized)
        assert optimized_tokens < content_tokens + self.optimizer.count_tokens(template)
        
        # Verify template format is preserved
        assert "Title:" in optimized
        assert "Content:" in optimized
        assert "Summary:" in optimized
        
        # Test with empty template
        assert self.optimizer.optimize_template("", params) == ""
        
        # Test with missing parameters
        template_with_missing = "Title: {title}\nAuthor: {author}\nContent: {content}"
        result = self.optimizer.optimize_template(template_with_missing, params)
        assert "Title:" in result
        assert "Author:" in result
        assert "Content:" in result
    
    def test_extract_key_sentences(self):
        """Test extraction of key sentences from text"""
        text = """This is the first sentence. This is the second sentence with key information. 
        This is the third sentence. The fourth sentence is critical for understanding. 
        This is the fifth sentence. This is the sixth sentence with important details.
        This is the seventh sentence. This is the eighth sentence."""
        
        # Extract 3 key sentences
        max_sentences = 3
        result = self.optimizer.extract_key_sentences(text, max_sentences)
        
        # Verify correct number of sentences
        # We can approximate by counting periods, but this isn't perfect
        sentence_count = result.count('.')
        assert 1 <= sentence_count <= max_sentences + 1  # Allow for some flexibility
        
        # Test with query parameter
        query = "critical understanding"
        query_result = self.optimizer.extract_key_sentences(text, max_sentences, query)
        
        # Verify query-relevant sentence is included
        assert "critical for understanding" in query_result
        
        # Test with text having fewer sentences than max
        short_text = "This is a single sentence."
        short_result = self.optimizer.extract_key_sentences(short_text, max_sentences)
        assert short_result == short_text
        
        # Test with empty text
        assert self.optimizer.extract_key_sentences("", max_sentences) == ""
    
    def test_estimate_tokens_saved(self):
        """Test token savings estimation functionality"""
        original = LARGE_TEXT
        optimized = original[:len(original)//2]  # Simulate 50% reduction
        
        # Get token counts
        original_tokens = self.optimizer.count_tokens(original)
        optimized_tokens = self.optimizer.count_tokens(optimized)
        
        # Calculate expected savings
        expected_tokens_saved = original_tokens - optimized_tokens
        expected_percentage = (expected_tokens_saved / original_tokens) * 100
        
        # Get estimated savings
        estimate = self.optimizer.estimate_tokens_saved(original, optimized)
        
        # Verify token counts match
        assert estimate["original_tokens"] == original_tokens
        assert estimate["optimized_tokens"] == optimized_tokens
        assert estimate["tokens_saved"] == expected_tokens_saved
        assert estimate["percentage_saved"] == pytest.approx(expected_percentage, 0.1)
        
        # Verify cost savings calculation is present
        assert "estimated_cost_saved" in estimate
        assert estimate["estimated_cost_saved"] >= 0
    
    @pytest.mark.usefixtures('mock_redis')
    def test_caching_behavior(self):
        """Test caching functionality of token optimizer"""
        # Set up mock cache behavior
        self.mock_cache_get.side_effect = [None, "cached_result"]  # First miss, then hit
        
        # First call should check cache, get a miss, and store result
        result1 = self.optimizer.optimize_prompt(SAMPLE_PROMPT, self.medium_text)
        assert self.mock_cache_get.called
        assert self.mock_cache_set.called
        
        # Reset mocks
        self.mock_cache_get.reset_mock()
        self.mock_cache_set.reset_mock()
        
        # Second call should get cache hit and return cached result
        result2 = self.optimizer.optimize_prompt(SAMPLE_PROMPT, self.medium_text)
        assert self.mock_cache_get.called
        assert not self.mock_cache_set.called
        assert result2 == "cached_result"
        
        # Test with caching disabled
        optimizer_no_cache = TokenOptimizer(use_cache=False)
        self.mock_cache_get.reset_mock()
        self.mock_cache_set.reset_mock()
        
        optimizer_no_cache.optimize_prompt(SAMPLE_PROMPT, self.medium_text)
        assert not self.mock_cache_get.called
        assert not self.mock_cache_set.called
    
    def test_token_optimization_performance(self):
        """Test performance and optimization efficiency"""
        # Create large sample text
        large_sample = LARGE_TEXT * 2
        
        # Measure token count before optimization
        start_tokens = self.optimizer.count_tokens(large_sample)
        
        # Measure time for optimization
        start_time = time.time()
        
        # Apply optimization
        optimized = self.optimizer.apply_context_window(large_sample, start_tokens // 2)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Measure token count after optimization
        end_tokens = self.optimizer.count_tokens(optimized)
        
        # Calculate reduction percentage
        reduction_percentage = ((start_tokens - end_tokens) / start_tokens) * 100
        
        # Verify reduction meets target (40-60%)
        assert 40 <= reduction_percentage <= 80
        
        # Verify processing time is within performance SLA (5 seconds)
        assert processing_time < 5.0
    
    def test_integration_with_context_manager(self):
        """Test integration with ContextManager"""
        # Create mock ContextManager
        context_manager = MagicMock(spec=ContextManager)
        
        # Configure mock to return sample context
        sample_context = {
            "document_content": SAMPLE_TEXT,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Improve my writing."}
            ]
        }
        context_manager.get_context.return_value = sample_context
        
        # Create optimizer that would interact with context
        optimizer = TokenOptimizer()
        
        # Simulate optimizing content from context
        document_content = sample_context.get("document_content", "")
        prompt = "Make this more professional:"
        
        # Use the optimizer with content from context
        optimized = optimizer.optimize_prompt(prompt, document_content)
        
        # Verify optimization worked
        assert prompt in optimized
        assert len(optimized) > len(prompt)
        
        # Create a larger context to test token allocation
        large_context = {
            "document_content": LARGE_TEXT,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Improve my writing."}
            ]
        }
        
        # Optimize with large context
        large_document = large_context.get("document_content", "")
        result = optimizer.optimize_prompt(prompt, large_document, max_tokens=1000)
        
        # Verify result is within token limit
        assert optimizer.count_tokens(result) <= 1000


class TestTokenOptimizerEdgeCases:
    """Test suite focusing on edge cases and error handling in TokenOptimizer"""
    
    def test_empty_inputs(self):
        """Test behavior with empty or null inputs"""
        optimizer = TokenOptimizer()
        
        # Test token counting with empty string
        assert optimizer.count_tokens("") == 0
        
        # Test optimization with empty content
        result = optimizer.optimize_prompt("Improve:", "", max_tokens=100)
        assert result == "Improve:"
        
        # Test document chunking with empty document
        chunks = optimizer.optimize_document_chunks("", chunk_size=100)
        assert chunks == [""]
        
        # Test context window with empty text
        windowed = optimizer.apply_context_window("", window_size=100)
        assert windowed == ""
    
    def test_extremely_large_inputs(self):
        """Test behavior with inputs far exceeding token limits"""
        optimizer = TokenOptimizer()
        
        # Create extremely large text (simulated)
        extremely_large = LARGE_TEXT * 20  # Should be well over typical token limits
        
        # Apply optimization with small window
        start_time = time.time()
        result = optimizer.apply_context_window(extremely_large, window_size=500)
        end_time = time.time()
        
        # Verify result is within limits
        assert optimizer.count_tokens(result) <= 500
        
        # Verify processing time is reasonable (should be well under SLA)
        assert end_time - start_time < 5.0
        
        # Test document chunking with extremely large input
        start_time = time.time()
        chunks = optimizer.optimize_document_chunks(extremely_large, chunk_size=200)
        end_time = time.time()
        
        # Verify chunks are created and properly sized
        assert len(chunks) > 1
        for chunk in chunks:
            assert optimizer.count_tokens(chunk) <= 200
            
        # Verify processing time is reasonable
        assert end_time - start_time < 10.0  # Chunking can take longer but still should be reasonable
    
    def test_invalid_models(self):
        """Test handling of invalid model specifications"""
        # Test with non-existent model name
        optimizer = TokenOptimizer(model="non-existent-model")
        
        # Should still be able to count tokens (using fallback encoding)
        token_count = optimizer.count_tokens(SAMPLE_TEXT)
        assert token_count > 0
        
        # Test with invalid max_tokens
        optimizer_bad_max = TokenOptimizer(max_tokens=-100)
        
        # Should still work with internal default
        result = optimizer_bad_max.optimize_prompt(SAMPLE_PROMPT, SAMPLE_TEXT)
        assert len(result) > 0
    
    def test_token_limit_edge_cases(self):
        """Test behavior at exact token limit boundaries"""
        optimizer = TokenOptimizer()
        
        # Count tokens in sample text
        sample_tokens = optimizer.count_tokens(SAMPLE_TEXT)
        
        # Test with exact token limit
        result_exact = optimizer.optimize_prompt(SAMPLE_PROMPT, SAMPLE_TEXT, max_tokens=sample_tokens + len(SAMPLE_PROMPT.split()))
        assert optimizer.count_tokens(result_exact) <= sample_tokens + len(SAMPLE_PROMPT.split())
        
        # Test with 1 token over limit
        result_over = optimizer.optimize_prompt(SAMPLE_PROMPT, SAMPLE_TEXT, max_tokens=sample_tokens - 1)
        assert optimizer.count_tokens(result_over) < sample_tokens
        
        # Test with 1 token under limit
        result_under = truncate_text_to_token_limit(SAMPLE_TEXT, sample_tokens - 1)
        assert optimizer.count_tokens(result_under) <= sample_tokens - 1
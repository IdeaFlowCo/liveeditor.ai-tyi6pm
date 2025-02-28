import unittest
import pytest
from unittest import mock

from src.backend.core.documents.diff_service import (
    DiffService, 
    generate_diff, 
    calculate_diff_statistics,
    UnsupportedAlgorithmError,
    UnsupportedFormatError,
    SUPPORTED_ALGORITHMS,
    SUPPORTED_FORMATS
)

class TestDiffService(unittest.TestCase):
    """Test suite for the DiffService class which analyzes text differences for track changes functionality"""
    
    def setUp(self):
        """Set up the test environment before each test case"""
        self.diff_service = DiffService()
        
        # Prepare common test text samples
        self.original_text = "The quick brown fox jumps over the lazy dog."
        self.modified_text_additions = "The quick brown fox jumps over the very lazy dog."
        self.modified_text_deletions = "The quick fox jumps over the lazy dog."
        self.modified_text_modifications = "The fast brown fox jumps over the lazy dog."
    
    def test_initialization(self):
        """Test that DiffService initializes correctly with default and custom algorithms"""
        # Default algorithm
        default_service = DiffService()
        self.assertEqual(default_service._algorithm, "diff_match_patch", "Default algorithm should be diff_match_patch")
        
        # Custom algorithm
        custom_service = DiffService(algorithm="word_level")
        self.assertEqual(custom_service._algorithm, "word_level", "Custom algorithm not properly set")
        
        # Invalid algorithm
        with self.assertRaises(UnsupportedAlgorithmError):
            DiffService(algorithm="invalid_algorithm")
    
    def test_get_supported_algorithms(self):
        """Test that the service returns the correct list of supported algorithms"""
        algorithms = self.diff_service.get_supported_algorithms()
        self.assertEqual(algorithms, SUPPORTED_ALGORITHMS, "Supported algorithms don't match expected list")
        self.assertIn("diff_match_patch", algorithms, "Missing diff_match_patch algorithm")
        self.assertIn("unified", algorithms, "Missing unified algorithm")
        self.assertIn("word_level", algorithms, "Missing word_level algorithm")
    
    def test_get_supported_formats(self):
        """Test that the service returns the correct list of supported output formats"""
        formats = self.diff_service.get_supported_formats()
        self.assertEqual(formats, SUPPORTED_FORMATS, "Supported formats don't match expected list")
        self.assertIn("track_changes", formats, "Missing track_changes format")
        self.assertIn("inline", formats, "Missing inline format")
        self.assertIn("unified", formats, "Missing unified format")
    
    def test_compare_identical_texts(self):
        """Test that comparing identical texts returns no differences"""
        identical_text = "This is a sample text."
        diff_result = self.diff_service.compare_texts(identical_text, identical_text)
        
        # Verify operations
        operations = diff_result.get("operations", [])
        self.assertEqual(len(operations), 1, "Should have exactly one operation for identical texts")
        self.assertEqual(operations[0]["operation"], "equal", "Operation should be 'equal' for identical texts")
        self.assertEqual(operations[0]["text"], identical_text, "Text content in equal operation doesn't match input")
        
        # Verify statistics
        stats = diff_result.get("statistics", {})
        self.assertEqual(stats.get("percent_unchanged", 0), 100, "Identical texts should show 100% unchanged")
        self.assertEqual(stats.get("chars_deleted", 0), 0, "Identical texts should have 0 deleted chars")
        self.assertEqual(stats.get("chars_inserted", 0), 0, "Identical texts should have 0 inserted chars")
    
    def test_compare_texts_with_additions(self):
        """Test that comparing texts with added content correctly identifies additions"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_additions
        )
        
        # Verify operations
        operations = diff_result.get("operations", [])
        
        # Find insert operations
        inserts = [op for op in operations if op["operation"] == "insert"]
        self.assertTrue(len(inserts) > 0, "Should detect inserted content")
        
        # Verify insert content matches what was added
        insert_text = ''.join(op["text"] for op in inserts)
        self.assertIn("very", insert_text, "Should detect the word 'very' as inserted")
        
        # Verify statistics
        stats = diff_result.get("statistics", {})
        self.assertTrue(stats.get("chars_inserted", 0) > 0, "Statistics should show inserted characters")
        self.assertEqual(stats.get("chars_deleted", 0), 0, "No characters should be deleted")
    
    def test_compare_texts_with_deletions(self):
        """Test that comparing texts with deleted content correctly identifies deletions"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_deletions
        )
        
        # Verify operations
        operations = diff_result.get("operations", [])
        
        # Find delete operations
        deletes = [op for op in operations if op["operation"] == "delete"]
        self.assertTrue(len(deletes) > 0, "Should detect deleted content")
        
        # Verify delete content matches what was removed
        delete_text = ''.join(op["text"] for op in deletes)
        self.assertIn("brown", delete_text, "Should detect the word 'brown' as deleted")
        
        # Verify statistics
        stats = diff_result.get("statistics", {})
        self.assertEqual(stats.get("chars_inserted", 0), 0, "No characters should be inserted")
        self.assertTrue(stats.get("chars_deleted", 0) > 0, "Statistics should show deleted characters")
    
    def test_compare_texts_with_modifications(self):
        """Test that comparing texts with replaced content correctly identifies modifications"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_modifications
        )
        
        # Verify operations
        operations = diff_result.get("operations", [])
        
        # Find relevant operations
        deletes = [op for op in operations if op["operation"] == "delete"]
        inserts = [op for op in operations if op["operation"] == "insert"]
        
        self.assertTrue(len(deletes) > 0, "Should detect deleted content in modification")
        self.assertTrue(len(inserts) > 0, "Should detect inserted content in modification")
        
        # Verify content matches the modification
        delete_text = ''.join(op["text"] for op in deletes)
        insert_text = ''.join(op["text"] for op in inserts)
        
        self.assertIn("quick", delete_text, "Should detect 'quick' as deleted")
        self.assertIn("fast", insert_text, "Should detect 'fast' as inserted")
        
        # Verify statistics
        stats = diff_result.get("statistics", {})
        self.assertTrue(stats.get("chars_inserted", 0) > 0, "Statistics should show inserted characters")
        self.assertTrue(stats.get("chars_deleted", 0) > 0, "Statistics should show deleted characters")
    
    def test_diff_match_patch_algorithm(self):
        """Test the diff-match-patch specific algorithm implementation"""
        original = "Hello world"
        modified = "Hello beautiful world"
        
        diff_result = self.diff_service.compare_texts(
            original, 
            modified,
            algorithm="diff_match_patch"
        )
        
        operations = diff_result.get("operations", [])
        
        # Verify correct character-level changes
        inserts = [op for op in operations if op["operation"] == "insert"]
        insert_text = ''.join(op["text"] for op in inserts)
        
        self.assertIn("beautiful ", insert_text, "Should detect 'beautiful ' as inserted")
        
        # Verify position calculations
        for op in operations:
            if op["operation"] == "insert":
                # "beautiful " should be inserted after "Hello "
                self.assertEqual(op["position"], 6, "Insert position should be after 'Hello '")
                break
    
    def test_unified_diff_algorithm(self):
        """Test the unified diff algorithm implementation for line-based comparison"""
        original = "Line one\nLine two\nLine three"
        modified = "Line one\nModified line\nLine three"
        
        diff_result = self.diff_service.compare_texts(
            original, 
            modified,
            algorithm="unified"
        )
        
        operations = diff_result.get("operations", [])
        
        # Verify line-based changes
        deletes = [op for op in operations if op["operation"] == "delete"]
        inserts = [op for op in operations if op["operation"] == "insert"]
        
        delete_text = ''.join(op["text"] for op in deletes)
        insert_text = ''.join(op["text"] for op in inserts)
        
        self.assertIn("Line two", delete_text, "Should detect 'Line two' as deleted")
        self.assertIn("Modified line", insert_text, "Should detect 'Modified line' as inserted")
        
        # Verify line numbers
        for op in operations:
            if op["operation"] == "delete" and "Line two" in op["text"]:
                self.assertEqual(op["line"], 1, "Line two should be at index 1 (0-indexed)")
                break
    
    def test_word_level_diff_algorithm(self):
        """Test the word-level diff algorithm implementation"""
        original = "The quick brown fox jumps"
        modified = "The fast brown fox leaps"
        
        diff_result = self.diff_service.compare_texts(
            original, 
            modified,
            algorithm="word_level"
        )
        
        operations = diff_result.get("operations", [])
        
        # Verify word-based changes
        deletes = [op for op in operations if op["operation"] == "delete"]
        inserts = [op for op in operations if op["operation"] == "insert"]
        
        delete_words = ''.join(op["text"] for op in deletes)
        insert_words = ''.join(op["text"] for op in inserts)
        
        self.assertIn("quick", delete_words, "Should detect 'quick' as deleted")
        self.assertIn("jumps", delete_words, "Should detect 'jumps' as deleted")
        self.assertIn("fast", insert_words, "Should detect 'fast' as inserted")
        self.assertIn("leaps", insert_words, "Should detect 'leaps' as inserted")
        
        # Verify word boundaries are maintained
        for op in operations:
            if op["operation"] == "delete" and "quick" in op["text"]:
                self.assertEqual(op["text"].strip(), "quick", "Should maintain word boundaries for 'quick'")
            if op["operation"] == "insert" and "fast" in op["text"]:
                self.assertEqual(op["text"].strip(), "fast", "Should maintain word boundaries for 'fast'")
    
    def test_track_changes_format(self):
        """Test that differences are correctly formatted for track changes display"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_modifications
        )
        
        formatted = self.diff_service.format_for_display(
            diff_result, 
            "track_changes"
        )
        
        # Verify format
        self.assertEqual(formatted["format"], "track_changes", "Format should be track_changes")
        
        # Verify changes structure
        changes = formatted.get("changes", [])
        self.assertTrue(len(changes) > 0, "Should contain changes")
        
        for change in changes:
            # Verify each change has required fields
            self.assertIn("id", change, "Each change should have an ID")
            self.assertIn("type", change, "Each change should have a type")
            self.assertIn("formatted_text", change, "Each change should have formatted text")
            
            # Verify correct formatting
            if change["type"] == "deletion":
                self.assertIn("[-", change["formatted_text"], "Deletion should have [- prefix")
                self.assertIn("-]", change["formatted_text"], "Deletion should have -] suffix")
            elif change["type"] == "addition":
                self.assertIn("{+", change["formatted_text"], "Addition should have {+ prefix")
                self.assertIn("+}", change["formatted_text"], "Addition should have +} suffix")
            
            # Verify position data
            self.assertIn("position", change, "Each change should have position data")
    
    def test_inline_format(self):
        """Test that differences are correctly formatted for inline display"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_modifications
        )
        
        formatted = self.diff_service.format_for_display(
            diff_result, 
            "inline"
        )
        
        # Verify format
        self.assertEqual(formatted["format"], "inline", "Format should be inline")
        
        # Verify text contains markup
        inline_text = formatted.get("text", "")
        self.assertIn("[-quick-]", inline_text, "Should contain deletion markup for 'quick'")
        self.assertIn("{+fast+}", inline_text, "Should contain addition markup for 'fast'")
    
    def test_unified_format(self):
        """Test that differences are correctly formatted as unified diff"""
        original = "Line one\nLine two\nLine three"
        modified = "Line one\nModified line\nLine three"
        
        diff_result = self.diff_service.compare_texts(
            original, 
            modified
        )
        
        formatted = self.diff_service.format_for_display(
            diff_result, 
            "unified"
        )
        
        # Verify format
        self.assertEqual(formatted["format"], "unified", "Format should be unified")
        
        # Verify unified diff syntax
        unified_text = formatted.get("text", "")
        self.assertIn("-Line two", unified_text, "Should contain - prefix for deleted line")
        self.assertIn("+Modified line", unified_text, "Should contain + prefix for added line")
    
    def test_invalid_format_error(self):
        """Test that requesting an invalid format raises UnsupportedFormatError"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_additions
        )
        
        with self.assertRaises(UnsupportedFormatError):
            self.diff_service.format_for_display(diff_result, "invalid_format")
    
    def test_create_suggestion_from_diff(self):
        """Test creation of structured suggestions from diff results"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_modifications
        )
        
        suggestions = self.diff_service.create_suggestion_from_diff(diff_result)
        
        # Verify suggestions structure
        self.assertTrue(len(suggestions) > 0, "Should generate suggestions")
        
        for suggestion in suggestions:
            # Verify required fields
            self.assertIn("id", suggestion, "Each suggestion should have an ID")
            self.assertIn("position", suggestion, "Each suggestion should have a position")
            self.assertIn("original_text", suggestion, "Each suggestion should have original text")
            self.assertIn("suggested_text", suggestion, "Each suggestion should have suggested text")
            
            # Verify content
            if "quick" in suggestion["original_text"]:
                self.assertIn("fast", suggestion["suggested_text"], 
                             "Suggestion for 'quick' should contain 'fast'")
    
    def test_apply_selected_changes(self):
        """Test applying selected changes from a diff result"""
        # Create a text with multiple changes
        original = "The quick brown fox jumps over the lazy dog."
        modified = "The fast brown fox leaps over the sleepy dog."
        
        # Generate diff
        diff_result = self.diff_service.compare_texts(original, modified)
        
        # Format as track changes to get change IDs
        formatted = self.diff_service.format_for_display(diff_result, "track_changes")
        
        # Get change IDs
        changes = formatted.get("changes", [])
        change_ids = [change["id"] for change in changes]
        
        # Apply only the first change
        result = self.diff_service.apply_selected_changes(
            original, 
            formatted, 
            [change_ids[0]]
        )
        
        # Verify only first change was applied
        if "quick" in changes[0].get("original_text", ""):
            self.assertIn("fast", result, "Should apply change from 'quick' to 'fast'")
            self.assertNotIn("leaps", result, "Should not apply change from 'jumps' to 'leaps'")
        elif "jumps" in changes[0].get("original_text", ""):
            self.assertIn("leaps", result, "Should apply change from 'jumps' to 'leaps'")
            self.assertNotIn("fast", result, "Should not apply change from 'quick' to 'fast'")
    
    def test_empty_text_handling(self):
        """Test handling of empty strings in diff operations"""
        # Empty vs non-empty
        diff_result = self.diff_service.compare_texts("", "Some text")
        operations = diff_result.get("operations", [])
        
        # Should show entire text as an insertion
        self.assertEqual(len(operations), 1, "Should have one operation for empty to non-empty comparison")
        self.assertEqual(operations[0]["operation"], "insert", "Operation should be 'insert'")
        self.assertEqual(operations[0]["text"], "Some text", "Inserted text should match input")
        
        # Empty vs empty
        diff_result = self.diff_service.compare_texts("", "")
        operations = diff_result.get("operations", [])
        
        # Should have no operations or one equal operation with empty text
        if operations:
            self.assertEqual(len(operations), 1, "Should have at most one operation for empty-to-empty comparison")
            self.assertEqual(operations[0]["operation"], "equal", "Operation should be 'equal'")
            self.assertEqual(operations[0]["text"], "", "Equal text should be empty")
        else:
            self.assertEqual(len(operations), 0, "May have zero operations for empty-to-empty comparison")
        
        # Test formatting empty diff
        formatted = self.diff_service.format_for_display(diff_result, "track_changes")
        self.assertEqual(formatted["changes"], [], "Should have no changes for empty diff")
    
    def test_calculate_diff_statistics(self):
        """Test calculation of statistics for text differences"""
        diff_result = self.diff_service.compare_texts(
            self.original_text, 
            self.modified_text_modifications
        )
        
        stats = diff_result.get("statistics", {})
        
        # Verify statistics structure
        self.assertIn("total_chars_original", stats, "Stats should include total_chars_original")
        self.assertIn("total_chars_modified", stats, "Stats should include total_chars_modified")
        self.assertIn("chars_deleted", stats, "Stats should include chars_deleted")
        self.assertIn("chars_inserted", stats, "Stats should include chars_inserted")
        self.assertIn("chars_unchanged", stats, "Stats should include chars_unchanged")
        self.assertIn("percent_deleted", stats, "Stats should include percent_deleted")
        self.assertIn("percent_inserted", stats, "Stats should include percent_inserted")
        self.assertIn("percent_unchanged", stats, "Stats should include percent_unchanged")
        self.assertIn("change_blocks", stats, "Stats should include change_blocks")
        
        # Verify calculations
        self.assertEqual(stats["total_chars_original"], len(self.original_text), 
                        "total_chars_original should match original text length")
        self.assertEqual(stats["total_chars_modified"], len(self.modified_text_modifications), 
                        "total_chars_modified should match modified text length")
        
        # Verify "quick" was replaced with "fast"
        self.assertEqual(stats["chars_deleted"], len("quick"), 
                        "chars_deleted should match length of deleted word 'quick'")
        self.assertEqual(stats["chars_inserted"], len("fast"), 
                        "chars_inserted should match length of inserted word 'fast'")
    
    def test_standalone_generate_diff(self):
        """Test the standalone generate_diff function"""
        # Basic functionality
        diff_result = generate_diff(
            self.original_text, 
            self.modified_text_modifications
        )
        
        # Verify result structure matches service method
        self.assertIn("algorithm", diff_result, "Result should include algorithm")
        self.assertIn("operations", diff_result, "Result should include operations")
        self.assertIn("metadata", diff_result, "Result should include metadata")
        self.assertIn("statistics", diff_result, "Result should include statistics")
        
        # Test with different algorithm
        diff_result = generate_diff(
            self.original_text, 
            self.modified_text_modifications,
            algorithm="word_level"
        )
        
        self.assertEqual(diff_result["algorithm"], "word_level", "Algorithm should be word_level")
    
    def test_custom_options(self):
        """Test that custom options are correctly applied to diff operations"""
        # Case sensitivity test
        options = {"case_sensitive": False}
        
        original = "Text with UPPER case words"
        modified = "Text with upper CASE words"
        
        # With case sensitivity (default)
        diff_result1 = self.diff_service.compare_texts(original, modified)
        
        # Without case sensitivity
        diff_result2 = self.diff_service.compare_texts(
            original, 
            modified, 
            options=options
        )
        
        # Case sensitive comparison should detect differences
        stats1 = diff_result1.get("statistics", {})
        self.assertTrue(stats1.get("chars_deleted", 0) > 0, 
                       "Case-sensitive comparison should detect changes")
        self.assertTrue(stats1.get("chars_inserted", 0) > 0, 
                       "Case-sensitive comparison should detect changes")
        
        # Case insensitive should not (or detect fewer changes)
        stats2 = diff_result2.get("statistics", {})
        self.assertTrue(stats2.get("chars_deleted", 0) < stats1.get("chars_deleted", 0), 
                       "Case-insensitive should detect fewer changes than case-sensitive")
        
        # Test format options
        format_options = {"include_positions": False}
        
        formatted = self.diff_service.format_for_display(
            diff_result1, 
            "track_changes", 
            format_options
        )
        
        # Verify positions are not included
        for change in formatted.get("changes", []):
            self.assertNotIn("position", change, 
                            "Position should not be included when include_positions=False")
    
    def test_large_text_performance(self):
        """Test performance with large text inputs"""
        # Create large text samples
        large_original = self.original_text * 500  # ~20000 characters
        large_modified = large_original.replace("quick", "fast", 100)
        
        # Record execution time
        import time
        start_time = time.time()
        
        diff_result = self.diff_service.compare_texts(large_original, large_modified)
        
        execution_time = time.time() - start_time
        
        # Verify execution completes within reasonable time (adjust as needed)
        self.assertLess(execution_time, 2.0, "Large text diff should complete in under 2 seconds")
        
        # Verify result is correct
        operations = diff_result.get("operations", [])
        self.assertTrue(len(operations) > 0, "Should generate operations for large text")
        
        # Verify memory usage (basic check)
        import sys
        result_size = sys.getsizeof(diff_result)
        self.assertLess(result_size, 10 * 1024 * 1024, "Result size should be under 10MB")
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in text differences"""
        original = "Text with    spaces   and\ttabs\nand newlines"
        modified = "Text with spaces and tabs\nand newlines"
        
        # With default whitespace sensitivity
        diff_result1 = self.diff_service.compare_texts(original, modified)
        
        # With whitespace insensitivity
        diff_result2 = self.diff_service.compare_texts(
            original, 
            modified, 
            options={"ignore_whitespace": True}
        )
        
        # Default should detect whitespace differences
        stats1 = diff_result1.get("statistics", {})
        self.assertTrue(stats1.get("chars_deleted", 0) > 0, 
                       "Default should detect whitespace differences")
        
        # Whitespace insensitive should detect fewer or no changes
        stats2 = diff_result2.get("statistics", {})
        self.assertTrue(stats2.get("chars_deleted", 0) < stats1.get("chars_deleted", 0), 
                       "Whitespace-insensitive should detect fewer changes")
    
    def test_special_characters_handling(self):
        """Test handling of special characters and Unicode"""
        original = "Text with emoji 😊 and non-English 汉字 characters"
        modified = "Text with emoji 😍 and non-English 漢字 characters"
        
        diff_result = self.diff_service.compare_texts(original, modified)
        
        # Verify special characters are correctly handled
        operations = diff_result.get("operations", [])
        
        deletes = [op for op in operations if op["operation"] == "delete"]
        inserts = [op for op in operations if op["operation"] == "insert"]
        
        delete_text = ''.join(op["text"] for op in deletes)
        insert_text = ''.join(op["text"] for op in inserts)
        
        self.assertIn("😊", delete_text, "Should detect emoji 😊 as deleted")
        self.assertIn("😍", insert_text, "Should detect emoji 😍 as inserted")
        self.assertIn("汉字", delete_text, "Should detect Chinese characters 汉字 as deleted")
        self.assertIn("漢字", insert_text, "Should detect Chinese characters 漢字 as inserted")
        
        # Verify formatting works with special characters
        formatted = self.diff_service.format_for_display(diff_result, "track_changes")
        
        for change in formatted.get("changes", []):
            if "😊" in change.get("original_text", ""):
                self.assertIn("😍", change.get("new_text", ""), 
                             "Should show emoji change from 😊 to 😍")
            if "汉字" in change.get("original_text", ""):
                self.assertIn("漢字", change.get("new_text", ""), 
                             "Should show Chinese character change from 汉字 to 漢字")
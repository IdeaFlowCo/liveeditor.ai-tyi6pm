"""
Core service that implements text differencing algorithms to power the track changes functionality,
enabling comparison between original document content and AI-suggested improvements with multiple
output formats and visualization options.
"""

import difflib  # standard library
import json  # standard library
import re  # standard library
import typing  # standard library
import uuid  # standard library
from diff_match_patch import diff_match_patch  # diff-match-patch ~=1.0.5

from ..utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Supported differencing algorithms
SUPPORTED_ALGORITHMS = ["diff_match_patch", "unified", "word_level"]

# Supported output formats
SUPPORTED_FORMATS = ["track_changes", "inline", "unified"]

# Default algorithm to use if none specified
DEFAULT_ALGORITHM = "diff_match_patch"

# Marker definitions for track changes formatting
TRACK_CHANGES_MARKERS = {
    "deletion_prefix": "[-",
    "deletion_suffix": "-]",
    "addition_prefix": "{+",
    "addition_suffix": "+}"
}


class DiffServiceError(Exception):
    """Base exception class for diff service errors"""
    
    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize the diff service error
        
        Args:
            message: Error message
            original_error: Original exception if this is a wrapper
        """
        super().__init__(message)
        self.original_error = original_error


class UnsupportedAlgorithmError(DiffServiceError):
    """Exception raised when an unsupported diff algorithm is requested"""
    
    def __init__(self, algorithm: str, message: str = None):
        """
        Initialize the unsupported algorithm error
        
        Args:
            algorithm: The unsupported algorithm name
            message: Custom error message (optional)
        """
        if message is None:
            message = f"Unsupported diff algorithm: {algorithm}. Supported algorithms are: {', '.join(SUPPORTED_ALGORITHMS)}"
        super().__init__(message)
        self.algorithm = algorithm


class UnsupportedFormatError(DiffServiceError):
    """Exception raised when an unsupported format is requested"""
    
    def __init__(self, format: str, message: str = None):
        """
        Initialize the unsupported format error
        
        Args:
            format: The unsupported format name
            message: Custom error message (optional)
        """
        if message is None:
            message = f"Unsupported diff format: {format}. Supported formats are: {', '.join(SUPPORTED_FORMATS)}"
        super().__init__(message)
        self.format = format


def _generate_diff_match_patch(original_text: str, modified_text: str, options: dict) -> list:
    """
    Internal function implementing diff-match-patch algorithm for text comparison
    
    Args:
        original_text: Original text content
        modified_text: Modified text content
        options: Algorithm options including:
            - cleanup_semantic: Whether to perform semantic cleanup
            - cleanup_efficiency: Whether to perform efficiency cleanup
            - case_sensitive: Whether comparison should be case sensitive
            - ignore_whitespace: Whether to ignore whitespace changes
            
    Returns:
        List of diff operations with change type and content
    """
    # Initialize diff_match_patch instance
    dmp = diff_match_patch()
    
    # Prepare text based on options
    if options.get("case_sensitive", True) is False:
        original_text = original_text.lower()
        modified_text = modified_text.lower()
    
    if options.get("ignore_whitespace", False) is True:
        original_text = re.sub(r'\s+', ' ', original_text).strip()
        modified_text = re.sub(r'\s+', ' ', modified_text).strip()
    
    # Generate diff
    diffs = dmp.diff_main(original_text, modified_text)
    
    # Apply cleanup options
    if options.get("cleanup_semantic", True):
        dmp.diff_cleanupSemantic(diffs)
    
    if options.get("cleanup_efficiency", True):
        dmp.diff_cleanupEfficiency(diffs)
    
    # Process diff operations to structured format
    result = []
    position = 0
    
    for op, text in diffs:
        operation = {
            "operation": "equal" if op == 0 else "delete" if op == -1 else "insert",
            "text": text,
            "position": position if op != 1 else position,
            "length": len(text)
        }
        
        # Update position based on operation
        if op != 1:  # Not an insertion
            position += len(text)
            
        result.append(operation)
    
    logger.debug("Generated diff with diff_match_patch algorithm", 
                result_count=len(result),
                original_length=len(original_text),
                modified_length=len(modified_text))
    
    return result


def _generate_unified_diff(original_text: str, modified_text: str, options: dict) -> list:
    """
    Internal function implementing unified diff algorithm for text comparison
    
    Args:
        original_text: Original text content
        modified_text: Modified text content
        options: Algorithm options including:
            - context_lines: Number of context lines to include
            - from_file: Filename for original text (for unified diff header)
            - to_file: Filename for modified text (for unified diff header)
            
    Returns:
        List of diff operations with line-based changes
    """
    # Split texts into lines
    original_lines = original_text.splitlines(True)
    modified_lines = modified_text.splitlines(True)
    
    # Get context lines option (default to 3)
    context_lines = options.get("context_lines", 3)
    
    # Generate unified diff
    diff_generator = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=options.get("from_file", "original"),
        tofile=options.get("to_file", "modified"),
        n=context_lines,
        lineterm=""
    )
    
    # Parse unified diff into structured format
    result = []
    line_position = 0
    char_position = 0
    
    # Skip headers (first 2 lines)
    try:
        next(diff_generator, None)  # from_file
        next(diff_generator, None)  # to_file
    
        # Skip chunk header if present
        for line in diff_generator:
            if line.startswith("@@"):
                continue
            
            if line.startswith("-"):
                # Deletion
                operation = {
                    "operation": "delete",
                    "text": line[1:],
                    "position": char_position,
                    "length": len(line) - 1,
                    "line": line_position
                }
                char_position += len(line) - 1
                line_position += 1
                result.append(operation)
            elif line.startswith("+"):
                # Addition
                operation = {
                    "operation": "insert",
                    "text": line[1:],
                    "position": char_position,
                    "length": len(line) - 1,
                    "line": line_position
                }
                result.append(operation)
            else:
                # Unchanged
                operation = {
                    "operation": "equal",
                    "text": line,
                    "position": char_position,
                    "length": len(line),
                    "line": line_position
                }
                char_position += len(line)
                line_position += 1
                result.append(operation)
    except Exception as e:
        logger.error("Error processing unified diff", error=str(e))
    
    logger.debug("Generated diff with unified diff algorithm", 
                result_count=len(result),
                original_lines=len(original_lines),
                modified_lines=len(modified_lines))
    
    return result


def _generate_word_level_diff(original_text: str, modified_text: str, options: dict) -> list:
    """
    Internal function implementing word-level diff algorithm for text comparison
    
    Args:
        original_text: Original text content
        modified_text: Modified text content
        options: Algorithm options including:
            - word_pattern: Regex pattern to identify words
            - group_changes: Whether to group adjacent changes of the same type
            - case_sensitive: Whether comparison should be case sensitive
            
    Returns:
        List of diff operations with word-level changes
    """
    # Get word pattern from options or use default
    word_pattern = options.get("word_pattern", r'\b\w+\b|\s+|[^\w\s]')
    
    # Case sensitivity
    if options.get("case_sensitive", True) is False:
        original_text = original_text.lower()
        modified_text = modified_text.lower()
    
    # Split text into words using regex
    original_words = re.findall(word_pattern, original_text)
    modified_words = re.findall(word_pattern, modified_text)
    
    # Use difflib to find differences
    matcher = difflib.SequenceMatcher(None, original_words, modified_words)
    opcodes = matcher.get_opcodes()
    
    # Process opcodes into structured format
    result = []
    char_position = 0
    
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            # Equal content
            equal_text = ''.join(original_words[i1:i2])
            operation = {
                "operation": "equal",
                "text": equal_text,
                "position": char_position,
                "length": len(equal_text)
            }
            char_position += len(equal_text)
            result.append(operation)
        elif tag == 'delete':
            # Deletion
            delete_text = ''.join(original_words[i1:i2])
            operation = {
                "operation": "delete",
                "text": delete_text,
                "position": char_position,
                "length": len(delete_text)
            }
            char_position += len(delete_text)
            result.append(operation)
        elif tag == 'insert':
            # Insertion
            insert_text = ''.join(modified_words[j1:j2])
            operation = {
                "operation": "insert",
                "text": insert_text,
                "position": char_position,
                "length": len(insert_text)
            }
            result.append(operation)
        elif tag == 'replace':
            # Replacement (delete + insert)
            delete_text = ''.join(original_words[i1:i2])
            insert_text = ''.join(modified_words[j1:j2])
            
            # Delete operation
            delete_op = {
                "operation": "delete",
                "text": delete_text,
                "position": char_position,
                "length": len(delete_text)
            }
            result.append(delete_op)
            
            # Insert operation
            insert_op = {
                "operation": "insert",
                "text": insert_text,
                "position": char_position,
                "length": len(insert_text)
            }
            result.append(insert_op)
            
            char_position += len(delete_text)
    
    # Group adjacent changes of the same type if requested
    if options.get("group_changes", True):
        grouped_result = []
        current_group = None
        
        for op in result:
            if current_group is None:
                current_group = op.copy()
                continue
                
            if op["operation"] == current_group["operation"]:
                # Merge with current group
                current_group["text"] += op["text"]
                current_group["length"] += op["length"]
            else:
                # Add current group to result and start a new one
                grouped_result.append(current_group)
                current_group = op.copy()
        
        if current_group is not None:
            grouped_result.append(current_group)
            
        result = grouped_result
    
    logger.debug("Generated diff with word-level diff algorithm", 
                result_count=len(result),
                original_words=len(original_words),
                modified_words=len(modified_words))
    
    return result


def _format_as_track_changes(diff_result: dict, options: dict) -> dict:
    """
    Internal function to format diff result for track changes display
    
    Args:
        diff_result: Diff result to format
        options: Formatting options including:
            - markers: Custom markers for formatting (overrides TRACK_CHANGES_MARKERS)
            - include_positions: Whether to include position information
            
    Returns:
        Formatted diff with track changes markup
    """
    # Get markers from options or use defaults
    markers = options.get("markers", TRACK_CHANGES_MARKERS)
    include_positions = options.get("include_positions", True)
    
    # Extract diff operations
    operations = diff_result.get("operations", [])
    formatted_changes = []
    
    for op in operations:
        op_type = op.get("operation")
        text = op.get("text", "")
        position = op.get("position", 0)
        
        change_id = str(uuid.uuid4())
        
        if op_type == "delete":
            formatted_change = {
                "id": change_id,
                "type": "deletion",
                "original_text": text,
                "formatted_text": f"{markers['deletion_prefix']}{text}{markers['deletion_suffix']}"
            }
            
            if include_positions:
                formatted_change["position"] = position
                formatted_change["length"] = len(text)
                
            formatted_changes.append(formatted_change)
            
        elif op_type == "insert":
            formatted_change = {
                "id": change_id,
                "type": "addition",
                "new_text": text,
                "formatted_text": f"{markers['addition_prefix']}{text}{markers['addition_suffix']}"
            }
            
            if include_positions:
                formatted_change["position"] = position
                formatted_change["length"] = len(text)
                
            formatted_changes.append(formatted_change)
            
        elif op_type == "replace":
            # Replace operations (from unified diff) need special handling
            original_text = op.get("original_text", "")
            new_text = op.get("new_text", "")
            
            formatted_change = {
                "id": change_id,
                "type": "replacement",
                "original_text": original_text,
                "new_text": new_text,
                "formatted_text": (
                    f"{markers['deletion_prefix']}{original_text}{markers['deletion_suffix']}"
                    f"{markers['addition_prefix']}{new_text}{markers['addition_suffix']}"
                )
            }
            
            if include_positions:
                formatted_change["position"] = position
                formatted_change["length"] = len(original_text)
                
            formatted_changes.append(formatted_change)
    
    result = {
        "format": "track_changes",
        "changes": formatted_changes,
        "metadata": diff_result.get("metadata", {})
    }
    
    logger.debug("Formatted diff as track changes", change_count=len(formatted_changes))
    
    return result


def _format_as_inline(diff_result: dict, options: dict) -> dict:
    """
    Internal function to format diff result for inline text display
    
    Args:
        diff_result: Diff result to format
        options: Formatting options including:
            - markers: Custom markers for formatting (overrides TRACK_CHANGES_MARKERS)
            
    Returns:
        Formatted diff with inline markup
    """
    # Get markers from options or use defaults
    markers = options.get("markers", TRACK_CHANGES_MARKERS)
    
    # Extract diff operations
    operations = diff_result.get("operations", [])
    
    # Build inline text with markup
    inline_text = ""
    
    for op in operations:
        op_type = op.get("operation")
        text = op.get("text", "")
        
        if op_type == "equal":
            inline_text += text
        elif op_type == "delete":
            inline_text += f"{markers['deletion_prefix']}{text}{markers['deletion_suffix']}"
        elif op_type == "insert":
            inline_text += f"{markers['addition_prefix']}{text}{markers['addition_suffix']}"
        elif op_type == "replace":
            original_text = op.get("original_text", "")
            new_text = op.get("new_text", "")
            
            inline_text += (
                f"{markers['deletion_prefix']}{original_text}{markers['deletion_suffix']}"
                f"{markers['addition_prefix']}{new_text}{markers['addition_suffix']}"
            )
    
    result = {
        "format": "inline",
        "text": inline_text,
        "metadata": diff_result.get("metadata", {})
    }
    
    logger.debug("Formatted diff as inline text", text_length=len(inline_text))
    
    return result


def _format_as_unified(diff_result: dict, options: dict) -> dict:
    """
    Internal function to format diff result as unified diff
    
    Args:
        diff_result: Diff result to format
        options: Formatting options including:
            - context_lines: Number of context lines to include
            - from_file: Filename for original text (for unified diff header)
            - to_file: Filename for modified text (for unified diff header)
            
    Returns:
        Formatted diff in unified diff format
    """
    # Get options with defaults
    context_lines = options.get("context_lines", 3)
    from_file = options.get("from_file", "original")
    to_file = options.get("to_file", "modified")
    
    # Extract metadata
    metadata = diff_result.get("metadata", {})
    
    # Get original and modified text if available in metadata
    original_text = metadata.get("original_text", "")
    modified_text = metadata.get("modified_text", "")
    
    # If original/modified text not available, reconstruct from operations
    if not original_text or not modified_text:
        operations = diff_result.get("operations", [])
        original_parts = []
        modified_parts = []
        
        for op in operations:
            op_type = op.get("operation")
            text = op.get("text", "")
            
            if op_type == "equal":
                original_parts.append(text)
                modified_parts.append(text)
            elif op_type == "delete":
                original_parts.append(text)
            elif op_type == "insert":
                modified_parts.append(text)
            elif op_type == "replace":
                original_text = op.get("original_text", "")
                new_text = op.get("new_text", "")
                
                original_parts.append(original_text)
                modified_parts.append(new_text)
        
        original_text = "".join(original_parts)
        modified_text = "".join(modified_parts)
    
    # Split texts into lines
    original_lines = original_text.splitlines(True)
    modified_lines = modified_text.splitlines(True)
    
    # Generate unified diff
    diff_generator = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=from_file,
        tofile=to_file,
        n=context_lines,
        lineterm=""
    )
    
    # Convert generator to list
    try:
        unified_diff = "\n".join(list(diff_generator))
    except Exception as e:
        logger.error("Error generating unified diff", error=str(e))
        unified_diff = ""
    
    result = {
        "format": "unified",
        "text": unified_diff,
        "metadata": metadata
    }
    
    logger.debug("Formatted diff as unified diff", text_length=len(unified_diff))
    
    return result


def generate_diff(original_text: str, modified_text: str, 
                 algorithm: str = DEFAULT_ALGORITHM, options: dict = None) -> dict:
    """
    Standalone function to generate diff between two text strings using specified algorithm
    
    Args:
        original_text: Original text content
        modified_text: Modified text content
        algorithm: Differencing algorithm to use
        options: Algorithm-specific options
        
    Returns:
        Structured diff result with detailed change information
        
    Raises:
        UnsupportedAlgorithmError: If the specified algorithm is not supported
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise UnsupportedAlgorithmError(algorithm)
    
    # Initialize options if None
    if options is None:
        options = {}
    
    # Select appropriate diff generation function
    if algorithm == "diff_match_patch":
        operations = _generate_diff_match_patch(original_text, modified_text, options)
    elif algorithm == "unified":
        operations = _generate_unified_diff(original_text, modified_text, options)
    elif algorithm == "word_level":
        operations = _generate_word_level_diff(original_text, modified_text, options)
    
    # Create result structure
    result = {
        "algorithm": algorithm,
        "operations": operations,
        "metadata": {
            "original_text": original_text,
            "modified_text": modified_text,
            "original_length": len(original_text),
            "modified_length": len(modified_text),
            "timestamp": uuid.uuid1().time,
            "options": options
        }
    }
    
    # Add statistics
    result["statistics"] = calculate_diff_statistics(result)
    
    logger.debug("Generated diff", 
                algorithm=algorithm,
                operation_count=len(operations),
                original_length=len(original_text),
                modified_length=len(modified_text))
    
    return result


def calculate_diff_statistics(diff_result: dict) -> dict:
    """
    Calculates statistics about the changes identified in a diff result
    
    Args:
        diff_result: Diff result to analyze
        
    Returns:
        Statistics including counts and percentages of changes
    """
    operations = diff_result.get("operations", [])
    
    # Initialize counters
    total_chars_original = diff_result.get("metadata", {}).get("original_length", 0)
    total_chars_modified = diff_result.get("metadata", {}).get("modified_length", 0)
    
    chars_deleted = 0
    chars_inserted = 0
    chars_unchanged = 0
    
    change_blocks = 0
    current_op_type = None
    
    # Calculate statistics
    for op in operations:
        op_type = op.get("operation")
        text = op.get("text", "")
        
        # Count characters by operation type
        if op_type == "delete":
            chars_deleted += len(text)
        elif op_type == "insert":
            chars_inserted += len(text)
        elif op_type == "equal":
            chars_unchanged += len(text)
        elif op_type == "replace":
            original_text = op.get("original_text", "")
            new_text = op.get("new_text", "")
            
            chars_deleted += len(original_text) if original_text else len(text)
            chars_inserted += len(new_text) if new_text else 0
        
        # Count change blocks
        if op_type != "equal" and op_type != current_op_type:
            change_blocks += 1
            current_op_type = op_type
        elif op_type == "equal":
            current_op_type = None
    
    # Calculate percentages
    percent_deleted = (chars_deleted / total_chars_original * 100) if total_chars_original > 0 else 0
    percent_inserted = (chars_inserted / total_chars_modified * 100) if total_chars_modified > 0 else 0
    percent_unchanged = (chars_unchanged / total_chars_original * 100) if total_chars_original > 0 else 0
    
    # Build statistics object
    statistics = {
        "total_chars_original": total_chars_original,
        "total_chars_modified": total_chars_modified,
        "chars_deleted": chars_deleted,
        "chars_inserted": chars_inserted,
        "chars_unchanged": chars_unchanged,
        "percent_deleted": round(percent_deleted, 2),
        "percent_inserted": round(percent_inserted, 2),
        "percent_unchanged": round(percent_unchanged, 2),
        "change_blocks": change_blocks
    }
    
    logger.debug("Calculated diff statistics", 
                chars_deleted=chars_deleted,
                chars_inserted=chars_inserted,
                chars_unchanged=chars_unchanged,
                change_blocks=change_blocks)
    
    return statistics


class DiffService:
    """
    Primary service that provides text differencing capabilities to compare
    original and modified content with various algorithms and formatting options
    """
    
    def __init__(self, algorithm: str = None, default_options: dict = None):
        """
        Initialize the DiffService with specified algorithm and default options
        
        Args:
            algorithm: Default differencing algorithm to use
            default_options: Default options for diff generation and formatting
            
        Raises:
            UnsupportedAlgorithmError: If the specified algorithm is not supported
        """
        # Validate algorithm if provided
        if algorithm is not None and algorithm not in SUPPORTED_ALGORITHMS:
            raise UnsupportedAlgorithmError(algorithm)
        
        self._algorithm = algorithm or DEFAULT_ALGORITHM
        self._default_options = default_options or {}
        
        logger.info("Initialized DiffService", 
                   algorithm=self._algorithm,
                   default_options=self._default_options)
    
    def compare_texts(self, original_text: str, modified_text: str, 
                     algorithm: str = None, options: dict = None) -> dict:
        """
        Compare two text strings and return detailed diff information
        
        Args:
            original_text: Original text content
            modified_text: Modified text content
            algorithm: Differencing algorithm to use (overrides instance default)
            options: Algorithm-specific options (merged with instance defaults)
            
        Returns:
            Structured diff result with change information
            
        Raises:
            UnsupportedAlgorithmError: If the specified algorithm is not supported
        """
        # Use instance algorithm if none specified
        algorithm = algorithm or self._algorithm
        
        # Merge options with instance defaults
        merged_options = self._default_options.copy()
        if options:
            merged_options.update(options)
        
        # Generate diff
        diff_result = generate_diff(original_text, modified_text, algorithm, merged_options)
        
        # Log operation
        stats = diff_result.get("statistics", {})
        logger.info("Compared texts", 
                   algorithm=algorithm,
                   original_length=len(original_text),
                   modified_length=len(modified_text),
                   chars_deleted=stats.get("chars_deleted", 0),
                   chars_inserted=stats.get("chars_inserted", 0),
                   change_blocks=stats.get("change_blocks", 0))
        
        return diff_result
    
    def format_for_display(self, diff_result: dict, format: str, format_options: dict = None) -> dict:
        """
        Format diff result for display in specified format
        
        Args:
            diff_result: Diff result to format
            format: Output format (track_changes, inline, unified)
            format_options: Format-specific options
            
        Returns:
            Formatted diff result ready for display
            
        Raises:
            UnsupportedFormatError: If the specified format is not supported
        """
        if format not in SUPPORTED_FORMATS:
            raise UnsupportedFormatError(format)
        
        # Initialize format options if None
        if format_options is None:
            format_options = {}
        
        # Merge with instance default options
        merged_options = self._default_options.copy()
        if format_options:
            merged_options.update(format_options)
        
        # Select appropriate formatter
        if format == "track_changes":
            formatted_result = _format_as_track_changes(diff_result, merged_options)
        elif format == "inline":
            formatted_result = _format_as_inline(diff_result, merged_options)
        elif format == "unified":
            formatted_result = _format_as_unified(diff_result, merged_options)
        
        logger.debug("Formatted diff for display", 
                    format=format,
                    options=merged_options)
        
        return formatted_result
    
    def get_supported_formats(self) -> list:
        """
        Returns list of supported output formats
        
        Returns:
            List of supported format names
        """
        return SUPPORTED_FORMATS
    
    def get_supported_algorithms(self) -> list:
        """
        Returns list of supported differencing algorithms
        
        Returns:
            List of supported algorithm names
        """
        return SUPPORTED_ALGORITHMS
    
    def create_suggestion_from_diff(self, diff_result: dict, 
                                   suggestion_metadata: dict = None) -> list:
        """
        Converts diff result to structured suggestion format for the AI system
        
        Args:
            diff_result: Diff result to convert
            suggestion_metadata: Additional metadata to include with suggestions
            
        Returns:
            List of structured suggestions for AI system
        """
        operations = diff_result.get("operations", [])
        
        if suggestion_metadata is None:
            suggestion_metadata = {}
        
        suggestions = []
        current_suggestion = None
        
        # Group related changes into coherent suggestions
        for op in operations:
            op_type = op.get("operation")
            
            if op_type == "equal":
                # Equal operations separate suggestions
                if current_suggestion is not None:
                    suggestions.append(current_suggestion)
                    current_suggestion = None
                continue
            
            # Initialize a new suggestion group if needed
            if current_suggestion is None:
                current_suggestion = {
                    "id": str(uuid.uuid4()),
                    "changes": [],
                    "position": op.get("position", 0),
                    "metadata": suggestion_metadata.copy()
                }
            
            # Add the operation to the current suggestion
            current_suggestion["changes"].append(op)
        
        # Add the last suggestion if there is one
        if current_suggestion is not None:
            suggestions.append(current_suggestion)
        
        # Format each suggestion
        formatted_suggestions = []
        
        for suggestion in suggestions:
            changes = suggestion.get("changes", [])
            
            # Skip empty suggestions
            if not changes:
                continue
            
            # Extract original and suggested text
            original_text = ""
            suggested_text = ""
            
            for change in changes:
                if change.get("operation") == "delete":
                    original_text += change.get("text", "")
                elif change.get("operation") == "insert":
                    suggested_text += change.get("text", "")
                elif change.get("operation") == "replace":
                    original_text += change.get("original_text", "")
                    suggested_text += change.get("new_text", "")
            
            # Create formatted suggestion
            formatted_suggestion = {
                "id": suggestion["id"],
                "position": suggestion["position"],
                "original_text": original_text,
                "suggested_text": suggested_text,
                "metadata": suggestion["metadata"]
            }
            
            formatted_suggestions.append(formatted_suggestion)
        
        logger.debug("Created suggestions from diff", 
                    suggestion_count=len(formatted_suggestions))
        
        return formatted_suggestions
    
    def apply_selected_changes(self, original_text: str, diff_result: dict, 
                              selected_change_ids: list) -> str:
        """
        Apply selected changes from a diff result to transform original text
        
        Args:
            original_text: Original text content
            diff_result: Diff result containing changes
            selected_change_ids: List of change IDs to apply
            
        Returns:
            Transformed text with selected changes applied
        """
        # Get formatted diff with track changes
        track_changes = diff_result
        
        # If diff_result is not already in track_changes format, convert it
        if "format" not in diff_result or diff_result["format"] != "track_changes":
            track_changes = self.format_for_display(diff_result, "track_changes")
        
        # Extract changes
        changes = track_changes.get("changes", [])
        
        # Filter changes by selected IDs
        selected_changes = [c for c in changes if c.get("id") in selected_change_ids]
        
        # Sort changes by position in reverse order to prevent position shifts
        selected_changes.sort(key=lambda c: c.get("position", 0), reverse=True)
        
        # Apply each selected change
        result_text = original_text
        
        for change in selected_changes:
            change_type = change.get("type")
            position = change.get("position", 0)
            
            if change_type == "deletion":
                # For deletions, remove the content
                length = len(change.get("original_text", ""))
                result_text = result_text[:position] + result_text[position + length:]
                
            elif change_type == "addition":
                # For additions, insert the new content
                new_text = change.get("new_text", "")
                result_text = result_text[:position] + new_text + result_text[position:]
                
            elif change_type == "replacement":
                # For replacements, replace the original with new
                length = len(change.get("original_text", ""))
                new_text = change.get("new_text", "")
                result_text = result_text[:position] + new_text + result_text[position + length:]
        
        logger.info("Applied selected changes", 
                   original_length=len(original_text),
                   result_length=len(result_text),
                   applied_changes=len(selected_changes))
        
        return result_text
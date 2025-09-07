import os
import json
from datetime import datetime
from typing import List, Dict, Any

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "data",
        "data/vectors",
        "data/exports"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes = int(size_bytes / 1024.0)
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    return filename if filename else "unnamed_file"

def load_json_data(file_path: str, default: Any = None) -> Any:
    """Safely load JSON data from file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default if default is not None else []
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {str(e)}")
        return default if default is not None else []

def save_json_data(file_path: str, data: Any) -> bool:
    """Safely save JSON data to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {str(e)}")
        return False

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def extract_text_preview(text: str, length: int = 200) -> str:
    """Extract a clean preview of text content"""
    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    if len(text) <= length:
        return text
    
    # Try to break at word boundary
    preview = text[:length]
    last_space = preview.rfind(' ')
    
    if last_space > length * 0.8:  # If we can break reasonably close to the end
        preview = preview[:last_space]
    
    return preview + "..."

def get_file_type_icon(file_type: str) -> str:
    """Get appropriate icon for file type"""
    icons = {
        'pdf': '📄',
        'application/pdf': '📄',
        'md': '📝',
        'text/markdown': '📝',
        'html': '🌐',
        'text/html': '🌐',
        'htm': '🌐',
        'text/htm': '🌐'
    }
    
    return icons.get(file_type.lower(), '📄')

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate if file type is allowed"""
    if not filename:
        return False
    
    file_extension = filename.split('.')[-1].lower()
    return file_extension in [ext.lower() for ext in allowed_types]

def clean_text_for_embedding(text: str) -> str:
    """Clean text for better embedding generation"""
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
    
    # Remove multiple consecutive punctuation
    text = re.sub(r'[\.]{2,}', '.', text)
    text = re.sub(r'[,]{2,}', ',', text)
    
    return text.strip()

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)"""
    # Rough estimation: 1 token ≈ 0.75 words for English
    words = len(text.split())
    return int(words / 0.75)

def get_chunk_summary(chunk: Dict[str, Any]) -> str:
    """Get a summary description of a chunk"""
    word_count = chunk.get('word_count', 0)
    chunk_id = chunk.get('chunk_id', 'Unknown')
    preview = truncate_text(chunk.get('text', ''), 50)
    
    return f"Chunk {chunk_id} ({word_count} words): {preview}"

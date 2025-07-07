import chardet

def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']
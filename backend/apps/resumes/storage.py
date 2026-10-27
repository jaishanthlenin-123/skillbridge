import os
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError

MAGIC_SIGNATURES = {
    'pdf': b'%PDF-',
    'docx': b'PK\x03\x04',
}

def validate_and_save_private_file(uploaded_file, user_id: str) -> dict:
    """
    Validates uploaded document for size, extension, magic bytes, and stores privately.
    Returns:
        {
            'original_filename': str,
            'storage_key': str,
            'file_hash': str,
            'file_size': int,
            'extension': str,
            'mime_type': str
        }
    """
    filename = uploaded_file.name
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if ext not in ('pdf', 'docx'):
        raise ValidationError(f"Unsupported file format '{ext}'. Only PDF and DOCX files are supported.")

    file_size = uploaded_file.size
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
    if file_size > max_size:
        raise ValidationError(f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum limit of {max_size / (1024*1024):.1f}MB.")

    # Read first chunk for magic bytes check
    uploaded_file.seek(0)
    header = uploaded_file.read(8)
    expected_magic = MAGIC_SIGNATURES.get(ext)
    if not header.startswith(expected_magic):
        raise ValidationError(f"Invalid file signature for extension .{ext}. The file content does not match the file extension.")

    # Compute SHA-256 hash
    hasher = hashlib.sha256()
    uploaded_file.seek(0)
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    file_hash = hasher.hexdigest()

    # Determine storage directory and file path (sanitized against path traversal)
    safe_user_id = "".join(c for c in str(user_id) if c.isalnum() or c in ('-', '_'))
    if not safe_user_id:
        safe_user_id = "default"

    user_storage_dir = Path(settings.PRIVATE_STORAGE_ROOT) / safe_user_id
    user_storage_dir.mkdir(parents=True, exist_ok=True)

    storage_filename = f"{file_hash}.{ext}"
    dest_path = user_storage_dir / storage_filename

    # Save to disk
    uploaded_file.seek(0)
    with open(dest_path, 'wb') as dest_file:
        for chunk in uploaded_file.chunks():
            dest_file.write(chunk)

    rel_storage_key = str(Path(safe_user_id) / storage_filename)
    mime_type = 'application/pdf' if ext == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    return {
        'original_filename': filename,
        'storage_key': rel_storage_key,
        'file_hash': file_hash,
        'file_size': file_size,
        'extension': ext,
        'mime_type': mime_type,
        'absolute_path': str(dest_path),
    }

def delete_private_file(storage_key: str):
    """
    Safely purges physical file from private storage disk with strict boundary check.
    """
    if not storage_key:
        return
    try:
        base_dir = Path(settings.PRIVATE_STORAGE_ROOT).resolve()
        target_path = (base_dir / storage_key).resolve()
        # Prevent path traversal outside PRIVATE_STORAGE_ROOT
        if base_dir in target_path.parents or base_dir == target_path.parent:
            if target_path.exists() and target_path.is_file():
                os.remove(target_path)
    except Exception as e:
        pass

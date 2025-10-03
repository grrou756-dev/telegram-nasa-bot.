# imghdr.py — lightweight replacement for removed stdlib imghdr (basic magic bytes)
# Placed next to bot.py so libraries that "import imghdr" will find it.

def _read_header(file):
    try:
        # file can be a path or a file-like object
        if isinstance(file, (str, bytes, bytearray)):
            with open(file, "rb") as f:
                return f.read(64)
        else:
            # assume file-like object
            pos = None
            try:
                pos = file.tell()
            except Exception:
                pos = None
            header = file.read(64)
            try:
                if pos is not None:
                    file.seek(pos)
            except Exception:
                pass
            return header
    except Exception:
        return None

def what(file, h=None):
    """
    Minimal implementation of imghdr.what().
    Returns one of: 'jpeg', 'png', 'gif', 'bmp', 'webp' or None.
    """
    if h is None:
        h = _read_header(file)
    if not h:
        return None

    # JPEG
    if h[:3] == b'\xff\xd8\xff':
        return "jpeg"
    # PNG
    if h.startswith(b'\x89PNG\r\n\x1a\n'):
        return "png"
    # GIF
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return "gif"
    # BMP
    if h[:2] == b'BM':
        return "bmp"
    # WebP (RIFF .... WEBP)
    if h[:4] == b'RIFF' and b'WEBP' in h[:12]:
        return "webp"

    return None

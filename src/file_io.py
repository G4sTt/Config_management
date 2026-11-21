"""Atomically save generated text files."""

import os
import tempfile


def write_text(path, text):
    """Replace a result only after writing the full UTF-8 content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, mode="w", encoding="utf-8", newline="\n",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)

"""
Containment helper for filesystem paths that arrive from the client.

Several Gradio handlers take a path as a plain string and hand it straight to
``shutil.rmtree``, ``shutil.copy``, ``shutil.copytree`` or a desktop "open"
command. Gradio does not validate component values server-side and every
``api_name`` endpoint is callable directly, so those strings are attacker
controlled. ``resolve_within`` gives them a single, shared boundary.
"""

import os
from typing import Iterable

# Directories the app legitimately reads and writes generations in.
DEFAULT_ROOTS = (
    "outputs",
    "favorites",
    "voices",
    "collections",
    "outputs-rvc",
    "voices-tortoise",
)


class UnsafePathError(ValueError):
    """Raised when a client-supplied path escapes its permitted roots."""


def resolve_within(candidate: str, roots: Iterable[str] = DEFAULT_ROOTS) -> str:
    """
    Resolve *candidate* and require the result to live inside one of *roots*.

    Roots are interpreted relative to the working directory, which is the
    project root. Symlinks are resolved first, so a symlink planted inside an
    output directory cannot be used to step outside it.

    Returns the resolved absolute path, or raises :class:`UnsafePathError`.
    """
    if not candidate or not str(candidate).strip():
        raise UnsafePathError("Empty path")

    base = os.path.realpath(os.getcwd())
    target = os.path.realpath(os.path.join(base, str(candidate)))

    for root in roots:
        root_abs = os.path.realpath(os.path.join(base, root))
        if target == root_abs or target.startswith(root_abs + os.sep):
            return target

    raise UnsafePathError(
        f"Refusing to operate on a path outside {', '.join(roots)}: {candidate}"
    )


def safe_directory_name(name: str) -> str:
    """
    Validate a single directory name supplied by the client.

    Rejects separators, parent references and absolute paths, so the result is
    always safe to join onto a trusted root.
    """
    cleaned = (name or "").strip()

    if not cleaned:
        raise UnsafePathError("Empty directory name")
    if cleaned in (os.curdir, os.pardir):
        raise UnsafePathError("Invalid directory name")
    if os.path.isabs(cleaned) or os.path.splitdrive(cleaned)[0]:
        raise UnsafePathError("Absolute paths are not allowed")
    if "/" in cleaned or "\\" in cleaned or os.sep in cleaned:
        raise UnsafePathError("Directory name may not contain path separators")

    return cleaned

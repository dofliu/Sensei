"""Sensei core modules.

Re-exports are lazy (PEP 562). Importing a leaf module that needs no models —
`core.session`, `core.glossary`, and through them `frontend.handout` and
`frontend.display` — must not drag in faster-whisper and CUDA just because the
package __init__ mentions SenseiASR. `from core import SenseiPipeline` behaves
exactly as before; it simply resolves on first access.
"""

_LAZY = {
    "SenseiASR":       ".asr",
    "ASRConfig":       ".asr",
    "SenseiLLM":       ".llm",
    "LLMConfig":       ".llm",
    "SenseiPipeline":  ".pipeline",
    "TEMPLATE_REGISTRY": ".templates",
    "Glossary":        ".glossary",
    "list_glossaries": ".glossary",
    "load_glossary":   ".glossary",
    "Session":         ".session",
}

__all__ = list(_LAZY)


def __getattr__(name: str):
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module 'core' has no attribute {name!r}")
    from importlib import import_module
    return getattr(import_module(module, __name__), name)


def __dir__():
    return sorted(__all__)

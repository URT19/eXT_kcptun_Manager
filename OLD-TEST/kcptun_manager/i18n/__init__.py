"""Bilingual messages (Finglish / English)."""

from kcptun_manager.i18n.en import EN
from kcptun_manager.i18n.fa import FA

_LANG = "fa"  # default


def set_lang(lang: str) -> None:
    global _LANG
    if lang in ("fa", "en"):
        _LANG = lang


def get_lang() -> str:
    return _LANG


def t(key: str) -> str:
    table = FA if _LANG == "fa" else EN
    return table.get(key, EN.get(key, key))
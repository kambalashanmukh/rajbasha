import hashlib
from typing import Optional
from django import template
from django.core.cache import cache
from deep_translator import GoogleTranslator


register = template.Library()

@register.filter(name='t')
def translate_text(text: Optional[str], lang: str) -> str:
    """Translate `text` to `lang` and always return a string.

    Coerce `None` to an empty string so callers (including `messages.error`)
    always receive a `str`.
    """
    text_str = str(text) if text is not None else ""

    if lang == 'en' or text_str == "":
        return text_str

    cache_key = f"trans_{lang}_{hashlib.sha256(text_str.encode(), usedforsecurity=False).hexdigest()}"

    try:
        return cache.get_or_set(
            cache_key,
            lambda: GoogleTranslator(source='en', target=lang).translate(text_str),
            86400,
        )
    except Exception as e:
        print(f"Translation failed: {e}")
        return text_str


@register.filter(name='mask_email')
def mask_email(value: Optional[str]) -> str:
    """Obfuscate email addresses for display."""
    email = str(value or "").strip()
    if "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if not local or not domain:
        return email.replace("@", " [at] ").replace(".", " [dot] ")

    visible_local = local[:1]
    domain_parts = domain.split(".")
    visible_domain = domain_parts[0][:1] + "***" if domain_parts and domain_parts[0] else "***"
    suffix = " [dot] ".join(domain_parts[1:]) if len(domain_parts) > 1 else ""
    masked = f"{visible_local}*** [at] {visible_domain}"
    return f"{masked} [dot] {suffix}" if suffix else masked

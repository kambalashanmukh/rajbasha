from urllib import response
import base64
import hashlib
import logging
import secrets
from bs4 import BeautifulSoup, Comment
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404
from django.core.cache import cache
import hashlib
from django.utils.cache import add_never_cache_headers
from .services.parichay import ParichayService

logger = logging.getLogger(__name__)


def _csp_sha256(value):
    digest = hashlib.sha256(value.encode("utf-8"), usedforsecurity=False).digest()
    return "'sha256-%s'" % base64.b64encode(digest).decode("ascii")


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Log application errors while showing only safe generic error pages."""

    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None

        if isinstance(exception, SuspiciousOperation):
            status_code = 400
            logger.warning("Bad request blocked at %s %s", request.method, request.get_full_path())
        elif isinstance(exception, PermissionDenied):
            status_code = 403
            logger.warning("Permission denied at %s %s", request.method, request.get_full_path())
        elif isinstance(exception, Http404):
            status_code = 404
            logger.info("Page not found at %s %s", request.method, request.get_full_path())
        else:
            status_code = 500
            logger.exception("Unhandled application error at %s %s", request.method, request.get_full_path())

        from .views import universal_error_view
        return universal_error_view(request, None, status_code)


class DynamicTranslationMiddleware(MiddlewareMixin):
    # Added more technical artifacts to prevent them from showing as "एचटीएमएल"
    BLACKLIST = ['HTML', 'html', 'Banner carousel', 'csrfmiddlewaretoken', 'doctype', 'DOCTYPE']
    
    # Task Requirement: Keep these fields UNCHANGED even in Hindi
    # Add the exact field names/labels you want to lock here
    LOCKED_FIELDS = ['Empcode', 'Superannuation Date'] 

    MANUAL_MAP = {
        'hi': {
            'Select': 'चुनना',
            'Actions': 'कार्रवाई',
            'Drafts': 'ड्राफ्ट',
            'Submitted Records': 'प्रस्तुत अभिलेख',
            'Back to Drafts': 'ड्राफ्ट पर वापस जाएँ',
            'Back to Form': 'फॉर्म पर वापस जाएँ',
            'Prabodh': 'प्रबोध',
            'Praveen': 'प्रवीण',
            'Pragya': 'प्रज्ञा',
            'Parangat': 'पारंगत',
            'Typing': 'टाइपिंग',
            'Hindi Proficiency': 'हिंदी प्रवीणता',
            'Gazetted': 'राजपत्रित',
            'Non-Gazetted': 'अराजपत्रित',
            'Passed': 'उत्तीर्ण',
            'Did not Appear': 'उपस्थित नहीं हुए',
            'Senior Assistant': 'सहायक अनुभाग अधिकारी',
            'Section Officer': 'अनुभाग अधिकारी'
        }
    }

    def process_response(self, request, response):
        if request.method != "GET":
            return response

        target_lang = request.GET.get("lang")

        if (
            request.method == "GET"
            and target_lang
            and target_lang != "en"
            and "text/html" in response.get("Content-Type", "")
        ):
            try:
                content = response.content.decode("utf-8")
                soup = BeautifulSoup(content, "html.parser")

                # Remove HTML comments
                for comment in soup.find_all(
                    string=lambda text: isinstance(text, Comment)
                ):
                    comment.extract()

                # Only use local/manual translations.
                manual_translations = self.MANUAL_MAP.get(target_lang, {})

                for element in soup.find_all(string=True):

                    # Skip technical/code elements
                    if element.parent.name in [
                        "script",
                        "style",
                        "code",
                        "head",
                        "title",
                        "meta",
                    ]:
                        continue

                    original_text = element.strip()

                    # Skip empty and numeric content
                    if not original_text or original_text.isdigit():
                        continue

                    # Keep locked fields unchanged
                    if original_text in self.LOCKED_FIELDS:
                        continue

                    # Keep blacklisted technical text unchanged
                    if original_text.upper() in [
                        item.upper() for item in self.BLACKLIST
                    ]:
                        continue

                    # Do not process HTML-looking text
                    if "<" in original_text or ">" in original_text:
                        continue

                    # Use ONLY the local translation dictionary.
                    translated_text = manual_translations.get(original_text)

                    if translated_text:
                        element.replace_with(translated_text)

                response.content = soup.encode("utf-8")

            except Exception as e:
                logger.exception(
                    "Offline translation middleware failed: %s",
                    e
                )

        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)

    def _prepare_html_for_csp(self, request, response):
        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type or getattr(response, "streaming", False):
            return [], []

        try:
            charset = getattr(response, "charset", None) or "utf-8"
            soup = BeautifulSoup(response.content.decode(charset), "html.parser")
            nonce = getattr(request, "csp_nonce", "")
            script_attr_hashes = set()
            style_attr_hashes = set()

            for tag in soup.find_all(["script", "style"]):
                if nonce and not tag.get("nonce"):
                    tag["nonce"] = nonce

            for tag in soup.find_all(True):
                for attr_name, attr_value in list(tag.attrs.items()):
                    if attr_name.lower().startswith("on"):
                        if isinstance(attr_value, list):
                            attr_value = " ".join(attr_value)
                        script_attr_hashes.add(_csp_sha256(str(attr_value)))
                    elif attr_name.lower() == "style":
                        if isinstance(attr_value, list):
                            attr_value = " ".join(attr_value)
                        style_attr_hashes.add(_csp_sha256(str(attr_value)))

            response.content = soup.encode(charset)
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))
            return sorted(script_attr_hashes), sorted(style_attr_hashes)
        except Exception:
            logger.exception("Failed to apply CSP nonces")
            return [], []

    def process_response(self, request, response):
        # Preserve any stronger upstream setting while preventing an explicit disable state.
        nonce = getattr(request, "csp_nonce", "")
        script_attr_hashes, style_attr_hashes = self._prepare_html_for_csp(request, response)
        script_sources = ["'self'"]
        style_sources = ["'self'", "https://cdn.jsdelivr.net"]
        if nonce:
            script_sources.append(f"'nonce-{nonce}'")
            style_sources.append(f"'nonce-{nonce}'")
        if script_attr_hashes:
            script_sources.append("'unsafe-hashes'")
            script_sources.extend(script_attr_hashes)
        if style_attr_hashes:
            style_sources.append("'unsafe-hashes'")
            style_sources.extend(style_attr_hashes)

        response.setdefault("X-XSS-Protection", "1; mode=block")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("Cross-Origin-Embedder-Policy", "require-corp")
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault(
            "Content-Security-Policy",
            "; ".join([
                "default-src 'self'",
                f"script-src {' '.join(script_sources)}",
                f"style-src {' '.join(style_sources)}",
                "font-src 'self' https://cdn.jsdelivr.net data:",
                "img-src 'self' data: blob:",
                "connect-src 'self'",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'self'",
            ]),
        )
        response ["Server"] = ""
        if "X-Powered-By" in response:
            del response["X-Powered-By"]
        return response
        
class StripUnnecessaryHeadersMiddleware(MiddlewareMixin):
    """Remove or mask runtime diagnostic headers that may leak server information."""
    def process_response(self, request, response):
        # Remove Server header if present
        response ["Server"] = ""
        if "Server" in response:
            del response["Server"]
        return response

class NoCacheMiddleware(MiddlewareMixin):
    """Add headers to prevent caching of sensitive pages."""
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
    
class ParichayTokenRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            access_token = request.session.get("parichay_access_token")
            refresh_token = request.session.get("parichay_refresh_token")
            expires_at = request.session.get("parichay_token_expires_at")

            if access_token and refresh_token:
                try:
                    (
                        new_access_token,
                        new_refresh_token,
                        new_expires_at,
                    ) = ParichayService.refresh_if_expired(
                        access_token,
                        refresh_token,
                        expires_at,
                    )

                    if new_expires_at is not None:
                        request.session["parichay_access_token"] = (
                            new_access_token
                        )
                        request.session["parichay_refresh_token"] = (
                            new_refresh_token
                        )
                        request.session["parichay_token_expires_at"] = (
                            new_expires_at
                        )

                except Exception as e:
                    print("PARICHAY TOKEN REFRESH FAILED:", e)

        response = self.get_response(request)
        return response

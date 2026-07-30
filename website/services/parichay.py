import requests
import secrets
from urllib.parse import urlencode

from django.conf import settings

class ParichayService:
    """
    Handles all communication with the Parichay OAuth 2.0 service.

    Responsibilities:
    - Build authorization URL
    - Exchange authorization code for tokens
    - Fetch user details
    - Refresh access tokens
    - Revoke tokens
    """

    @staticmethod
    def build_authorization_url(code_challenge, state):
        """
        Build the Parichay Authorization URL.
        """

        params = {
            "response_type": settings.PARICHAY_RESPONSE_TYPE,
            "client_id": settings.PARICHAY_CLIENT_ID,
            "redirect_uri": settings.PARICHAY_REDIRECT_URI,
            "scope": settings.PARICHAY_SCOPE,
            "state": state,
            "code_challenge_method": settings.PARICHAY_CODE_CHALLENGE_METHOD,
            "code_challenge": code_challenge,
        }

        return f"{settings.PARICHAY_AUTHORIZATION_URL}?{urlencode(params)}"
    
    @staticmethod
    def generate_state():
        """
        Generate a random state value for CSRF protection.
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def exchange_code_for_token(code, code_verifier):
        """
        Exchange the authorization code for an access token.
        """

        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.PARICHAY_CLIENT_ID,
            "client_secret": settings.PARICHAY_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.PARICHAY_REDIRECT_URI,
            "code_verifier": code_verifier,
        }

        response = requests.post(
            settings.PARICHAY_TOKEN_URL,
            data=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
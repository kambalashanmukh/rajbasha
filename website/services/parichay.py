import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

import logging

token_log = logging.getLogger('parichay_token')
userinfo_log = logging.getLogger('parichay_userinfo')
refresh_log = logging.getLogger('parichay_refresh')
revoke_log = logging.getLogger('parichay_revoke')

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

        token_log.info("Parichay token endpoint called")

        response = requests.post(
            settings.PARICHAY_TOKEN_URL,
            data=payload,
            timeout=30,
        )

        token_log.info("Parichay token endpoint response: %s", response.status_code)

        if not response.ok:
            print("PARICHAY TOKEN ERROR")
            print("Status:", response.status_code)
            print("Response:", response.text)

        response.raise_for_status()

        return response.json()
    
    @staticmethod
    def get_user_details(access_token):

        userinfo_log.info("Parichay user info endpoint called")

        response = requests.get(

            settings.PARICHAY_USERINFO_URL,
            headers={
                "Authorization": access_token,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        userinfo_log.info(
            "Parichay user info endpoint response: %s",
            response.status_code
        )

        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    def revoke_token(access_token):
        """
        Revoke the Parichay access token.
        """

        revoke_log.info("Parichay revoke endpoint called")

        response = requests.get(
            settings.PARICHAY_REVOKE_URL,
            headers={
                "Authorization": access_token,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        
        revoke_log.info(
            "Parichay revoke endpoint response: %s",
            response.status_code
        )

        if not response.ok:
            print("PARICHAY REVOKE ERROR")
            print("Status:", response.status_code)
            print("Response:", response.text)

        response.raise_for_status()
        return response.json()
    

    @staticmethod
    def refresh_access_token(refresh_token):
        """
        Refresh the Parichay access token using the refresh token.
        """

        refresh_log.info("Parichay refresh endpoint called")

        response = requests.post(
            settings.PARICHAY_TOKEN_URL,
            headers={
                "Authorization": refresh_token,
                "Content-Type": "application/json",
            },
            json={
                "grant_type": "refresh_token",
            },
            timeout=30,
        )

        refresh_log.info(
            "Parichay refresh endpoint response: %s",
            response.status_code
        )

        if not response.ok:
            print("PARICHAY REFRESH TOKEN ERROR")
            print("Status:", response.status_code)
            print("Response:", response.text)

        response.raise_for_status()
        return response.json()
    

    @staticmethod
    def is_token_expired(expires_at):
        """
        Check whether the Parichay access token has expired.
        """
        if not expires_at:
            return True

        return timezone.now().timestamp() >= float(expires_at)
    
    @staticmethod
    def refresh_if_expired(access_token, refresh_token, expires_at):
        """
        Refresh the access token if it has expired.
        """
        if not ParichayService.is_token_expired(expires_at):
            return access_token, refresh_token, None

        if not refresh_token:
            raise ValueError("Parichay refresh token is missing.")

        token_response = ParichayService.refresh_access_token(
            refresh_token
        )

        new_access_token = token_response.get("access_token")
        new_refresh_token = token_response.get(
            "refresh_token",
            refresh_token,
        )
        expires_in = token_response.get("expires_in")

        if not new_access_token:
            raise ValueError(
                "Access token not received from Parichay refresh API."
            )
        
        new_expires_at = timezone.now().timestamp() + (7 * 24 * 60 * 60)

        return (
            new_access_token,
            new_refresh_token,
            new_expires_at,
        )
        
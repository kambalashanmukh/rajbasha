import pkce


class PKCEService:
    """
    Handles PKCE (Proof Key for Code Exchange)
    generation required by Parichay OAuth 2.0.
    """

    @staticmethod
    def generate_pkce_pair():
        """
        Generate a code_verifier and code_challenge.
        """

        code_verifier, code_challenge = pkce.generate_pkce_pair()

        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
        }
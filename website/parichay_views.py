from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import login

from .services.parichay import ParichayService
from .services.pkce import PKCEService
from .models import CustomUser

def parichay_login(request):
    """
    Redirect the user to the Parichay login page.
    """

    # Generate PKCE values
    pkce_data = PKCEService.generate_pkce_pair()

    code_verifier = pkce_data["code_verifier"]
    code_challenge = pkce_data["code_challenge"]

    # Generate state
    state = ParichayService.generate_state()

    # Store values in session
    request.session["code_verifier"] = code_verifier
    request.session["oauth_state"] = state

    # Build authorization URL
    authorization_url = ParichayService.build_authorization_url(
        code_challenge=code_challenge,
        state=state,
    )

    # Redirect to Parichay
    return redirect(authorization_url)

def parichay_callback(request):
    """
    Callback endpoint invoked by Parichay after authentication.
    """

    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code:
        return HttpResponse("Authorization code not received.", status=400)

    session_state = request.session.get("oauth_state")

    if state != session_state:
        return HttpResponse("Invalid state parameter.", status=400)

    code_verifier = request.session.get("code_verifier")

    if not code_verifier:
        return HttpResponse("Missing PKCE code verifier.", status=400)

    try:
        token_response = ParichayService.exchange_code_for_token(
            code=code,
            code_verifier=code_verifier,
        )
    except Exception as e:
        return HttpResponse(
            f"Token exchange failed: {str(e)}",
            status=400,
        )
    
    access_token = token_response.get("access_token")

    if not access_token:
        return HttpResponse(
            "Access token not received from Parichay.",
            status=400,
        )
    try:
        user_info = ParichayService.get_user_details(access_token)

    except Exception as e:
        return HttpResponse(
            f"Unable to fetch user details: {str(e)}",
            status=400,
        )
    
    return HttpResponse(str(user_info))

    # ============================================================
    # STEP 2 (Disabled for now)
    # Login existing Django user using Parichay details
    # Enable only after UserInfo payload is verified.
    # ============================================================

    # employee_code = user_info.get("employeeCode")
    #
    # if not employee_code:
    #     return HttpResponse(
    #         "Employee Code not found in Parichay response.",
    #         status=400,
    #     )
    #
    # try:
    #     user = CustomUser.objects.get(username=employee_code)
    # except CustomUser.DoesNotExist:
    #     return HttpResponse(
    #         "No matching local user found.",
    #         status=404,
    #     )
    #
    # login(
    #     request,
    #     user,
    #     backend="django.contrib.auth.backends.ModelBackend",
    # )
    #
    # return redirect("dashboard")
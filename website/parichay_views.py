import logging

from django.contrib.auth import login
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import CustomUser, UserProfile
from .services.parichay import ParichayService
from .services.pkce import PKCEService

log = logging.getLogger("")

def parichay_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    pkce_data = PKCEService.generate_pkce_pair()

    request.session["code_verifier"] = pkce_data["code_verifier"]
    request.session["oauth_state"] = ParichayService.generate_state()

    authorization_url = ParichayService.build_authorization_url(
        code_challenge=pkce_data["code_challenge"],
        state=request.session["oauth_state"],
    )
    
    log.info("Parichay Authorization URL: %s", authorization_url)

    return redirect(authorization_url)


def parichay_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    # ---------------------------------------------------------
    # Validate authorization response
    # ---------------------------------------------------------
    if not code:
        return HttpResponse(
            "Authorization code not received.",
            status=400,
        )

    session_state = request.session.get("oauth_state")

    if not session_state or state != session_state:
        return HttpResponse(
            "Invalid state parameter.",
            status=400,
        )

    code_verifier = request.session.get("code_verifier")

    if not code_verifier:
        return HttpResponse(
            "Missing PKCE code verifier.",
            status=400,
        )

    # ---------------------------------------------------------
    # Exchange authorization code for access token
    # ---------------------------------------------------------
    try:
        token_response = ParichayService.exchange_code_for_token(
            code=code,
            code_verifier=code_verifier,
        )

        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")

        if not access_token:
            return HttpResponse(
                "Access token not received from Parichay.",
                status=400,
            )

        user_info = ParichayService.get_user_details(access_token)

    except Exception as e:
        return HttpResponse(
            f"Parichay authentication failed: {str(e)}",
            status=400,
        )

    # ---------------------------------------------------------
    # Extract Parichay user information
    # ---------------------------------------------------------
    parichay_id = str(
        user_info.get("parichayId")
        or user_info.get("userName")
        or user_info.get("loginId")
        or ""
    ).strip()

    email = str(
        user_info.get("EmailId")
        or user_info.get("Email")
        or ""
    ).strip().lower()

    phone = str(
        user_info.get("mobile")
        or user_info.get("MobileNo")
        or user_info.get("mobileNo")
        or ""
    ).strip()

    first_name = str(
        user_info.get("FirstName")
        or ""
    ).strip()

    last_name = str(
        user_info.get("LastName")
        or ""
    ).strip()

    full_name = f"{first_name} {last_name}".strip()

    if not parichay_id and not email:
        return HttpResponse(
            "Parichay did not provide a usable user identifier.",
            status=400,
        )

    # The existing CustomUser implementation requires email.
    if not email:
        return HttpResponse(
            "Parichay did not provide an email address.",
            status=400,
        )

    # ---------------------------------------------------------
    # Find or create local Django user
    # ---------------------------------------------------------
    try:
        with transaction.atomic():

            user = None

            # First: stable Parichay identifier
            if parichay_id:
                user = CustomUser.objects.filter(
                    username=parichay_id
                ).first()

            # Second: existing account created through old system
            if user is None:
                import hashlib

                email_hash = hashlib.sha256(
                    email.encode()
                ).hexdigest()

                user = CustomUser.objects.filter(
                    email_hash=email_hash
                ).first()

            # -------------------------------------------------
            # New Parichay user
            # -------------------------------------------------
            if user is None:

                username = parichay_id or email

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    consent_given_at=timezone.now(),
                )

                UserProfile.objects.create(
                    user=user,
                    employee_code=f"TEMP-{user.id}",
                    name=full_name,
                    profile_updated=False,
                    approval_status="pending_admin",
                )

            # -------------------------------------------------
            # Existing local user
            # -------------------------------------------------
            else:

                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "employee_code": user.username,
                        "profile_updated": False,
                        "approval_status": "pending_admin",
                    },
                )

                # Don't overwrite employee-entered information.
                if email and not user.get_email():
                    user.set_email(email)

                if first_name and not user.first_name:
                    user.first_name = first_name

                if last_name and not user.last_name:
                    user.last_name = last_name

                user.is_active = True
                user.save()

                if phone and not profile.phone:
                    profile.phone = phone

                if full_name and not profile.name:
                    profile.name = full_name

                if email and not profile.email:
                    profile.email = email

                profile.save()

            # -------------------------------------------------
            # Save temporary login information
            # -------------------------------------------------
            request.session["parichay_id"] = parichay_id
            request.session["parichay_access_token"] = access_token
            request.session["parichay_refresh_token"] = refresh_token
            request.session["parichay_token_expires_at"] = (
                timezone.now().timestamp() + (7 * 24 * 60 * 60)
            )

            request.session.pop("code_verifier", None)
            request.session.pop("oauth_state", None)

            # -------------------------------------------------
            # Log the user into Django
            # -------------------------------------------------
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

    except Exception as e:
        return HttpResponse(
            f"Unable to create/login local user: {str(e)}",
            status=400,
        )

    return redirect("dashboard")
 
 
   
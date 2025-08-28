import os
import random
from datetime import timedelta
from urllib.parse import quote_plus

import requests
from django.shortcuts import redirect, render
from django.utils import timezone
from dotenv import load_dotenv

from .models import HighLevelToken

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
API_VERSION = "2021-07-28"
CUSTOM_FIELD_NAME = "DFS Booking Zoom Link"


def oauth_login(request):
    """Redirect user to GoHighLevel OAuth authorization URL."""
    scope = "contacts.readonly contacts.write locations/customFields.readonly locations/customFields.write"
    auth_url = (
        "https://marketplace.gohighlevel.com/oauth/chooselocation"
        f"?response_type=code"
        f"&redirect_uri={quote_plus(REDIRECT_URI)}"
        f"&client_id={CLIENT_ID}"
        f"&scope={quote_plus(scope)}"
    )
    return redirect(auth_url)


def oauth_callback(request):
    """Handle OAuth callback and store access tokens."""
    code = request.GET.get("code")
    if not code:
        return render(
            request,
            "redirect_login.html",
            {"message": "Authorization code not found, please login"},
        )

    url = "https://services.leadconnectorhq.com/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "user_type": "Location",
    }

    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()

    if response.status_code != 200 or "access_token" not in response_data:
        return render(
            request, "message.html", {"error": "Failed to authorize", "details": response_data}
        )

    HighLevelToken.objects.update_or_create(
        location_id=response_data.get("locationId"),
        defaults={
            "access_token": response_data.get("access_token"),
            "refresh_token": response_data.get("refresh_token"),
            "expires_in": response_data.get("expires_in"),
        },
    )

    request.session["location_id"] = response_data.get("locationId")
    return redirect("dashboard")


def refresh_access_token(location_id):
    """Refresh OAuth access token for a given location."""
    try:
        token_obj = HighLevelToken.objects.get(location_id=location_id)
    except HighLevelToken.DoesNotExist:
        return None

    url = "https://services.leadconnectorhq.com/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": token_obj.refresh_token,
        "redirect_uri": REDIRECT_URI,
        "user_type": "Location",
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None

    response_data = response.json()
    token_obj.access_token = response_data.get("access_token")
    token_obj.refresh_token = response_data.get("refresh_token")
    token_obj.expires_in = response_data.get("expires_in")
    token_obj.save()

    return token_obj.access_token


def is_token_expired(token_obj):
    """Check if the access token has expired."""
    expiry_time = token_obj.created_at + timedelta(seconds=token_obj.expires_in)
    return timezone.now() > expiry_time


def dashboard(request):
    """Render the dashboard with location and access token details."""
    location_id = request.session.get("location_id")
    if not location_id:
        return redirect("oauth_login")

    token_obj = HighLevelToken.objects.filter(location_id=location_id).first()
    if not token_obj:
        return redirect("oauth_login")

    access_token = (
        refresh_access_token(location_id)
        if is_token_expired(token_obj)
        else token_obj.access_token
    )

    return render(
        request,
        "dashboard.html",
        {"location_id": location_id, "access_token": access_token},
    )


def update_contact(request):
    """Update a random contact's custom field with a test value."""
    location_id = request.session.get("location_id")
    if not location_id:
        return render(request, "message.html", {"error": "Not logged in"})

    token_obj = HighLevelToken.objects.filter(location_id=location_id).first()
    if not token_obj:
        return render(request, "message.html", {"error": "No token found"})

    access_token = (
        refresh_access_token(location_id)
        if is_token_expired(token_obj)
        else token_obj.access_token
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Accept": "application/json",
    }

    contacts_response = requests.get(
        f"https://services.leadconnectorhq.com/contacts?locationId={location_id}",
        headers=headers,
    )
    if contacts_response.status_code != 200:
        return render(
            request,
            "message.html",
            {
                "error": "Failed to fetch contacts",
                "details": contacts_response.text,
            },
        )

    contacts = contacts_response.json().get("contacts", [])
    if not contacts:
        return render(request, "message.html", {"error": "No contacts found"})

    contact = random.choice(contacts)
    contact_id = contact.get("id")

    custom_fields_response = requests.get(
        f"https://services.leadconnectorhq.com/locations/{location_id}/customFields",
        headers=headers,
    )
    if custom_fields_response.status_code != 200:
        return render(
            request,
            "message.html",
            {
                "error": "Failed to fetch custom fields",
                "details": custom_fields_response.text,
            },
        )

    custom_fields = custom_fields_response.json().get("customFields", [])
    custom_field_id = next(
        (field.get("id") for field in custom_fields if field.get("name") == CUSTOM_FIELD_NAME),
        None,
    )

    if not custom_field_id:
        return render(
            request,
            "message.html",
            {"error": f"Custom field '{CUSTOM_FIELD_NAME}' not found"},
        )

    payload = {"customFields": [{"id": custom_field_id, "value": "TEST"}]}
    update_response = requests.put(
        f"https://services.leadconnectorhq.com/contacts/{contact_id}",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )

    if update_response.status_code == 200:
        return render(
            request,
            "success.html",
            {
                "contact_id": contact_id,
                "custom_field_id": custom_field_id,
                "custom_field_name": CUSTOM_FIELD_NAME,
                "update_response": update_response.json(),
            },
        )
    return render(
        request,
        "message.html",
        {"error": "Failed to update contact", "details": update_response.text},
    )
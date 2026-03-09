"""
Google OAuth 2.0 Authentication Script
This script helps you get an access token using the OAuth 2.0 flow.
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import json
import os
import pickle

# Path to your credentials file
CREDENTIALS_FILE = 'client_secret_885896162050-oad630f8k184bbov20jlbuq9vogt4ua9.apps.googleusercontent.com.json'
TOKEN_PICKLE = 'token.pickle'

# Define the scopes you need access to
# Common scopes:
# - 'https://www.googleapis.com/auth/drive.readonly' - Read-only access to Google Drive
# - 'https://www.googleapis.com/auth/drive' - Full access to Google Drive
# - 'https://www.googleapis.com/auth/gmail.readonly' - Read-only Gmail access
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
]


def get_credentials():
    """
    Get valid user credentials from storage or run OAuth flow.
    Returns credentials object.
    """
    creds = None
    
    # Check if we already have a token saved
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Starting OAuth flow...")
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
                redirect_uri='http://localhost:8080'
            )
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            print("\n" + "="*60)
            print("AUTHORIZATION REQUIRED")
            print("="*60)
            print(f"\nPlease visit this URL to authorize the application:\n")
            print(f"{auth_url}\n")
            print("="*60)
            
            # Get the authorization response
            print("\nAfter authorization, you'll be redirected to localhost:8080")
            print("Copy the ENTIRE URL from your browser address bar and paste it below:")
            auth_response = input("\nPaste the full redirect URL here: ").strip()
            
            # Fetch the token
            flow.fetch_token(authorization_response=auth_response)
            creds = flow.credentials
            
            # Save the credentials for next time
            with open(TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)
            
            print("\n✓ Credentials saved successfully!")
    
    return creds


def display_token_info(creds):
    """Display token information."""
    print("\n" + "="*60)
    print("TOKEN INFORMATION")
    print("="*60)
    print(f"\nAccess Token: {creds.token[:50]}...")
    print(f"Token Type: Bearer")
    print(f"Expires At: {creds.expiry}")
    
    if creds.refresh_token:
        print(f"Refresh Token: Available (saved for future use)")
    
    print("\n" + "="*60)
    print("You can now use this access token in your API requests!")
    print("="*60)
    
    # Example usage
    print("\nExample usage in requests:")
    print(f'''
import requests

headers = {{
    'Authorization': f'Bearer {{creds.token}}'
}}

response = requests.get(
    'https://www.googleapis.com/drive/v3/files',
    headers=headers
)
''')


def main():
    """Main function."""
    try:
        # Get credentials
        creds = get_credentials()
        
        # Display token info
        display_token_info(creds)
        
        # Return credentials for further use
        return creds
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == '__main__':
    credentials = main()

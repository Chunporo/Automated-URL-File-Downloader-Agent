"""
Google OAuth 2.0 Authentication Script
This script helps you get an access token using the OAuth 2.0 flow.
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
import pickle
from pathlib import Path

# Path to your credentials file
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / 'client_secret_885896162050-oad630f8k184bbov20jlbuq9vogt4ua9.apps.googleusercontent.com.json'
TOKEN_PICKLE = BASE_DIR / 'token.pickle'
ENV_FILE = BASE_DIR / '.env'

# Define the scopes you need access to
# Common scopes:
# - 'https://www.googleapis.com/auth/drive.readonly' - Read-only access to Google Drive
# - 'https://www.googleapis.com/auth/drive' - Full access to Google Drive
# - 'https://www.googleapis.com/auth/gmail.readonly' - Read-only Gmail access
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
]
REDIRECT_URI = 'http://localhost:8080'


def update_env_access_token(access_token: str) -> None:
    """Write GOOGLE_ACCESS_TOKEN to .env."""
    if not access_token:
        return

    lines: list[str] = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as env_file:
            lines = env_file.readlines()

    updated = False
    for index, line in enumerate(lines):
        if line.startswith('GOOGLE_ACCESS_TOKEN='):
            lines[index] = f'GOOGLE_ACCESS_TOKEN={access_token}\n'
            updated = True
            break

    if not updated:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        lines.append(f'GOOGLE_ACCESS_TOKEN={access_token}\n')

    with open(ENV_FILE, 'w', encoding='utf-8') as env_file:
        env_file.writelines(lines)

    print(f"✓ Updated {ENV_FILE} with GOOGLE_ACCESS_TOKEN")


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
            update_env_access_token(creds.token)
        else:
            print("Starting OAuth flow...")
            if REDIRECT_URI.startswith('http://localhost') or REDIRECT_URI.startswith('http://127.0.0.1'):
                os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')

            flow = Flow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
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

            update_env_access_token(creds.token)
            
            print("\n✓ Credentials saved successfully!")

    if creds and creds.valid:
        update_env_access_token(creds.token)
    
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

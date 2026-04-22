import os
from google_auth_oauthlib.flow import Flow
from config.config import GOOGLE_SCOPES, GOOGLE_REDIRECT_URI

def get_google_flow():
    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    return flow
# buatkan fungsi untuk mengambil client_id, client_secret,redirect_uri dari .env
import logging
import os

from fastapi import Request


class GoogleAuth:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    FRONTEND_URL = os.getenv("FRONTEND_URI")

    @staticmethod
    def get_client_id():
        return GoogleAuth.GOOGLE_CLIENT_ID

    @staticmethod
    def get_client_secret():
        return GoogleAuth.GOOGLE_CLIENT_SECRET

    @staticmethod
    def get_redirect_uri(request: Request):
        if request:
            try:
                request_scheme = (
                    "http" if request.url.hostname == "localhost" else "https"
                )
                redirect_uri = (
                    f"{request_scheme}://{request.url.netloc}/v1/auth/google/callback"
                )
                logging.info(f"Dynamically generated redirect URI: {redirect_uri}")
                return redirect_uri
            except Exception as e:
                logging.error(f"Error building redirect URI from request: {e}")

    @staticmethod
    def get_frontend_uri():
        return GoogleAuth.FRONTEND_URL

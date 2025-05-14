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
    def get_redirect_uri(request: Request = None):
        if request:
            try:
                base_url = str(request.base_url).rstrip("/")
                callback_path = GoogleAuth.CALLBACK_PATH.lstrip("/")
                redirect_uri = f"{base_url}/{callback_path}"
                logging.info(f"Dynamically generated redirect URI: {redirect_uri}")
                return redirect_uri
            except Exception as e:
                logging.error(f"Error building redirect URI from request: {e}")
        if GoogleAuth.GOOGLE_REDIRECT_URI:
            return GoogleAuth.GOOGLE_REDIRECT_URI

    @staticmethod
    def get_frontend_uri():
        return GoogleAuth.FRONTEND_URL

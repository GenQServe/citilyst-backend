# buatkan fungsi untuk mengambil client_id, client_secret,redirect_uri dari .env
import os


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
    def get_redirect_uri():
        return GoogleAuth.GOOGLE_REDIRECT_URI

    @staticmethod
    def get_frontend_uri():
        return GoogleAuth.FRONTEND_URL

from fastapi import HTTPException


def _handle_api_response(self, response):
    """
    Helper method to handle API response and raise HTTPException on errors.
    """
    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized, please create a new session",
        )
    elif response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Data not found",
        )
    elif response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Bad Request, please check your input",
        )
    elif response.status_code == 500:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error, please try again later",
        )
    elif not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail="Unexpected error occurred",
        )

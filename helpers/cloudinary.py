import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from helpers.config import settings


def configure_cloudinary() -> None:
    """
    Configure Cloudinary with credentials from settings or environment variables
    """
    try:
        cloud_name = getattr(
            settings, "CLOUDINARY_CLOUD_NAME", os.getenv("CLOUDINARY_CLOUD_NAME")
        )
        api_key = getattr(
            settings, "CLOUDINARY_API_KEY", os.getenv("CLOUDINARY_API_KEY")
        )
        api_secret = getattr(
            settings,
            "CLOUDINARY_API_SECRET",
            os.getenv("CLOUDINARY_API_SECRET"),
        )

        if not all([cloud_name, api_key, api_secret]):
            logging.error("Cloudinary credentials not fully configured")
            return

        cloudinary.config(
            cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True
        )
        logging.info("Cloudinary configured successfully")
    except Exception as e:
        logging.error(f"Failed to configure Cloudinary: {e}")


async def upload_image(
    file: UploadFile,
    folder: str = "uploads",
    public_id: Optional[str] = None,
    overwrite: bool = True,
    tags: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Upload image to Cloudinary

    Args:
        file: UploadFile object
        folder: Cloudinary folder to store the image
        public_id: Custom public ID for the image
        overwrite: Whether to overwrite existing image with same public_id
        tags: List of tags to add to the image

    Returns:
        Dict: Cloudinary upload response
    """
    try:
        # Check if file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="File must be an image (jpeg, png, etc)"
            )

        # Create a temporary file
        temp_file = f"temp_{file.filename}"
        try:
            # Save uploaded file to temp location
            with open(temp_file, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Upload to Cloudinary
            upload_options = {
                "folder": folder,
                "overwrite": overwrite,
                "resource_type": "image",
            }

            # Add public_id if provided
            if public_id:
                upload_options["public_id"] = public_id

            # Add tags if provided
            if tags:
                upload_options["tags"] = tags

            # Perform upload
            result = cloudinary.uploader.upload(temp_file, **upload_options)
            logging.info(
                f"Image uploaded successfully to Cloudinary: {result.get('secure_url')}"
            )

            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    except cloudinary.exceptions.Error as e:
        logging.error(f"Cloudinary upload error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cloudinary upload failed: {str(e)}"
        )
    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


async def delete_image(public_id: str) -> Dict[str, Any]:
    """
    Delete image from Cloudinary by public_id

    Args:
        public_id: Public ID of the image to delete

    Returns:
        Dict: Cloudinary delete response
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        logging.info(f"Image {public_id} deleted from Cloudinary: {result}")
        return result
    except cloudinary.exceptions.Error as e:
        logging.error(f"Cloudinary delete error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cloudinary delete failed: {str(e)}"
        )
    except Exception as e:
        logging.error(f"Error deleting image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


async def upload_file(
    file_path: str,
    folder: str = "uploads",
    public_id: Optional[str] = None,
    overwrite: bool = True,
    tags: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Upload file to Cloudinary from a local file path

    Args:
        file_path: Path to the file to upload
        folder: Cloudinary folder to store the file
        public_id: Custom public ID for the file
        overwrite: Whether to overwrite existing file with same public_id
        tags: List of tags to add to the file

    Returns:
        Dict: Cloudinary upload response
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Upload to Cloudinary
        upload_options = {
            "folder": folder,
            "overwrite": overwrite,
            "resource_type": "raw",
        }

        # Add public_id if provided
        if public_id:
            upload_options["public_id"] = public_id

        # Add tags if provided
        if tags:
            upload_options["tags"] = tags

        # Perform upload
        result = cloudinary.uploader.upload(file_path, **upload_options)
        logging.info(
            f"File uploaded successfully to Cloudinary: {result.get('secure_url')}"
        )

        return result

    except cloudinary.exceptions.Error as e:
        logging.error(f"Cloudinary upload error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cloudinary upload failed: {str(e)}"
        )
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


configure_cloudinary()

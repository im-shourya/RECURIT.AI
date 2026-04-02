"""
RECRUIT.AI — QR Code Generator Service
Creates QR codes for drive apply links.
"""

import io
import base64
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer

from app.config import get_settings

settings = get_settings()


def generate_apply_link(link_token: str) -> str:
    """Build the full public apply URL from a link token."""
    return f"{settings.FRONTEND_URL}/apply/{link_token}"


def generate_qr_base64(url: str) -> str:
    """
    Generate a QR code image for the given URL.
    Returns a base64-encoded PNG string (data URI ready).
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def generate_qr_for_drive(link_token: str) -> str:
    """Convenience: generate the full apply URL and its QR code."""
    url = generate_apply_link(link_token)
    return generate_qr_base64(url)

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...auth import (
    create_session,
    delete_session,
    get_current_user,
    is_auth_enabled,
    validate_credentials,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def api_login(request: Request):
    """Handle login API request."""
    try:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")
        remember = data.get("remember", False)

        if validate_credentials(username, password):
            session_id = create_session(username)
            response = JSONResponse(
                {
                    "success": True,
                    "redirect": "/",
                    "user": username,
                }
            )
            max_age = 86400 * 30 if remember else 86400  # 30 days or 1 day
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=False,  # Set True in production with HTTPS
                samesite="lax",
                max_age=max_age,
            )
            logger.info(f"User '{username}' logged in successfully")
            return response
        logger.warning(f"Failed login attempt for user '{username}'")
        return JSONResponse(
            {"success": False, "error": "Invalid username or password"},
            status_code=401,
        )
    except Exception as e:
        logger.exception("Login error")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500,
        )


@router.post("/logout")
async def api_logout(request: Request):
    """Handle logout API request."""
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
    response = JSONResponse({"success": True})
    response.delete_cookie("session_id")
    return response


@router.get("/status")
async def api_auth_status(request: Request):
    """Get current auth status."""
    user = get_current_user(request) if is_auth_enabled() else "admin"
    return {
        "authenticated": bool(user),
        "user": user,
        "auth_enabled": is_auth_enabled(),
    }

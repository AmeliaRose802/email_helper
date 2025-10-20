"""Settings endpoints for FastAPI Email Helper API."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import json

from backend.database.connection import db_manager

router = APIRouter()


class UserSettings(BaseModel):
    """User settings model."""
    username: Optional[str] = None
    job_context: Optional[str] = None
    newsletter_interests: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    custom_prompts: Optional[Dict[str, str]] = None
    ado_area_path: Optional[str] = None
    ado_pat: Optional[str] = None


class SettingsResponse(BaseModel):
    """Response model for settings."""
    success: bool
    message: str
    settings: Optional[UserSettings] = None


def _ensure_settings_table():
    """Ensure the user_settings table exists."""
    with db_manager.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY DEFAULT 1,
                username TEXT,
                job_context TEXT,
                newsletter_interests TEXT,
                azure_openai_endpoint TEXT,
                azure_openai_deployment TEXT,
                custom_prompts TEXT,
                ado_area_path TEXT,
                ado_pat TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default user if doesn't exist
        conn.execute("""
            INSERT OR IGNORE INTO user_settings (user_id) VALUES (1)
        """)
        conn.commit()


@router.get("/settings", response_model=UserSettings)
async def get_settings():
    """Get current user settings.
    
    Returns:
        Current user settings from database
    """
    try:
        _ensure_settings_table()
        
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT username, job_context, newsletter_interests,
                       azure_openai_endpoint, azure_openai_deployment,
                       custom_prompts, ado_area_path, ado_pat
                FROM user_settings
                WHERE user_id = 1
            """)
            row = cursor.fetchone()
            
            if row:
                custom_prompts = None
                if row[5]:  # custom_prompts field
                    try:
                        custom_prompts = json.loads(row[5])
                    except:
                        custom_prompts = {}
                
                return UserSettings(
                    username=row[0],
                    job_context=row[1],
                    newsletter_interests=row[2],
                    azure_openai_endpoint=row[3],
                    azure_openai_deployment=row[4],
                    custom_prompts=custom_prompts,
                    ado_area_path=row[6],
                    ado_pat=row[7]
                )
            else:
                return UserSettings()
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}"
        )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: UserSettings):
    """Update user settings.
    
    Args:
        settings: New settings to save
    
    Returns:
        Success status and updated settings
    """
    try:
        _ensure_settings_table()
        
        # Serialize custom_prompts to JSON
        custom_prompts_json = None
        if settings.custom_prompts:
            custom_prompts_json = json.dumps(settings.custom_prompts)
        
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE user_settings
                SET username = ?,
                    job_context = ?,
                    newsletter_interests = ?,
                    azure_openai_endpoint = ?,
                    azure_openai_deployment = ?,
                    custom_prompts = ?,
                    ado_area_path = ?,
                    ado_pat = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = 1
            """, (
                settings.username,
                settings.job_context,
                settings.newsletter_interests,
                settings.azure_openai_endpoint,
                settings.azure_openai_deployment,
                custom_prompts_json,
                settings.ado_area_path,
                settings.ado_pat
            ))
            conn.commit()
        
        return SettingsResponse(
            success=True,
            message="Settings updated successfully",
            settings=settings
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.delete("/settings", response_model=SettingsResponse)
async def reset_settings():
    """Reset user settings to defaults.
    
    Returns:
        Success status
    """
    try:
        _ensure_settings_table()
        
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE user_settings
                SET username = NULL,
                    job_context = NULL,
                    newsletter_interests = NULL,
                    azure_openai_endpoint = NULL,
                    azure_openai_deployment = NULL,
                    custom_prompts = NULL,
                    ado_area_path = NULL,
                    ado_pat = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = 1
            """)
            conn.commit()
        
        return SettingsResponse(
            success=True,
            message="Settings reset to defaults",
            settings=UserSettings()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}"
        )

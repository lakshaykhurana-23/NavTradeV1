"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from enum import StrEnum
from typing import Optional


class Model(StrEnum):
    """Enumeration of supported chat models."""
    MODEL_A = "model_a"
    MODEL_B = "model_b"
    MODEL_C = "model_c"


class Item(BaseModel):
    """Chat request model."""
    userInput: str = Field(..., description="User's input message")
    model: Model = Field(..., description="Model to use for response")
    threadId: str = Field(..., description="Conversation thread ID")


class ProcessRequest(BaseModel):
    """Document processing request model."""
    file_path: str = Field(..., description="Path to the input file")
    enable_ocr: bool = Field(default=False, description="Enable OCR for scanned PDFs")


class ProcessResponse(BaseModel):
    """Document processing response model."""
    success: bool = Field(..., description="Whether processing succeeded")
    chunks_path: Optional[str] = Field(None, description="Path to output chunks JSON")
    message: str = Field(..., description="Status message")
    file_type: Optional[str] = Field(None, description="Detected file type")

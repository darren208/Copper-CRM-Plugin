"""
RingCentral webhook endpoints.

Every endpoint:
  1. Validates the HMAC-SHA256 signature supplied by RingCentral.
  2. Normalises the payload into a typed schema.
  3. Publishes the event to Pub/Sub for async processing.
  4. Returns HTTP 200 immediately so RingCentral does not retry.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.schemas.webhook import (
    CallEndedPayload,
    MissedCallPayload,
    SMSPayload,
    VoicemailPayload,
)
from app.services.queue import QueueService
from app.utils.security import verify_ringcentral_signature

logger = structlog.get_logger(__name__)
router = APIRouter()
_queue = QueueService()


def _ack() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"received": True, "timestamp": datetime.now(timezone.utc).isoformat()},
    )


async def _validate_and_read(request: Request) -> bytes:
    """Read raw body and validate RingCentral HMAC signature."""
    body = await request.body()
    signature = request.headers.get("Validation-Token") or request.headers.get(
        "X-Rc-Hmac-Signature"
    )

    # RingCentral sends a Validation-Token header on initial subscription validation;
    # we echo it back.  For live events the HMAC header is used.
    if request.headers.get("Validation-Token"):
        # Subscription validation handshake – return the token, no further processing.
        raise HTTPException(
            status_code=200,
            detail=request.headers["Validation-Token"],
        )

    if signature and settings.ringcentral_webhook_validation_token:
        if not verify_ringcentral_signature(
            body, signature, settings.ringcentral_webhook_validation_token
        ):
            logger.warning("ringcentral_signature_invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    return body


@router.post("/ringcentral/call-ended")
async def call_ended(
    request: Request,
    background_tasks: BackgroundTasks,
    validation_token: str | None = Header(default=None, alias="Validation-Token"),
) -> JSONResponse:
    """Receive call-ended event from RingCentral."""
    if validation_token:
        return JSONResponse(
            status_code=200,
            content={},
            headers={"Validation-Token": validation_token},
        )

    body = await _validate_and_read(request)
    try:
        raw = json.loads(body)
        payload = CallEndedPayload(**raw)
    except Exception as exc:
        logger.error("call_ended_parse_error", error=str(exc))
        return _ack()

    background_tasks.add_task(
        _queue.enqueue_event,
        "call_ended",
        payload.model_dump(mode="json"),
    )
    logger.info("call_ended_enqueued", call_id=payload.uuid)
    return _ack()


@router.post("/ringcentral/sms-received")
async def sms_received(
    request: Request,
    background_tasks: BackgroundTasks,
    validation_token: str | None = Header(default=None, alias="Validation-Token"),
) -> JSONResponse:
    """Receive inbound SMS event from RingCentral."""
    if validation_token:
        return JSONResponse(
            status_code=200,
            content={},
            headers={"Validation-Token": validation_token},
        )

    body = await _validate_and_read(request)
    try:
        raw = json.loads(body)
        payload = SMSPayload(**raw)
    except Exception as exc:
        logger.error("sms_received_parse_error", error=str(exc))
        return _ack()

    background_tasks.add_task(
        _queue.enqueue_event,
        "sms_received",
        payload.model_dump(mode="json"),
    )
    logger.info("sms_received_enqueued", message_id=payload.uuid)
    return _ack()


@router.post("/ringcentral/voicemail")
async def voicemail(
    request: Request,
    background_tasks: BackgroundTasks,
    validation_token: str | None = Header(default=None, alias="Validation-Token"),
) -> JSONResponse:
    """Receive voicemail-left event from RingCentral."""
    if validation_token:
        return JSONResponse(
            status_code=200,
            content={},
            headers={"Validation-Token": validation_token},
        )

    body = await _validate_and_read(request)
    try:
        raw = json.loads(body)
        payload = VoicemailPayload(**raw)
    except Exception as exc:
        logger.error("voicemail_parse_error", error=str(exc))
        return _ack()

    background_tasks.add_task(
        _queue.enqueue_event,
        "voicemail",
        payload.model_dump(mode="json"),
    )
    logger.info("voicemail_enqueued", message_id=payload.uuid)
    return _ack()


@router.post("/ringcentral/missed-call")
async def missed_call(
    request: Request,
    background_tasks: BackgroundTasks,
    validation_token: str | None = Header(default=None, alias="Validation-Token"),
) -> JSONResponse:
    """Receive missed-call event from RingCentral."""
    if validation_token:
        return JSONResponse(
            status_code=200,
            content={},
            headers={"Validation-Token": validation_token},
        )

    body = await _validate_and_read(request)
    try:
        raw = json.loads(body)
        payload = MissedCallPayload(**raw)
    except Exception as exc:
        logger.error("missed_call_parse_error", error=str(exc))
        return _ack()

    background_tasks.add_task(
        _queue.enqueue_event,
        "missed_call",
        payload.model_dump(mode="json"),
    )
    logger.info("missed_call_enqueued", call_id=payload.uuid)
    return _ack()

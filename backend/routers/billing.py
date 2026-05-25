"""
Billing endpoints: Stripe checkout, customer portal, webhook, usage.

Plan limits (turns/month):
  free      → 100
  basic     → 600   ($10/mo)
  unlimited → 2400  ($35/mo)
"""
import os
import logging
from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId
from pydantic import BaseModel

from middleware.auth_middleware import get_current_user, get_current_user_opt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PLANS = {
    "free": {
        "turns": 100,
        "price_id": None,
        "display": "Free",
        "price_display": "$0/mo",
        "description": "100 turns/month",
    },
    "basic": {
        "turns": 600,
        "price_id": os.getenv("STRIPE_PRICE_BASIC", ""),
        "display": "Adventurer",
        "price_display": "$10/mo",
        "description": "600 turns/month",
    },
    "unlimited": {
        "turns": 2400,
        "price_id": os.getenv("STRIPE_PRICE_UNLIMITED", ""),
        "display": "Legend",
        "price_display": "$35/mo",
        "description": "2,400 turns/month",
    },
}

_db = None


def set_database(database):
    global _db
    _db = database


def get_turn_limit(plan: str) -> int:
    return PLANS.get(plan, PLANS["free"])["turns"]


async def check_and_increment_usage(user_id: str) -> dict:
    """
    Check if user has turns remaining; if yes increment and return usage info.
    Raises HTTP 402 if limit reached.
    Returns usage dict for injection into response.
    """
    period = datetime.utcnow().strftime("%Y-%m")
    user = await _db.users.find_one({"_id": ObjectId(user_id)})
    plan = user.get("plan", "free") if user else "free"
    limit = get_turn_limit(plan)

    usage = await _db.usage.find_one({"user_id": user_id, "period": period}) or {}
    used = usage.get("turn_count", 0)

    if used >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "reason": "turn_limit_reached",
                "turns_used": used,
                "turns_limit": limit,
                "plan": plan,
                "period": period,
            },
        )

    # Increment atomically
    await _db.usage.update_one(
        {"user_id": user_id, "period": period},
        {"$inc": {"turn_count": 1}, "$setOnInsert": {"user_id": user_id, "period": period}},
        upsert=True,
    )

    return {
        "plan": plan,
        "turns_used": used + 1,
        "turns_limit": limit,
        "turns_remaining": max(0, limit - used - 1),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/plans")
async def list_plans():
    return {"plans": PLANS}


@router.get("/usage")
async def get_usage(user_id: str = Depends(get_current_user)):
    period = datetime.utcnow().strftime("%Y-%m")
    user = await _db.users.find_one({"_id": ObjectId(user_id)})
    plan = user.get("plan", "free") if user else "free"
    limit = get_turn_limit(plan)

    usage = await _db.usage.find_one({"user_id": user_id, "period": period}) or {}
    used = usage.get("turn_count", 0)

    return {
        "plan": plan,
        "turns_used": used,
        "turns_limit": limit,
        "turns_remaining": max(0, limit - used),
        "period": period,
    }


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest, user_id: str = Depends(get_current_user)):
    plan = body.plan
    if plan not in PLANS or not PLANS[plan]["price_id"]:
        raise HTTPException(400, "Invalid plan or Stripe not configured")

    user = await _db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "User not found")

    try:
        session = stripe.checkout.Session.create(
            customer_email=user["email"],
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": PLANS[plan]["price_id"], "quantity": 1}],
            metadata={"user_id": user_id, "plan": plan},
            success_url=f"{FRONTEND_URL}/#/billing/success?plan={plan}",
            cancel_url=f"{FRONTEND_URL}/#/pricing",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(500, "Payment provider error")


@router.post("/portal")
async def customer_portal(user_id: str = Depends(get_current_user)):
    sub = await _db.subscriptions.find_one({"user_id": user_id, "status": "active"})
    if not sub:
        raise HTTPException(404, "No active subscription found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=sub["stripe_customer_id"],
            return_url=f"{FRONTEND_URL}/#/",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(500, "Payment provider error")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        if os.getenv("ENV", "development") == "production":
            raise HTTPException(400, "Webhook not configured")
        # Dev-only: accept unsigned webhook for local Stripe CLI testing
        import json as _json
        event = _json.loads(payload)
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(400, "Invalid webhook signature")

    etype = event.get("type", "")
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        user_id = obj["metadata"]["user_id"]
        plan = obj["metadata"]["plan"]
        await _db.subscriptions.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "stripe_customer_id": obj["customer"],
                "stripe_subscription_id": obj["subscription"],
                "plan": plan,
                "status": "active",
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )
        await _db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"plan": plan}}
        )
        logger.info(f"Subscription activated: user={user_id} plan={plan}")

    elif etype in ("customer.subscription.deleted", "invoice.payment_failed"):
        sub_id = obj.get("id") or obj.get("subscription")
        sub = await _db.subscriptions.find_one({"stripe_subscription_id": sub_id})
        if sub:
            await _db.users.update_one(
                {"_id": ObjectId(sub["user_id"])}, {"$set": {"plan": "free"}}
            )
            await _db.subscriptions.update_one(
                {"stripe_subscription_id": sub_id},
                {"$set": {"plan": "free", "status": "cancelled", "updated_at": datetime.utcnow()}},
            )
            logger.info(f"Subscription cancelled: user={sub['user_id']}")

    return {"received": True}

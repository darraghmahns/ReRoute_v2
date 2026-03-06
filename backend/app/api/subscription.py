import logging
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import (
    CheckoutSessionResponse,
    PortalSessionResponse,
    SubscriptionResponse,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_API_KEY

router = APIRouter(prefix="/subscription", tags=["subscription"])


def _get_or_create_subscription(user: User, db: Session) -> Subscription:
    """Get or create a free-tier subscription for the user."""
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub:
        sub = Subscription(user_id=user.id, tier="free", status="active")
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


@router.get("/status", response_model=SubscriptionResponse)
def get_status(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get the current user's subscription status."""
    sub = _get_or_create_subscription(current_user, db)
    return sub


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for upgrading to Pro."""
    if settings.STRIPE_API_KEY == "changeme":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    sub = _get_or_create_subscription(current_user, db)

    # Create or retrieve Stripe customer
    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": str(current_user.id)},
        )
        sub.stripe_customer_id = customer.id
        db.commit()

    success_url = f"{settings.FRONTEND_URL}/profile?subscription=success"
    cancel_url = f"{settings.FRONTEND_URL}/profile"
    print(f"[CHECKOUT] success_url={success_url} cancel_url={cancel_url}", flush=True)

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return CheckoutSessionResponse(url=session.url)


@router.post("/portal", response_model=PortalSessionResponse)
def create_portal(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Create a Stripe Customer Portal session for managing subscription."""
    if settings.STRIPE_API_KEY == "changeme":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    portal_session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/profile",
    )

    return PortalSessionResponse(url=portal_session.url)


@router.post("/webhooks", status_code=200)
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        sub = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()

        if sub is None:
            logger.warning(f"checkout.session.completed: no subscription found for customer={customer_id}")
        elif subscription_id:
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            sub.stripe_subscription_id = subscription_id
            sub.tier = "pro"
            sub.status = "active"
            sub.current_period_end = datetime.utcfromtimestamp(
                stripe_sub["current_period_end"]
            )
            db.commit()
            logger.info(f"Upgraded user subscription to Pro: customer={customer_id}")

    elif event_type == "customer.subscription.updated":
        subscription_id = data.get("id")
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if sub:
            sub.status = data.get("status", sub.status)
            period_end = data.get("current_period_end")
            if period_end:
                sub.current_period_end = datetime.utcfromtimestamp(period_end)
            db.commit()
            logger.info(f"Updated subscription status: {sub.status}")

    elif event_type == "customer.subscription.deleted":
        subscription_id = data.get("id")
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if sub:
            sub.tier = "free"
            sub.status = "canceled"
            sub.stripe_subscription_id = None
            sub.current_period_end = None
            db.commit()
            logger.info(f"Downgraded subscription to free: customer={sub.stripe_customer_id}")

    return {"received": True}

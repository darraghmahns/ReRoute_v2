from fastapi import APIRouter

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/status")
def status():
    """Current subscription status"""
    return {"message": "status placeholder"}

@router.post("/checkout")
def checkout():
    """Create Stripe checkout"""
    return {"message": "checkout placeholder"}

@router.post("/portal")
def portal():
    """Customer portal access"""
    return {"message": "portal placeholder"}

@router.post("/webhooks")
def webhooks():
    """Stripe webhooks"""
    return {"message": "webhooks placeholder"} 
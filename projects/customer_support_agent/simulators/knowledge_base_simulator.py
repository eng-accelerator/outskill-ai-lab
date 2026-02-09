"""Knowledge base simulator.

Generates FAQ entries and technical documentation articles for
product troubleshooting, billing help, and general support.
"""

import logging

from customer_support_agent.models.support import KBArticle

logger = logging.getLogger(__name__)


def generate_knowledge_base() -> list[KBArticle]:
    """Generate a comprehensive knowledge base with FAQ and documentation articles.

    Creates articles covering orders, billing, technical issues, account management,
    and general topics for the support agent to reference.

    Returns:
        list[KBArticle]: List of knowledge base articles.
    """
    articles = [
        # Order-related articles
        KBArticle(
            article_id="KB-001",
            title="How to Track Your Order",
            content=(
                "To track your order: 1) Log into your account. 2) Go to 'My Orders'. "
                "3) Click on the order number. 4) View the tracking information. "
                "If your tracking hasn't updated in 48+ hours, the carrier may be "
                "experiencing delays. Contact support if no update after 5 business days."
            ),
            category="orders",
            tags=["tracking", "order", "shipping", "delivery"],
            helpful_count=342,
        ),
        KBArticle(
            article_id="KB-002",
            title="Return and Refund Policy",
            content=(
                "We accept returns within 30 days of delivery for most items. "
                "Defective items can be returned within 90 days. To initiate a return: "
                "1) Contact support with your order number. 2) Describe the issue. "
                "3) We'll provide a prepaid return label. 4) Ship the item back. "
                "Refunds are processed within 5-7 business days after we receive the item. "
                "Original shipping costs are non-refundable unless the return is due to our error."
            ),
            category="orders",
            tags=["return", "refund", "policy", "defective"],
            helpful_count=567,
        ),
        KBArticle(
            article_id="KB-003",
            title="Order Cancellation",
            content=(
                "Orders can be cancelled within 1 hour of placement if not yet processing. "
                "To cancel: Go to 'My Orders' > select order > click 'Cancel Order'. "
                "If the order is already processing or shipped, you'll need to wait for "
                "delivery and then initiate a return. Subscription orders can be cancelled "
                "before the next billing cycle."
            ),
            category="orders",
            tags=["cancel", "order", "cancellation"],
            helpful_count=189,
        ),
        KBArticle(
            article_id="KB-004",
            title="Shipping Delays and Lost Packages",
            content=(
                "If your package hasn't arrived by the estimated delivery date: "
                "1) Check tracking for the latest status. "
                "2) Wait 2 additional business days (carriers sometimes run behind). "
                "3) If still no update after 5 business days, contact us. "
                "We can file a claim with the carrier or send a replacement. "
                "For packages marked 'delivered' but not received, check with neighbors "
                "and your building office. If still missing after 48 hours, contact us."
            ),
            category="orders",
            tags=["shipping", "delay", "lost", "package", "delivery"],
            helpful_count=423,
        ),

        # Billing-related articles
        KBArticle(
            article_id="KB-010",
            title="Understanding Your Subscription Plans",
            content=(
                "We offer 4 subscription tiers: "
                "Free ($0/mo) - Basic features, 5 projects. "
                "Starter ($9.99/mo) - 25 projects, email support. "
                "Professional ($29.99/mo) - Unlimited projects, priority support, API access. "
                "Enterprise ($99.99/mo) - Everything in Pro + dedicated account manager, SLA, SSO. "
                "You can upgrade or downgrade at any time. Changes take effect at the next billing cycle."
            ),
            category="billing",
            tags=["subscription", "plan", "pricing", "upgrade", "downgrade"],
            helpful_count=891,
        ),
        KBArticle(
            article_id="KB-011",
            title="How to Change Your Subscription Plan",
            content=(
                "To change your plan: 1) Go to Account Settings > Subscription. "
                "2) Click 'Change Plan'. 3) Select your new plan. 4) Confirm. "
                "Upgrades take effect immediately with prorated billing. "
                "Downgrades take effect at the start of the next billing cycle. "
                "You'll retain access to current plan features until the cycle ends."
            ),
            category="billing",
            tags=["subscription", "change", "upgrade", "downgrade"],
            helpful_count=234,
        ),
        KBArticle(
            article_id="KB-012",
            title="Payment Issues and Failed Transactions",
            content=(
                "Common payment failure reasons: "
                "1) Insufficient funds. 2) Expired card. 3) Bank security block. "
                "4) Incorrect billing address. "
                "To resolve: Update your payment method in Account Settings > Payment. "
                "If the issue persists, contact your bank to authorize the transaction. "
                "We retry failed payments after 24 hours, then again after 72 hours."
            ),
            category="billing",
            tags=["payment", "failed", "transaction", "card", "billing"],
            helpful_count=312,
        ),
        KBArticle(
            article_id="KB-013",
            title="Requesting a Refund",
            content=(
                "Refunds for subscription charges: You can request a refund within 14 days "
                "of a charge if you haven't used the service significantly. "
                "Refunds for product purchases: Follow our return policy (30-day window). "
                "Double charges: Contact support immediately with payment IDs. "
                "We'll investigate and process the refund within 3-5 business days. "
                "Refunds appear on your statement within 5-10 business days."
            ),
            category="billing",
            tags=["refund", "billing", "charge", "double-charge"],
            helpful_count=445,
        ),

        # Technical support articles
        KBArticle(
            article_id="KB-020",
            title="Troubleshooting Login Issues",
            content=(
                "Can't log in? Try these steps: "
                "1) Clear browser cache and cookies. "
                "2) Try incognito/private browsing mode. "
                "3) Reset your password via 'Forgot Password'. "
                "4) Check if your account email is correct. "
                "5) Disable browser extensions that may interfere. "
                "6) Try a different browser. "
                "If none of these work, your account may be locked after 5 failed attempts. "
                "Contact support to unlock it."
            ),
            category="troubleshooting",
            tags=["login", "password", "access", "locked", "account"],
            helpful_count=1023,
        ),
        KBArticle(
            article_id="KB-021",
            title="API Access and Authentication",
            content=(
                "API access requires Professional or Enterprise plan. "
                "To get your API key: Account Settings > API > Generate Key. "
                "Common API issues: "
                "1) 401 Unauthorized - Check your API key is valid. "
                "2) 429 Rate Limited - You've exceeded 1000 requests/hour. "
                "3) 403 Forbidden - Your plan may not include this endpoint. "
                "API documentation: docs.ourservice.com/api"
            ),
            category="technical",
            tags=["api", "authentication", "key", "rate-limit"],
            helpful_count=567,
        ),
        KBArticle(
            article_id="KB-022",
            title="Known Issues and System Status",
            content=(
                "Current known issues: "
                "1) Dashboard loading slowly for accounts with 100+ projects (fix ETA: this week). "
                "2) Email notifications may be delayed up to 30 minutes. "
                "3) Mobile app v3.2 crash on Android 14 (update to v3.3 to fix). "
                "Check real-time system status at status.ourservice.com. "
                "Subscribe to status updates via email or SMS."
            ),
            category="technical",
            tags=["known-issues", "status", "bug", "outage"],
            helpful_count=234,
        ),
        KBArticle(
            article_id="KB-023",
            title="Product Feature Guide: Smart Watch Pro X",
            content=(
                "Smart Watch Pro X setup: "
                "1) Charge for 2 hours before first use. "
                "2) Download the companion app (iOS/Android). "
                "3) Enable Bluetooth and pair. "
                "Common issues: "
                "- Screen not responding: Hold power button for 10 seconds to force restart. "
                "- Dead pixels: Contact support for warranty replacement (1-year warranty). "
                "- Battery draining fast: Disable always-on display in Settings > Display."
            ),
            category="troubleshooting",
            tags=["smart-watch", "setup", "screen", "battery", "warranty"],
            helpful_count=178,
        ),

        # Account management articles
        KBArticle(
            article_id="KB-030",
            title="Account Security Best Practices",
            content=(
                "Protect your account: "
                "1) Use a strong, unique password (12+ characters). "
                "2) Enable two-factor authentication (2FA). "
                "3) Review active sessions regularly. "
                "4) Don't share your API keys. "
                "5) Update your recovery email and phone number. "
                "If you suspect unauthorized access, change your password immediately "
                "and contact support."
            ),
            category="account",
            tags=["security", "password", "2fa", "account"],
            helpful_count=345,
        ),
        KBArticle(
            article_id="KB-031",
            title="How to Update Account Information",
            content=(
                "To update your account: Go to Account Settings. "
                "You can change: Name, email, phone, password, payment method, "
                "notification preferences, and communication preferences. "
                "Email changes require verification. "
                "Contact support to change your account's primary email if you no longer "
                "have access to the current one."
            ),
            category="account",
            tags=["account", "update", "email", "settings"],
            helpful_count=156,
        ),

        # General articles
        KBArticle(
            article_id="KB-040",
            title="Contact Support Options",
            content=(
                "Ways to reach us: "
                "1) Live Chat - Available 24/7 (fastest response). "
                "2) Email - support@ourservice.com (response within 4 hours). "
                "3) Phone - +1-800-555-0199 (Mon-Fri 8AM-8PM EST). "
                "4) Help Center - help.ourservice.com (self-service). "
                "Priority support available for Professional and Enterprise customers."
            ),
            category="general",
            tags=["contact", "support", "help", "chat", "phone"],
            helpful_count=678,
        ),
    ]

    logger.info("Generated %d knowledge base articles", len(articles))
    return articles

"""Customer profile simulator.

Generates realistic customer profiles with varied tiers, spending history,
and account characteristics for use in support scenarios.
"""

import logging

from customer_support_agent.models.customer import CustomerProfile

logger = logging.getLogger(__name__)


def generate_customer_profiles() -> list[CustomerProfile]:
    """Generate a diverse set of customer profiles.

    Creates 10 customer profiles spanning all loyalty tiers with
    realistic spending patterns and account histories.

    Returns:
        list[CustomerProfile]: List of simulated customer profiles.
    """
    profiles = [
        CustomerProfile(
            customer_id="CUST-001",
            name="Sarah Johnson",
            email="sarah.johnson@email.com",
            phone="+1-555-0101",
            tier="platinum",
            account_age_days=1825,
            total_orders=147,
            total_spent=28450.00,
            preferred_contact="email",
            notes="VIP customer. Long-standing account. Previously escalated billing issue resolved satisfactorily.",
        ),
        CustomerProfile(
            customer_id="CUST-002",
            name="Marcus Chen",
            email="marcus.chen@email.com",
            phone="+1-555-0102",
            tier="gold",
            account_age_days=730,
            total_orders=52,
            total_spent=8920.00,
            preferred_contact="chat",
            notes="Active user. Prefers quick resolutions. Has used technical support 3 times.",
        ),
        CustomerProfile(
            customer_id="CUST-003",
            name="Emily Rodriguez",
            email="emily.rod@email.com",
            phone="+1-555-0103",
            tier="silver",
            account_age_days=365,
            total_orders=18,
            total_spent=2340.00,
            preferred_contact="phone",
            notes="New to premium features. Recently upgraded from free plan.",
        ),
        CustomerProfile(
            customer_id="CUST-004",
            name="James Wilson",
            email="j.wilson@email.com",
            phone="+1-555-0104",
            tier="bronze",
            account_age_days=90,
            total_orders=3,
            total_spent=245.00,
            preferred_contact="email",
            notes="New customer. First-time buyer.",
        ),
        CustomerProfile(
            customer_id="CUST-005",
            name="Priya Patel",
            email="priya.patel@email.com",
            phone="+1-555-0105",
            tier="gold",
            account_age_days=1095,
            total_orders=89,
            total_spent=15670.00,
            preferred_contact="chat",
            notes="Enterprise customer. Multiple team members on account.",
        ),
        CustomerProfile(
            customer_id="CUST-006",
            name="David Kim",
            email="d.kim@email.com",
            phone="+1-555-0106",
            tier="silver",
            account_age_days=540,
            total_orders=24,
            total_spent=3890.00,
            preferred_contact="email",
            notes="Developer. Uses API extensively. Had API key issues last month.",
        ),
        CustomerProfile(
            customer_id="CUST-007",
            name="Lisa Thompson",
            email="lisa.t@email.com",
            phone="+1-555-0107",
            tier="platinum",
            account_age_days=2190,
            total_orders=203,
            total_spent=42100.00,
            preferred_contact="phone",
            notes="Top-tier customer. Account manager assigned. White-glove service required.",
        ),
        CustomerProfile(
            customer_id="CUST-008",
            name="Ahmed Hassan",
            email="a.hassan@email.com",
            phone="+1-555-0108",
            tier="bronze",
            account_age_days=30,
            total_orders=1,
            total_spent=79.99,
            preferred_contact="chat",
            notes="Brand new customer. First order just placed.",
        ),
        CustomerProfile(
            customer_id="CUST-009",
            name="Rachel Green",
            email="r.green@email.com",
            phone="+1-555-0109",
            tier="gold",
            account_age_days=912,
            total_orders=67,
            total_spent=11250.00,
            preferred_contact="email",
            notes="Frequent buyer. Participates in beta program. Provides detailed feedback.",
        ),
        CustomerProfile(
            customer_id="CUST-010",
            name="Carlos Mendez",
            email="c.mendez@email.com",
            phone="+1-555-0110",
            tier="silver",
            account_age_days=450,
            total_orders=15,
            total_spent=2100.00,
            preferred_contact="sms",
            notes="International customer. Timezone: UTC-6. Prefers Spanish but accepts English.",
        ),
    ]

    logger.info("Generated %d customer profiles", len(profiles))
    return profiles


def get_customer_by_id(
    profiles: list[CustomerProfile], customer_id: str
) -> CustomerProfile | None:
    """Look up a customer profile by ID.

    Args:
        profiles: List of customer profiles to search.
        customer_id: The customer ID to find.

    Returns:
        CustomerProfile | None: The matching profile, or None if not found.
    """
    for profile in profiles:
        if profile.customer_id == customer_id:
            return profile
    return None

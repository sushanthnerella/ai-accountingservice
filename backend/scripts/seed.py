import asyncio
import uuid
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.services.organization_service import OrganizationService
from backend.app.services.client_service import ClientService
from backend.app.models.organization import OrganizationType
from backend.app.models.client_business import BusinessType

async def seed_data():
    print("Seeding initial realistic Indian accounting test fixtures...")
    async with AsyncSessionLocal() as session:
        # 1. Freelancer Persona
        try:
            freelancer_user = await AuthService.register_user(
                session,
                email="rohan.developer@example.in",
                password="Password123!",
                full_name="Rohan Verma",
                phone="+919811122233"
            )
            freelancer_org = await OrganizationService.create_organization(
                session,
                user=freelancer_user,
                name="Rohan Verma Consulting",
                slug="rohan-consulting",
                org_type=OrganizationType.FREELANCER
            )
            await ClientService.create_client_business(
                session,
                organization_id=freelancer_org.id,
                user_id=freelancer_user.id,
                legal_name="Rohan Verma",
                trade_name="RV Tech Solutions",
                business_type=BusinessType.INDIVIDUAL,
                pan="ABCDE1234F",
                gstin="27ABCDE1234F1Z5",
                state_code="27",
                is_composition_scheme=False
            )
            print("Freelancer persona seeded.")
        except Exception as e:
            print(f"Skipping freelancer seed or exists: {e}")

        # 2. CA Firm Persona
        try:
            ca_user = await AuthService.register_user(
                session,
                email="priya.sharma@capractice.in",
                password="Password123!",
                full_name="CA Priya Sharma",
                phone="+919877788899"
            )
            ca_org = await OrganizationService.create_organization(
                session,
                user=ca_user,
                name="Priya Sharma & Associates Chartered Accountants",
                slug="priya-sharma-ca",
                org_type=OrganizationType.CA_FIRM
            )
            # Add 2 Client businesses under CA firm
            await ClientService.create_client_business(
                session,
                organization_id=ca_org.id,
                user_id=ca_user.id,
                legal_name="Apex Global Tech Solutions Pvt Ltd",
                trade_name="Apex Global",
                business_type=BusinessType.PVT_LTD,
                pan="BCDEF2345G",
                gstin="27BCDEF2345G1Z3",
                state_code="27",
                is_composition_scheme=False
            )
            await ClientService.create_client_business(
                session,
                organization_id=ca_org.id,
                user_id=ca_user.id,
                legal_name="Bharat Retail Distributors LLP",
                trade_name="Bharat Retail",
                business_type=BusinessType.LLP,
                pan="CDEFG3456H",
                gstin="29CDEFG3456H1Z1",
                state_code="29",
                is_composition_scheme=True
            )
            print("CA Firm persona with multiple client businesses seeded.")
        except Exception as e:
            print(f"Skipping CA firm seed or exists: {e}")

        await session.commit()
    print("Database seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())

from sqlmodel import SQLModel, Field, Relationship

class TenantUserLink(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    tenant_id: int | None = Field(default=None, foreign_key="tenant.id", primary_key=True)

class Tenant(SQLModel, table= True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    users: TenantUserLink = Relationship(link_model=TenantUserLink)
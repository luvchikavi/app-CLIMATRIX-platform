"""
PCF API — product catalog, BOM, supplier PCFs, footprint compute + PACT export.

Teaser semantics match the platform rule: modeling and computing stay open
(the wow), exports are gated by the existing entitlement lane (trial = 402,
Report Pass = year-licensed).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field as PydField
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_session
from app.models.core import Organization, ReportingPeriod, User
from app.models.product import (
    FootprintStatus,
    Product,
    ProductFootprint,
    ProductInput,
    ProductInputType,
    SupplierPCF,
)
from app.services.entitlements import (
    ensure_period_year_licensed,
    get_entitlement,
    require_report_generation,
)
from app.services import lca as lca_service
from app.services.pcf import (
    build_pact_json,
    compute_footprint,
    parse_supplier_pact_json,
)

router = APIRouter()

DECLARED_UNITS = {
    "kilogram",
    "tonne",
    "liter",
    "cubic_meter",
    "kilowatt_hour",
    "megajoule",
    "ton_kilometer",
    "square_meter",
    "piece",
}

INPUT_TYPES = {t.value for t in ProductInputType}
# Full EN 15804 module vocabulary (LCA-lite). Only A1-A3 lines enter the
# cradle-to-gate PCF total; the rest live in the LCA matrix.
EN15804_MODULES = set(lca_service.EN15804_MODULES)


# ---------------------------------------------------------------- schemas


class ProductCreate(BaseModel):
    name: str = PydField(min_length=1, max_length=255)
    sku: Optional[str] = PydField(default=None, max_length=100)
    description: Optional[str] = PydField(default=None, max_length=1000)
    declared_unit: str = "kilogram"
    declared_unit_amount: Decimal = Decimal("1")
    cn_code: Optional[str] = PydField(default=None, max_length=10)
    category: Optional[str] = PydField(default=None, max_length=100)


class ProductUpdate(BaseModel):
    name: Optional[str] = PydField(default=None, min_length=1, max_length=255)
    sku: Optional[str] = PydField(default=None, max_length=100)
    description: Optional[str] = PydField(default=None, max_length=1000)
    declared_unit: Optional[str] = None
    declared_unit_amount: Optional[Decimal] = None
    cn_code: Optional[str] = PydField(default=None, max_length=10)
    category: Optional[str] = PydField(default=None, max_length=100)
    is_active: Optional[bool] = None


class InputCreate(BaseModel):
    input_type: str = ProductInputType.PURCHASED_MATERIAL.value
    name: str = PydField(min_length=1, max_length=255)
    quantity_per_unit: Decimal
    unit: str = PydField(min_length=1, max_length=50)
    activity_key: Optional[str] = PydField(default=None, max_length=100)
    supplier_pcf_id: Optional[UUID] = None
    category_code: Optional[str] = PydField(default=None, max_length=10)
    scope: Optional[int] = PydField(default=None, ge=1, le=3)
    region: Optional[str] = PydField(default=None, max_length=50)
    en15804_module: Optional[str] = None
    notes: Optional[str] = PydField(default=None, max_length=500)
    sort_order: int = 0


class InputUpdate(BaseModel):
    input_type: Optional[str] = None
    name: Optional[str] = PydField(default=None, min_length=1, max_length=255)
    quantity_per_unit: Optional[Decimal] = None
    unit: Optional[str] = PydField(default=None, min_length=1, max_length=50)
    activity_key: Optional[str] = PydField(default=None, max_length=100)
    supplier_pcf_id: Optional[UUID] = None
    category_code: Optional[str] = PydField(default=None, max_length=10)
    scope: Optional[int] = PydField(default=None, ge=1, le=3)
    region: Optional[str] = PydField(default=None, max_length=50)
    en15804_module: Optional[str] = None
    notes: Optional[str] = PydField(default=None, max_length=500)
    sort_order: Optional[int] = None


class SupplierPCFCreate(BaseModel):
    supplier_name: str = PydField(min_length=1, max_length=255)
    product_name: str = PydField(min_length=1, max_length=255)
    pcf_value: Decimal
    unit: str = PydField(min_length=1, max_length=50)
    boundary: str = "cradle_to_gate"
    primary_data_share: Optional[float] = PydField(default=None, ge=0, le=100)
    valid_until: Optional[date] = None


class PactUpload(BaseModel):
    payload: dict


class InputResponse(BaseModel):
    id: UUID
    input_type: str
    name: str
    quantity_per_unit: Decimal
    unit: str
    activity_key: Optional[str]
    supplier_pcf_id: Optional[UUID]
    category_code: Optional[str]
    scope: Optional[int]
    region: Optional[str]
    en15804_module: str
    notes: Optional[str]
    sort_order: int


class FootprintResponse(BaseModel):
    id: UUID
    product_id: UUID
    reporting_period_id: UUID
    declared_unit: str
    declared_unit_amount: Decimal
    boundary: str
    total_kgco2e_per_unit: Decimal
    fossil_kgco2e_per_unit: Optional[Decimal]
    biogenic_kgco2e_per_unit: Optional[Decimal]
    primary_data_share: Optional[float]
    stage_breakdown: Optional[dict]
    line_items: Optional[List[dict]]
    warnings: Optional[List[str]]
    methodology: Optional[dict]
    lca_results: Optional[dict] = None
    status: str
    finalized_at: Optional[datetime]
    created_at: datetime


class ProductResponse(BaseModel):
    id: UUID
    name: str
    sku: Optional[str]
    description: Optional[str]
    declared_unit: str
    declared_unit_amount: Decimal
    cn_code: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    input_count: int = 0
    latest_footprint: Optional[FootprintResponse] = None


class ProductDetailResponse(ProductResponse):
    inputs: List[InputResponse] = []
    footprints: List[FootprintResponse] = []


class SupplierPCFResponse(BaseModel):
    id: UUID
    supplier_name: str
    product_name: str
    pcf_value: Decimal
    unit: str
    boundary: str
    primary_data_share: Optional[float]
    valid_until: Optional[date]
    pact_pf_id: Optional[str]
    source: str
    status: str
    created_at: datetime


# ---------------------------------------------------------------- helpers


async def _get_product(
    product_id: UUID, session: AsyncSession, current_user: User
) -> Product:
    product = await session.get(Product, product_id)
    if product is None or product.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def _get_inputs(session: AsyncSession, product_id: UUID) -> list[ProductInput]:
    result = await session.execute(
        select(ProductInput)
        .where(ProductInput.product_id == product_id)
        .order_by(ProductInput.sort_order, ProductInput.created_at)
    )
    return list(result.scalars().all())


def _validate_declared_unit(unit: str) -> None:
    if unit not in DECLARED_UNITS:
        raise HTTPException(
            status_code=422,
            detail=f"declared_unit must be one of: {', '.join(sorted(DECLARED_UNITS))}",
        )


async def _resolve_supplier_pcf_ref(
    session: AsyncSession, current_user: User, data
) -> None:
    """Cross-tenant guard: a BOM line may only reference the org's own
    supplier PCFs (the site_id lesson from the grid-region build)."""
    if data.supplier_pcf_id is None:
        return
    spcf = await session.get(SupplierPCF, data.supplier_pcf_id)
    if spcf is None or spcf.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Supplier PCF not found")


def _input_payload(data, exclude_unset: bool = False) -> dict:
    payload = data.model_dump(exclude_unset=exclude_unset)
    input_type = payload.get("input_type")
    if input_type is not None and input_type not in INPUT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"input_type must be one of: {', '.join(sorted(INPUT_TYPES))}",
        )
    module = payload.get("en15804_module")
    if module is not None and module not in EN15804_MODULES:
        raise HTTPException(
            status_code=422,
            detail=f"en15804_module must be one of: {', '.join(sorted(EN15804_MODULES))}",
        )
    return payload


# ---------------------------------------------------------------- products


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    org_id = current_user.organization_id
    products = (
        (
            await session.execute(
                select(Product)
                .where(Product.organization_id == org_id)
                .order_by(Product.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    inputs = (
        (
            await session.execute(
                select(ProductInput).where(ProductInput.organization_id == org_id)
            )
        )
        .scalars()
        .all()
    )
    footprints = (
        (
            await session.execute(
                select(ProductFootprint)
                .where(ProductFootprint.organization_id == org_id)
                .order_by(ProductFootprint.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    counts: dict[UUID, int] = {}
    for i in inputs:
        counts[i.product_id] = counts.get(i.product_id, 0) + 1
    latest: dict[UUID, ProductFootprint] = {}
    for f in footprints:  # ordered desc — first seen is the latest
        latest.setdefault(f.product_id, f)
    return [
        ProductResponse(
            **p.model_dump(),
            input_count=counts.get(p.id, 0),
            latest_footprint=(
                FootprintResponse(**latest[p.id].model_dump())
                if p.id in latest
                else None
            ),
        )
        for p in products
    ]


@router.post("/products", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _validate_declared_unit(data.declared_unit)
    product = Product(
        **data.model_dump(),
        organization_id=current_user.organization_id,
        created_by=current_user.id,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return ProductResponse(**product.model_dump())


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await _get_product(product_id, session, current_user)
    inputs = await _get_inputs(session, product.id)
    footprints = (
        (
            await session.execute(
                select(ProductFootprint)
                .where(ProductFootprint.product_id == product.id)
                .order_by(ProductFootprint.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    fps = [FootprintResponse(**f.model_dump()) for f in footprints]
    return ProductDetailResponse(
        **product.model_dump(),
        input_count=len(inputs),
        latest_footprint=fps[0] if fps else None,
        inputs=[InputResponse(**i.model_dump()) for i in inputs],
        footprints=fps,
    )


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await _get_product(product_id, session, current_user)
    payload = data.model_dump(exclude_unset=True)
    if "declared_unit" in payload:
        _validate_declared_unit(payload["declared_unit"])
    for key, value in payload.items():
        setattr(product, key, value)
    product.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(product)
    return ProductResponse(**product.model_dump())


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await _get_product(product_id, session, current_user)
    footprints = (
        (
            await session.execute(
                select(ProductFootprint).where(
                    ProductFootprint.product_id == product.id
                )
            )
        )
        .scalars()
        .all()
    )
    if any(f.status == FootprintStatus.FINAL.value for f in footprints):
        raise HTTPException(
            status_code=409,
            detail="Product has finalized footprints — deactivate it instead "
            "(PATCH is_active=false) to preserve the audit trail",
        )
    # Explicit ordered bulk deletes: children before parent. ORM-level
    # session.delete() in one flush has no relationship metadata here, so
    # PostgreSQL saw DELETE products before product_inputs → FK violation
    # (SQLite tests don't enforce FKs, which is how this shipped).
    await session.execute(
        sa_delete(ProductFootprint).where(ProductFootprint.product_id == product.id)
    )
    await session.execute(
        sa_delete(ProductInput).where(ProductInput.product_id == product.id)
    )
    await session.delete(product)
    await session.commit()
    return {"ok": True}


# ---------------------------------------------------------------- BOM lines


@router.post("/products/{product_id}/inputs", response_model=InputResponse)
async def create_input(
    product_id: UUID,
    data: InputCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    product = await _get_product(product_id, session, current_user)
    payload = _input_payload(data)
    await _resolve_supplier_pcf_ref(session, current_user, data)
    if payload.get("en15804_module") is None:
        from app.services.pcf import TYPE_MODULE

        payload["en15804_module"] = TYPE_MODULE.get(payload["input_type"], "A1")
    line = ProductInput(
        **payload,
        organization_id=current_user.organization_id,
        product_id=product.id,
    )
    session.add(line)
    await session.commit()
    await session.refresh(line)
    return InputResponse(**line.model_dump())


@router.patch("/products/{product_id}/inputs/{input_id}", response_model=InputResponse)
async def update_input(
    product_id: UUID,
    input_id: UUID,
    data: InputUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _get_product(product_id, session, current_user)
    line = await session.get(ProductInput, input_id)
    if (
        line is None
        or line.product_id != product_id
        or line.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=404, detail="BOM line not found")
    payload = _input_payload(data, exclude_unset=True)
    await _resolve_supplier_pcf_ref(session, current_user, data)
    for key, value in payload.items():
        setattr(line, key, value)
    line.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(line)
    return InputResponse(**line.model_dump())


@router.delete("/products/{product_id}/inputs/{input_id}")
async def delete_input(
    product_id: UUID,
    input_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _get_product(product_id, session, current_user)
    line = await session.get(ProductInput, input_id)
    if (
        line is None
        or line.product_id != product_id
        or line.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=404, detail="BOM line not found")
    await session.delete(line)
    await session.commit()
    return {"ok": True}


# ---------------------------------------------------------------- footprints


@router.post("/products/{product_id}/footprint", response_model=FootprintResponse)
async def compute_product_footprint(
    product_id: UUID,
    period_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Compute + store a draft footprint. Open to trial (compute is the wow);
    only exports are gated."""
    product = await _get_product(product_id, session, current_user)
    period = await session.get(ReportingPeriod, period_id)
    if period is None or period.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    inputs = await _get_inputs(session, product.id)
    if not inputs:
        raise HTTPException(
            status_code=422, detail="Add at least one BOM line before computing"
        )
    org = await session.get(Organization, current_user.organization_id)
    spcf_ids = [i.supplier_pcf_id for i in inputs if i.supplier_pcf_id]
    supplier_pcfs = {}
    if spcf_ids:
        rows = (
            (
                await session.execute(
                    select(SupplierPCF).where(SupplierPCF.id.in_(spcf_ids))
                )
            )
            .scalars()
            .all()
        )
        supplier_pcfs = {
            s.id: s for s in rows if s.organization_id == current_user.organization_id
        }

    computed = await compute_footprint(
        session, org, product, period, inputs, supplier_pcfs
    )
    footprint = ProductFootprint(
        organization_id=current_user.organization_id,
        product_id=product.id,
        reporting_period_id=period.id,
        declared_unit=product.declared_unit,
        declared_unit_amount=product.declared_unit_amount,
        created_by=current_user.id,
        **computed,
    )
    session.add(footprint)
    await session.commit()
    await session.refresh(footprint)
    return FootprintResponse(**footprint.model_dump())


@router.post(
    "/products/{product_id}/footprints/{footprint_id}/finalize",
    response_model=FootprintResponse,
)
async def finalize_footprint(
    product_id: UUID,
    footprint_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _get_product(product_id, session, current_user)
    footprint = await session.get(ProductFootprint, footprint_id)
    if (
        footprint is None
        or footprint.product_id != product_id
        or footprint.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=404, detail="Footprint not found")
    if footprint.status == FootprintStatus.FINAL.value:
        raise HTTPException(status_code=409, detail="Footprint is already final")
    footprint.status = FootprintStatus.FINAL.value
    footprint.finalized_at = datetime.utcnow()
    await session.commit()
    await session.refresh(footprint)
    return FootprintResponse(**footprint.model_dump())


@router.get("/products/{product_id}/footprints/{footprint_id}/export/pact")
async def export_footprint_pact(
    product_id: UUID,
    footprint_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    entitlement: Annotated[dict, Depends(get_entitlement)],
):
    """PACT Data Exchange JSON. Export-gated: trial sees results on screen
    but cannot export (teaser rule); Report Pass is year-licensed."""
    product = await _get_product(product_id, session, current_user)
    footprint = await session.get(ProductFootprint, footprint_id)
    if (
        footprint is None
        or footprint.product_id != product_id
        or footprint.organization_id != current_user.organization_id
    ):
        raise HTTPException(status_code=404, detail="Footprint not found")
    await require_report_generation(entitlement)
    period = await session.get(ReportingPeriod, footprint.reporting_period_id)
    ensure_period_year_licensed(entitlement, period)
    org = await session.get(Organization, current_user.organization_id)
    return build_pact_json(org, product, footprint, period)


# ---------------------------------------------------------------- supplier PCFs


@router.get("/supplier-pcfs", response_model=List[SupplierPCFResponse])
async def list_supplier_pcfs(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    rows = (
        (
            await session.execute(
                select(SupplierPCF)
                .where(SupplierPCF.organization_id == current_user.organization_id)
                .order_by(SupplierPCF.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [SupplierPCFResponse(**r.model_dump()) for r in rows]


@router.post("/supplier-pcfs", response_model=SupplierPCFResponse)
async def create_supplier_pcf(
    data: SupplierPCFCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    row = SupplierPCF(
        **data.model_dump(),
        organization_id=current_user.organization_id,
        source="manual",
        created_by=current_user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return SupplierPCFResponse(**row.model_dump())


@router.post("/supplier-pcfs/upload", response_model=SupplierPCFResponse)
async def upload_supplier_pcf(
    data: PactUpload,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Ingest a PACT ProductFootprint JSON file from a supplier."""
    try:
        fields = parse_supplier_pact_json(data.payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid PACT file: {exc}")
    row = SupplierPCF(
        **fields,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return SupplierPCFResponse(**row.model_dump())


@router.delete("/supplier-pcfs/{supplier_pcf_id}")
async def delete_supplier_pcf(
    supplier_pcf_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    row = await session.get(SupplierPCF, supplier_pcf_id)
    if row is None or row.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Supplier PCF not found")
    referenced = (
        (
            await session.execute(
                select(ProductInput).where(
                    ProductInput.supplier_pcf_id == supplier_pcf_id
                )
            )
        )
        .scalars()
        .first()
    )
    if referenced is not None:
        raise HTTPException(
            status_code=409,
            detail="This supplier PCF is referenced by a BOM line — remove the "
            "reference first",
        )
    await session.delete(row)
    await session.commit()
    return {"ok": True}

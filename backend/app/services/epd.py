"""
EPD generator — ISO 14025 / EN 15804+A2 declaration preparation on top of
the PCF + LCA-lite lane.

Climatrix PREPARES the EPD: pins a finalized ProductFootprint, freezes its
PCF totals + EN 15804 indicator × module matrix as the declaration's
version-stable results, walks the ISO 14025 workflow (draft →
internal_review → verification → registered → published, 5-year validity),
and generates the two deliverables — an EN 15804-structured PDF and an
ILCD+EPD digital dataset. Publishing stays with the program operator;
third-party verification reuses the VerifierAccess token portal.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape  # noqa: F401  (kept for future inline use)

from app.data.impact_factors import EF31_INDICATORS
from app.models.core import Organization
from app.models.product import (
    EPDProject,
    EPDStatus,
    FootprintStatus,
    Product,
    ProductFootprint,
)
from app.services.lca import EN15804_MODULES

VALIDITY_YEARS = 5

# One step at a time, enforced server-side (the QA-tracker idiom). Reopening
# to draft is allowed until registration; a published EPD only expires.
STATUS_TRANSITIONS: dict[str, set[str]] = {
    EPDStatus.DRAFT.value: {EPDStatus.INTERNAL_REVIEW.value},
    EPDStatus.INTERNAL_REVIEW.value: {
        EPDStatus.VERIFICATION.value,
        EPDStatus.DRAFT.value,
    },
    EPDStatus.VERIFICATION.value: {
        EPDStatus.REGISTERED.value,
        EPDStatus.DRAFT.value,
    },
    EPDStatus.REGISTERED.value: {EPDStatus.PUBLISHED.value},
    EPDStatus.PUBLISHED.value: {EPDStatus.EXPIRED.value},
    EPDStatus.EXPIRED.value: set(),
}

STATUS_ORDER = [
    EPDStatus.DRAFT.value,
    EPDStatus.INTERNAL_REVIEW.value,
    EPDStatus.VERIFICATION.value,
    EPDStatus.REGISTERED.value,
    EPDStatus.PUBLISHED.value,
]

# EN 15804 default declared scope: A1-A3 mandatory minimum, C1-C4 + D
# mandatory disclosure under +A2 (cradle-to-grave declaration).
DEFAULT_SCOPE_MODULES = ["A1", "A2", "A3", "C1", "C2", "C3", "C4", "D"]

# EF 3.1 indicator code → EN 15804+A2 core-indicator abbreviation.
EN15804_ABBREV = {
    "climate_change": "GWP-total",
    "ozone_depletion": "ODP",
    "acidification": "AP",
    "eutrophication_freshwater": "EP-freshwater",
    "eutrophication_marine": "EP-marine",
    "eutrophication_terrestrial": "EP-terrestrial",
    "photochemical_ozone_formation": "POCP",
    "resource_use_fossils": "ADPF",
    "resource_use_minerals_metals": "ADPE",
    "water_use": "WDP",
    "particulate_matter": "PM",
    "ionising_radiation": "IRP",
    "ecotoxicity_freshwater": "ETP-fw",
    "human_toxicity_cancer": "HTP-c",
    "human_toxicity_non_cancer": "HTP-nc",
    "land_use": "SQP",
}

# EN 15804+A2 splits indicators into core (mandatory) and additional.
ADDITIONAL_INDICATORS = {
    "particulate_matter",
    "ionising_radiation",
    "ecotoxicity_freshwater",
    "human_toxicity_cancer",
    "human_toxicity_non_cancer",
    "land_use",
}

SCREENING_NOTE = (
    "Prepared with Climatrix on screening-grade EF 3.1 characterization "
    "(curated library). Confirm background data against a licensed LCI "
    "dataset with the program operator before publication."
)


class EPDTransitionError(Exception):
    """Raised when a status transition is invalid or prerequisites fail.
    Carries an HTTP-ready message; the API maps it to 409/422."""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def can_edit(epd: EPDProject) -> bool:
    """Declaration content is editable only while drafting."""
    return epd.status == EPDStatus.DRAFT.value


def freeze_results(
    epd: EPDProject, footprint: ProductFootprint, product: Product
) -> dict:
    """Snapshot the pinned footprint's PCF totals + LCA matrix as the EPD
    version's immutable results (what the declaration documents render)."""
    return {
        "footprint_id": str(footprint.id),
        "product_name": product.name,
        "declared_unit": footprint.declared_unit,
        "declared_unit_amount": float(footprint.declared_unit_amount),
        "boundary": footprint.boundary,
        "pcf": {
            "total_kgco2e_per_unit": float(footprint.total_kgco2e_per_unit),
            "fossil_kgco2e_per_unit": (
                float(footprint.fossil_kgco2e_per_unit)
                if footprint.fossil_kgco2e_per_unit is not None
                else None
            ),
            "biogenic_kgco2e_per_unit": (
                float(footprint.biogenic_kgco2e_per_unit)
                if footprint.biogenic_kgco2e_per_unit is not None
                else None
            ),
            "primary_data_share": footprint.primary_data_share,
            "stage_breakdown": footprint.stage_breakdown,
        },
        "lca": footprint.lca_results,
        "line_items": footprint.line_items,
        "methodology": footprint.methodology,
        "warnings": footprint.warnings or [],
    }


def apply_transition(
    epd: EPDProject,
    new_status: str,
    footprint: Optional[ProductFootprint],
    product: Product,
) -> None:
    """Validate + apply one status step, with its side effects (freeze on
    leaving draft, registration/publication stamps, 5-year validity)."""
    valid = {s.value for s in EPDStatus}
    if new_status not in valid:
        raise EPDTransitionError(
            f"Unknown status '{new_status}'. Valid: {', '.join(sorted(valid))}",
            status_code=422,
        )
    allowed = STATUS_TRANSITIONS.get(epd.status, set())
    if new_status not in allowed:
        raise EPDTransitionError(
            f"Cannot move from '{epd.status}' to '{new_status}' — the workflow "
            "moves one step at a time "
            f"(allowed next: {', '.join(sorted(allowed)) or 'none'})"
        )

    if (
        epd.status == EPDStatus.DRAFT.value
        and new_status == EPDStatus.INTERNAL_REVIEW.value
    ):
        # The freeze point: the declaration needs a finalized footprint with
        # an LCA matrix; from here the results are version-stable.
        if footprint is None:
            raise EPDTransitionError(
                "Pin a computed footprint to this EPD before review "
                "(compute + finalize on the product page)",
                status_code=422,
            )
        if footprint.status != FootprintStatus.FINAL.value:
            raise EPDTransitionError(
                "The pinned footprint is still a draft — finalize it first "
                "(a declaration must pin an immutable snapshot)",
                status_code=422,
            )
        if not footprint.lca_results:
            raise EPDTransitionError(
                "The pinned footprint has no LCA results matrix — recompute "
                "the footprint (LCA-lite runs inside every compute)",
                status_code=422,
            )
        epd.results = freeze_results(epd, footprint, product)
        epd.results_frozen_at = datetime.utcnow()

    if new_status == EPDStatus.DRAFT.value:
        # Reopen: thaw the results so the next review re-freezes fresh.
        epd.results = None
        epd.results_frozen_at = None

    if new_status == EPDStatus.REGISTERED.value:
        if not epd.program_operator:
            raise EPDTransitionError(
                "Set the program operator before marking the EPD registered",
                status_code=422,
            )
        epd.registered_at = datetime.utcnow()

    if new_status == EPDStatus.PUBLISHED.value:
        now = datetime.utcnow()
        epd.published_at = now
        epd.valid_until = date(now.year + VALIDITY_YEARS, now.month, min(now.day, 28))

    epd.status = new_status
    epd.updated_at = datetime.utcnow()


def effective_status(epd: EPDProject) -> str:
    """Published EPDs lapse to expired after their 5-year validity — computed
    on read so nothing depends on a cron."""
    if (
        epd.status == EPDStatus.PUBLISHED.value
        and epd.valid_until is not None
        and epd.valid_until < date.today()
    ):
        return EPDStatus.EXPIRED.value
    return epd.status


def readiness_checklist(
    epd: EPDProject,
    product: Product,
    footprint: Optional[ProductFootprint],
    input_count: int,
    has_verifier: bool,
) -> list[dict]:
    """The wizard's data-gaps checklist: what still blocks a credible
    declaration. Each item: key, label, ok, detail."""
    items: list[dict] = []

    def item(key: str, label: str, ok: bool, detail: str) -> None:
        items.append({"key": key, "label": label, "ok": ok, "detail": detail})

    item(
        "bom",
        "Product model (BOM)",
        input_count > 0,
        (
            f"{input_count} BOM lines on {product.name}"
            if input_count
            else "Add BOM lines on the product page"
        ),
    )
    item(
        "footprint",
        "Computed footprint pinned",
        footprint is not None,
        (
            "Pinned to a footprint snapshot"
            if footprint is not None
            else "Compute a footprint and pin it to this EPD"
        ),
    )
    item(
        "final",
        "Footprint finalized (immutable)",
        footprint is not None and footprint.status == FootprintStatus.FINAL.value,
        (
            "Snapshot is final"
            if footprint is not None and footprint.status == FootprintStatus.FINAL.value
            else "Finalize the pinned footprint — declarations pin immutable data"
        ),
    )

    lca = (epd.results or {}).get("lca") if epd.results else None
    if lca is None and footprint is not None:
        lca = footprint.lca_results
    if lca:
        rows = lca.get("rows", [])
        total_lines = rows[0]["total_lines"] if rows else 0
        full = [r for r in rows if r.get("covered_lines") == r.get("total_lines")]
        item(
            "lca",
            "EN 15804 indicator coverage",
            len(full) == len(rows) and bool(rows),
            f"{len(full)}/{len(rows)} indicators fully covered across "
            f"{total_lines} lines"
            + (
                ""
                if len(full) == len(rows)
                else " — fill EF 3.1 datasets or accept partial disclosure"
            ),
        )
        declared = set(epd.scope_modules or DEFAULT_SCOPE_MODULES)
        present = set(lca.get("modules", []))
        missing = [m for m in EN15804_MODULES if m in declared and m not in present]
        item(
            "modules",
            "Declared modules have data",
            not missing,
            (
                "All declared modules carry BOM lines"
                if not missing
                else "Declared but no data yet: "
                + ", ".join(missing)
                + " — add lines or narrow the declared scope"
            ),
        )
    else:
        item("lca", "EN 15804 indicator coverage", False, "No LCA matrix yet")

    declared = set(epd.scope_modules or DEFAULT_SCOPE_MODULES)
    needs_rsl = any(m.startswith("B") for m in declared)
    item(
        "rsl",
        "Reference service life (RSL)",
        (not needs_rsl) or epd.rsl_years is not None,
        (
            "RSL required — B modules are declared"
            if needs_rsl and epd.rsl_years is None
            else (
                f"RSL: {epd.rsl_years} years"
                if epd.rsl_years is not None
                else "Not required for the declared modules"
            )
        ),
    )
    item(
        "operator",
        "Program operator",
        bool(epd.program_operator),
        epd.program_operator or "Pick the program operator that will publish",
    )
    item(
        "verifier",
        "Third-party verifier invited",
        has_verifier,
        (
            "Verifier has a read-only portal link"
            if has_verifier
            else "Invite the verifier from the Verification tab"
        ),
    )
    return items


# ---------------------------------------------------------------- documents


def _fmt(v: float) -> str:
    """EN 15804 tables span 12 orders of magnitude — format like the UI."""
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 100:
        return f"{v:.1f}"
    if a >= 0.01:
        return f"{v:.3f}"
    return f"{v:.2E}"


def _indicator_rows(results: dict) -> list[dict]:
    """Frozen LCA rows in EN 15804 order with abbreviations attached."""
    lca = results.get("lca") or {}
    rows = {r["code"]: r for r in lca.get("rows", [])}
    out = []
    for ind in EF31_INDICATORS:
        row = rows.get(ind["code"])
        if row is None:
            continue
        out.append(
            {
                **row,
                "abbrev": EN15804_ABBREV.get(ind["code"], ind["code"]),
                "additional": ind["code"] in ADDITIONAL_INDICATORS,
            }
        )
    return out


def build_ilcd_epd_xml(
    org: Organization, product: Product, epd: EPDProject, results: dict
) -> bytes:
    """ILCD+EPD digital dataset (machine-readable EPD, the format the
    digital-EPD ecosystem ingests via soda4LCA nodes).

    A well-formed ILCD process dataset with the EPD extension namespace,
    carrying the declaration metadata + the indicator × module results.
    Full schema conformance against a program operator's node is a
    follow-up when a real operator ingests our files (the PACT-checker
    pattern).
    """
    NS = {
        "": "http://lca.jrc.it/ILCD/Process",
        "common": "http://lca.jrc.it/ILCD/Common",
        "epd": "http://www.iai.kit.edu/EPD/2013",
    }
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)

    def q(ns: str, tag: str) -> str:
        return f"{{{NS[ns]}}}{tag}"

    root = ET.Element(q("", "processDataSet"), {"version": "1.1"})
    info = ET.SubElement(root, q("", "processInformation"))
    dsi = ET.SubElement(info, q("", "dataSetInformation"))
    ET.SubElement(dsi, q("common", "UUID")).text = str(epd.id)
    name_el = ET.SubElement(dsi, q("", "name"))
    ET.SubElement(name_el, q("", "baseName")).text = product.name
    ET.SubElement(dsi, q("common", "generalComment")).text = SCREENING_NOTE

    classification = ET.SubElement(
        ET.SubElement(dsi, q("", "classificationInformation")),
        q("common", "classification"),
    )
    ET.SubElement(classification, q("common", "class"), {"level": "0"}).text = (
        product.category or "Construction products"
    )

    qref = ET.SubElement(info, q("", "quantitativeReference"))
    ET.SubElement(qref, q("", "referenceToReferenceFlow")).text = "1"
    ET.SubElement(qref, q("", "functionalUnitOrOther")).text = epd.functional_unit or (
        f"{results.get('declared_unit_amount', 1)} "
        f"{results.get('declared_unit', epd.declared_unit)} of {product.name}"
    )

    time_el = ET.SubElement(info, q("", "time"))
    ET.SubElement(time_el, q("common", "referenceYear")).text = str(
        (epd.results_frozen_at or epd.created_at).year
    )
    if epd.valid_until:
        ET.SubElement(time_el, q("common", "dataSetValidUntil")).text = str(
            epd.valid_until.year
        )

    geo = ET.SubElement(info, q("", "geography"))
    ET.SubElement(
        geo,
        q("", "locationOfOperationSupplyOrProduction"),
        {"location": org.country_code or "GLO"},
    )

    method = ET.SubElement(root, q("", "modellingAndValidation"))
    lcim = ET.SubElement(method, q("", "LCIMethodAndAllocation"))
    ET.SubElement(lcim, q("", "typeOfDataSet")).text = "EPD"
    ET.SubElement(lcim, q("common", "other"))  # extension container
    subtype = ET.SubElement(lcim.find(q("common", "other")), q("epd", "subType"))
    subtype.text = "specific dataset"

    compliance = ET.SubElement(
        ET.SubElement(method, q("", "complianceDeclarations")),
        q("", "compliance"),
    )
    ET.SubElement(compliance, q("common", "approvalOfOverallCompliance")).text = (
        epd.pcr
    )  # EN 15804+A2

    validation = ET.SubElement(method, q("", "validation"))
    review = ET.SubElement(
        validation, q("", "review"), {"type": "Independent external review"}
    )
    ET.SubElement(review, q("common", "otherReviewDetails")).text = (
        epd.verifier_statement or "Verification in progress"
    )

    admin = ET.SubElement(root, q("", "administrativeInformation"))
    pub = ET.SubElement(admin, q("", "publicationAndOwnership"))
    ET.SubElement(pub, q("common", "dataSetVersion")).text = f"{epd.version:02d}.00.000"
    ET.SubElement(pub, q("common", "permanentDataSetURI")).text = (
        f"https://climatrix.co/epd/{epd.id}"
    )
    ET.SubElement(pub, q("epd", "registrationNumber")).text = (
        epd.registration_number or ""
    )
    ET.SubElement(pub, q("epd", "programOperator")).text = epd.program_operator or ""
    ET.SubElement(pub, q("common", "referenceToOwnershipOfDataSet")).text = org.name

    # LCIA results: one result per indicator per declared module.
    lcia = ET.SubElement(root, q("", "LCIAResults"))
    lca = results.get("lca") or {}
    modules = lca.get("modules", [])
    for row in _indicator_rows(results):
        result_el = ET.SubElement(lcia, q("", "LCIAResult"))
        ref = ET.SubElement(
            result_el,
            q("", "referenceToLCIAMethodDataSet"),
            {"type": "LCIA method data set"},
        )
        ET.SubElement(ref, q("common", "shortDescription")).text = (
            f"{row['abbrev']} — {row['name']} ({lca.get('method', 'EF 3.1')})"
        )
        ET.SubElement(result_el, q("", "meanAmount")).text = _fmt(row["total"])
        other = ET.SubElement(result_el, q("common", "other"))
        for module in modules:
            amount = ET.SubElement(
                other,
                q("epd", "amount"),
                {q("epd", "module"): module},
            )
            amount.text = _fmt(row["by_module"].get(module, 0))
        unit_el = ET.SubElement(other, q("epd", "referenceToUnitGroupDataSet"))
        ET.SubElement(unit_el, q("common", "shortDescription")).text = row["unit"]

    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_epd_pdf(
    org: Organization, product: Product, epd: EPDProject, results: dict
) -> bytes:
    """EN 15804-structured declaration PDF via the existing reportlab lane."""
    import io

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"EPD — {product.name}",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "EpdTitle", parent=styles["Title"], fontSize=20, spaceAfter=4
    )
    sub = ParagraphStyle(
        "EpdSub", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#555555"), spaceAfter=3,
    )  # fmt: skip
    heading = ParagraphStyle(
        "EpdHeading", parent=styles["Heading2"], fontSize=13,
        spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1F7A5C"),
    )  # fmt: skip
    body = ParagraphStyle("EpdBody", parent=styles["Normal"], fontSize=9.5, leading=13)
    small = ParagraphStyle(
        "EpdSmall", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor("#777777"), leading=11,
    )  # fmt: skip

    accent = colors.HexColor("#1F7A5C")
    hairline = colors.HexColor("#DDE5E0")

    elements = []

    # --- Cover / declaration header -------------------------------------
    elements.append(Paragraph("Environmental Product Declaration", title))
    elements.append(Paragraph(f"{product.name} — {org.name}", sub))
    elements.append(Paragraph(f"In accordance with ISO 14025 and {epd.pcr}", sub))
    elements.append(Spacer(1, 6 * mm))

    status = effective_status(epd)
    decl_unit = (
        f"{results.get('declared_unit_amount', 1)} "
        f"{results.get('declared_unit', epd.declared_unit)}"
    )
    meta_rows = [
        ["Declaration owner", org.name],
        ["Product", product.name + (f" (SKU {product.sku})" if product.sku else "")],
        ["PCR", epd.pcr],
        ["Program operator", epd.program_operator or "— to be selected"],
        ["Declared unit", decl_unit],
        ["Functional unit", epd.functional_unit or "n/a (declared unit basis)"],
        [
            "Reference service life",
            f"{epd.rsl_years} years" if epd.rsl_years else "Not declared",
        ],
        [
            "System boundary",
            results.get("boundary", "cradle_to_gate").replace("_", "-"),
        ],
        ["Status", status.replace("_", " ").title()],
        [
            "Registration number",
            epd.registration_number or "— pending registration",
        ],
        [
            "Valid until",
            epd.valid_until.isoformat() if epd.valid_until else "— set on publication",
        ],
        ["EPD version", str(epd.version)],
    ]
    meta_table = Table(
        [
            [Paragraph(f"<b>{k}</b>", body), Paragraph(str(v), body)]
            for k, v in meta_rows
        ],
        colWidths=[55 * mm, 150 * mm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, hairline),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(meta_table)

    # --- Methodology -----------------------------------------------------
    methodology = results.get("methodology") or {}
    elements.append(Paragraph("LCA calculation rules", heading))
    elements.append(
        Paragraph(
            f"Quantification per {methodology.get('standard', 'ISO 14067:2018')} · "
            f"GWP: {methodology.get('gwp', 'IPCC AR5 (100-year)')} · "
            f"LCIA: {methodology.get('lcia_method', 'EF 3.1 (screening)')} · "
            f"Allocation: {methodology.get('allocation', 'physical')} · "
            "Offsets excluded.",
            body,
        )
    )
    pcf = results.get("pcf") or {}
    pds = pcf.get("primary_data_share")
    elements.append(
        Paragraph(
            f"Climate result (A1-A3): <b>{_fmt(pcf.get('total_kgco2e_per_unit', 0))} "
            f"kg CO2e per {decl_unit}</b>"
            + (f" · primary data share {pds:.1f}%" if pds is not None else "")
            + (
                f" · biogenic (reported separately) "
                f"{_fmt(pcf['biogenic_kgco2e_per_unit'])} kg CO2"
                if pcf.get("biogenic_kgco2e_per_unit")
                else ""
            ),
            body,
        )
    )

    # --- EN 15804 results matrix ----------------------------------------
    lca = results.get("lca") or {}
    modules = lca.get("modules", [])
    rows = _indicator_rows(results)
    if rows and modules:
        for section, want_additional in (
            ("Core environmental impact indicators (EN 15804+A2)", False),
            ("Additional environmental impact indicators", True),
        ):
            section_rows = [r for r in rows if r["additional"] == want_additional]
            if not section_rows:
                continue
            elements.append(Paragraph(section, heading))
            header = ["Indicator", "Unit", *modules, "Total"]
            data = [header]
            for r in section_rows:
                data.append(
                    [
                        Paragraph(f"<b>{r['abbrev']}</b><br/>{r['name']}", small),
                        Paragraph(r["unit"], small),
                        *[_fmt(r["by_module"].get(m, 0)) for m in modules],
                        _fmt(r["total"]),
                    ]
                )
            col_w = [58 * mm, 30 * mm] + [(165 * mm) / (len(modules) + 1)] * (
                len(modules) + 1
            )
            table = Table(data, colWidths=col_w, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), accent),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("FONTSIZE", (2, 1), (-1, -1), 8),
                        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.4, hairline),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            elements.append(table)

        partial = [
            r for r in rows if r.get("covered_lines", 0) < r.get("total_lines", 0)
        ]
        if partial:
            elements.append(
                Paragraph(
                    "Data coverage: "
                    + "; ".join(
                        f"{r['abbrev']} covers {r['covered_lines']}/{r['total_lines']} lines"
                        for r in partial
                    )
                    + ". Uncovered lines contribute to the climate indicator only.",
                    small,
                )
            )

    # --- Verification ----------------------------------------------------
    elements.append(Paragraph("Verification", heading))
    elements.append(
        Paragraph(
            "Independent third-party verification per ISO 14025 §8.1.3. "
            + (
                f"Verifier statement: {epd.verifier_statement}"
                if epd.verifier_statement
                else "Verification is performed through the Climatrix verifier "
                "portal (read-only access to the declaration, the underlying "
                "model and every line's derivation)."
            ),
            body,
        )
    )
    if results.get("warnings"):
        elements.append(Paragraph("Notes and limitations", heading))
        for w in results["warnings"][:10]:
            elements.append(Paragraph(f"• {w}", small))

    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(SCREENING_NOTE, small))
    elements.append(
        Paragraph(
            f"Generated by Climatrix · climatrix.co · "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            small,
        )
    )
    _ = (PageBreak, timedelta, Decimal)  # imported for future layout use

    doc.build(elements)
    return buf.getvalue()

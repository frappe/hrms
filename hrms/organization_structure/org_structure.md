# Organization Structure — Developer Guide

This document maps **which file does what** in the `hrms/organization_structure` module.
For business concepts and data model overview, see [README.md](README.md).

---

## Module layout

```
hrms/organization_structure/
├── setup.py                 # Sample data, migrations, workspace refresh, diagnostics
├── README.md                # Business / ER overview
├── org_structure.md         # This file — code & file map
├── fixtures/                # Workspace, sidebar, desktop icon JSON (imported by setup)
├── doctype/                 # Frappe DocTypes (schema + server + client logic)
├── page/                    # Desk pages (Organization Chart, Location Chart)
├── report/                  # Query reports
├── number_card/             # Dashboard number cards
├── dashboard_chart/         # Workspace charts
└── workspace/               # Module workspace definition
```

**Registered in HRMS app**

| File | What it wires |
|------|----------------|
| `hrms/modules.txt` | Lists `Organization Structure` as an app module |
| `hrms/hooks.py` | Page CSS for `organization-chart` and `location-chart` |

---

## Architecture in one picture

```
Organization Unit (Nested Set)
├── Reporting tree: Executive → Function → Process → … → Team
└── Physical sites: location_1 = Head Office | District Office | Branch
        └── geography: Region → Zone → City → Woreda

Position (Nested Set, parent = parent_position)
├── site_organization_unit  → where the seat physically sits
├── org_function … org_branch → reporting org cascade (optional pickers)
├── organization_unit       → resolved deepest cascade (read-only)
└── cost_center             → org unit for cost allocation

Organization Chart  → groups positions under org units via resolve_position_chart_unit()
Location Chart      → shows only units where location_1 is set
```

---

## DocTypes

### Organization Unit — functional + physical site tree

| File | Role |
|------|------|
| `doctype/organization_unit/organization_unit.json` | Schema: `unit_type`, `location_1`, geography, branch staffing, NSM fields |
| `doctype/organization_unit/organization_unit.py` | Server logic (see below) |
| `doctype/organization_unit/organization_unit.js` | Form: geo cascade queries, HO propagate button, branch position generation |
| `doctype/organization_unit/organization_unit_tree.js` | Frappe Tree view settings |
| `doctype/organization_unit/test_organization_unit.py` | Unit tests |

**Key Python functions (`organization_unit.py`)**

| Function / method | Purpose |
|-------------------|---------|
| `OrganizationUnit.validate()` | Circular ref, HO inheritance, site hierarchy, geography, primary HO |
| `apply_inherited_ho_geography()` | Non-primary HO units copy geography from primary HO |
| `propagate_ho_geography_if_primary()` | On save, push primary HO geography to inheriting HO units |
| `validate_location_hierarchy()` | District Office → Head Office parent; Branch → District Office parent |
| `validate_geography()` | Region/Zone/City/Woreda consistency and active status |
| `generate_positions_for_branch()` | Create vacant positions from branch staffing template |
| `create_branch_positions()` | Whitelisted API for **Actions → Generate Positions** |
| `propagate_ho_geography()` | Whitelisted API for **Apply Geography to Head Offices** |
| `get_children()` / `add_tree_node()` | Tree view API |
| `validate_circular_reference()` | Shared with Position — blocks self/descendant parent |
| `update_descendant_levels()` | Recalculates `organization_level` after tree moves |

**Important fields**

- `unit_type` — reporting role (Function, Department, District, Branch, …)
- `location_1` — physical site type (blank for pure reporting nodes)
- `is_primary_head_office` / `inherit_ho_geography` — Head Office geography sharing
- `branch_staffing_template` + `auto_create_positions` — branch auto-staffing on insert

---

### Position — seat in the org

| File | Role |
|------|------|
| `doctype/position/position.json` | Schema: placement, org cascade, reporting, occupancy |
| `doctype/position/position.py` | Server logic (see below) |
| `doctype/position/position.js` | Form: org cascade queries, site filter by `location_1` |
| `doctype/position/position_tree.js` | Position tree filters (org unit, location_1, site, grade) |
| `doctype/position/test_position.py` | Unit tests |

**Validate pipeline (`position.py` → `validate()`)**

```
validate_circular_reference
→ apply_template_defaults          # job_grade, job_category from template
→ set_position_code                # TEMPLATE-SITE-001
→ set_position_name
→ set_position_level
→ sync_org_from_site               # sets org_branch / org_district from site
→ set_organization_unit_from_cascade
→ set_required_defaults            # company, cost_center fallbacks
→ set_location_1_from_site
→ validate_site_placement
→ sync_occupancy_status
```

**Key Python functions**

| Function | Purpose |
|----------|---------|
| `sync_org_from_site()` | Branch site → `org_branch`; parent district → `org_district` |
| `set_organization_unit_from_cascade()` | Deepest cascade field wins (`org_branch` > `org_district` > …) |
| `resolve_position_chart_unit()` | **Organization Chart** — which org unit box shows this position |
| `get_organization_hierarchy()` | Rebuild cascade pickers when opening saved position |
| `update_occupancy()` | Refresh vacant/occupied from Position Assignment |
| `ORG_CASCADE_FIELD_ORDER` | Order: function → process → … → sub_team |
| `ORG_CASCADE_FIELDS` | Maps `unit_type` → cascade field name |

**Organization Chart linking priority (`resolve_position_chart_unit`)**

1. `org_branch`
2. `org_district`
3. `organization_unit`
4. `site_organization_unit` (if site `location_1` is Branch or District Office)

> **Why district/branch positions may not appear on the chart:** the chart only shows positions under org units that exist in the **Organization Unit tree**. A position must have `org_branch`, `org_district`, or `site_organization_unit` pointing at a unit that is a node in that tree. Pick **Site Organization Unit** on the Position form (or set `org_district` / `org_branch` in the cascade).

---

### Position Template

| File | Role |
|------|------|
| `doctype/position_template/position_template.json` | Template name, code prefix, job grade, category, family |
| `doctype/position_template/position_template.py` | Validations |
| `doctype/position_template/position_template.js` | Client scripts |

Used for position code prefix (e.g. `TEL`) and default classification on new positions.

---

### Branch Staffing Template + Detail

| File | Role |
|------|------|
| `doctype/branch_staffing_template/` | Staffing plan per branch size (Small / Medium / Large) |
| `doctype/branch_staffing_detail/` | Child table: `position_template` × `quantity` |
| `branch_staffing_template.js` | Link to Organization Unit tree |

When a **Branch** site org unit is created with `auto_create_positions`, `organization_unit.generate_positions_for_branch()` runs.

---

### Geography masters

| DocType | Folder | Hierarchy |
|---------|--------|-----------|
| Region | `doctype/region/` | Top level |
| Zone | `doctype/zone/` | → Region |
| City | `doctype/city/` | → Region, Zone |
| Woreda | `doctype/woreda/` | → City |

Each has `.json` (schema), `.py` (validation), `.js` (filtered link queries on forms).

Linked from **Organization Unit** Location 2 section and filtered on the org unit form in `organization_unit.js`.

---

### Job Grade & Job Category

| DocType | Folder | Purpose |
|---------|--------|---------|
| Job Grade | `doctype/job_grade/` | Roman levels I–VII |
| Job Category | `doctype/job_category/` | Job family / ownership category |

---

### Position Assignment

| File | Role |
|------|------|
| `doctype/position_assignment/position_assignment.py` | Links Employee ↔ Position; calls `update_occupancy()` |
| `doctype/position_assignment/position_assignment.js` | Form client script |

One active assignment per position. Updates `occupancy_status`, `is_occupied`, `current_employee` on Position.

---

## Pages

### Organization Chart

| File | Role |
|------|------|
| `page/organization_chart/organization_chart.json` | Page registration |
| `page/organization_chart/organization_chart.py` | `get_chart_data()` — builds org tree + positions per unit |
| `page/organization_chart/organization_chart.js` | Renders nested tree; unit type colours/abbreviations |
| `page/organization_chart/organization_chart.css` | Styling (loaded via `hooks.py`) |

**Flow**

1. Load all Organization Units (nested set order).
2. `_get_head_positions()` — `is_head_position` positions mapped via `resolve_position_chart_unit`.
3. `_get_positions_by_unit()` — other active positions grouped by chart unit.
4. `_build_position_tree()` — nested reporting under each unit box.
5. JS renders org nodes + position sub-trees.

### Location Chart

| File | Role |
|------|------|
| `page/location_chart/location_chart.py` | `get_chart_data()` — units where `location_1` is set |
| `page/location_chart/location_chart.js` | Site hierarchy visual (HO → District Office → Branch) |
| `page/location_chart/location_chart.css` | Styling |

Shows physical site tree only (not the full reporting org tree).

---

## Reports

Each report folder contains:

- `*.py` — `execute()` → columns + data
- `*.js` — filter fields
- `*.json` — Report DocType metadata

| Report | File | What it shows |
|--------|------|----------------|
| Organization Hierarchy | `report/organization_hierarchy/` | Org unit tree listing |
| Position Hierarchy | `report/position_hierarchy/` | Position reporting tree with filters |
| Vacant Positions | `report/vacant_positions/` | Unoccupied active positions |
| Positions by Organization Unit | `report/positions_by_organization_unit/` | Counts by resolved org unit |
| Positions by Location | `report/positions_by_location/` | Counts by `site_organization_unit` |
| Span of Control | `report/span_of_control/` | Direct reports per manager position |
| Position Count by Function | `report/position_count_by_function/` | Positions under each Function |
| Job Category Distribution | `report/job_category_distribution/` | Positions by job category |
| Location Hierarchy | `report/location_hierarchy/` | Site org units with geography |
| Branch List | `report/branch_list/` | Branch sites detail |
| District Summary | `report/district_summary/` | District sites + branch counts |
| Branches by Region/Zone/City/Woreda | `report/branches_by_*` | Geographic branch rollups |

---

## Number cards & charts

| Path | Counts |
|------|--------|
| `number_card/total_organization_units/` | All org units |
| `number_card/total_locations/` | Org units with `location_1` set |
| `number_card/total_districts/` | `location_1 = District Office` |
| `number_card/total_branches/` | `location_1 = Branch` |
| `number_card/active_branches/` / `inactive_branches/` | Branch status |
| `number_card/total_positions/` | All positions |
| `number_card/occupied_positions/` / `vacant_positions/` | Occupancy |
| `dashboard_chart/positions_by_occupancy/` | Chart on workspace |
| `dashboard_chart/positions_by_job_grade/` | Chart on workspace |

---

## Workspace & navigation

| File | Role |
|------|------|
| `fixtures/workspace.json` | Main **Organization Structure** workspace (cards, shortcuts, links) |
| `fixtures/workspace_sidebar.json` | Left sidebar items |
| `fixtures/desktop_icon.json` | Desktop module icon |
| `workspace/organization_structure/organization_structure.json` | Alternate workspace export |
| `hrms/workspace_sidebar/organization_structure.json` | Sidebar copy at app root (synced on migrate) |
| `hrms/desktop_icon/organization_structure.json` | Desktop icon at app root |

**Refresh after editing fixtures**

```bash
bench --site <site> execute hrms.organization_structure.setup.refresh_module
```

---

## setup.py — operations reference

| Function | When to run |
|----------|-------------|
| `create_sample_data()` | Seed demo org, sites, positions |
| `create_site_organization_units()` | Create/update physical site org units only |
| `create_organization_units()` | Reporting org tree only |
| `reset_sample_data()` | **Destructive** — wipe module data (dev/demo) |
| `verify_sample_data()` | Print hierarchy summary to console |
| `migrate_location_units_to_organization_units()` | One-time legacy Location Unit → Org Unit |
| `patch_position_site_fields()` | Back-fill `location_1` / `site_organization_unit` on positions |
| `patch_position_organization_units()` | Re-run cascade + site sync on all positions |
| `refresh_module()` | Import fixtures + patches + clear cache |
| `diagnose()` | Check workspace, doctypes, reports, cards exist |

---

## Data flow cheat sheet

### Creating a branch position manually

1. User opens **Position** form.
2. Sets **Location 1** = Branch, **Site Organization Unit** = e.g. `Bole Branch`.
3. Optionally sets org cascade (Function → …) for reporting org.
4. `position.py` validate:
   - `sync_org_from_site` → `org_branch` = site, `org_district` = parent district
   - `set_organization_unit_from_cascade` → deepest cascade → `organization_unit`
5. **Organization Chart** places position under `org_branch` (or district / org unit per priority).

### Auto branch staffing

1. Create **Organization Unit** with `location_1 = Branch`, staffing template, `auto_create_positions = 1`.
2. `organization_unit.after_insert` → `generate_positions_for_branch`.
3. Inserts Position rows with `site_organization_unit` + template; validate fills the rest.

### Head Office geography inheritance

1. One HO unit: `is_primary_head_office = 1`, fill Region/Zone/City/Woreda.
2. Other HO units: `inherit_ho_geography = 1` (auto), geography read-only on form.
3. Save primary HO → `propagate_ho_geography_if_primary` updates inheriting units.
4. Or use **Actions → Apply Geography to Head Offices** on primary HO form.

---

## Frappe file conventions (quick reference)

| Extension | Purpose |
|-----------|---------|
| `*.json` | DocType / Report / Page / Workspace schema |
| `*.py` | Server controller (`Document` subclass or `execute()` for reports) |
| `*.js` | Client form scripts (`frappe.ui.form.on`) or page scripts |
| `*_tree.js` | `frappe.treeview_settings["DocType Name"]` |
| `test_*.py` | `FrappeTestCase` tests run via `bench run-tests` |

---

## Common troubleshooting

| Symptom | Likely cause | Where to look |
|---------|--------------|---------------|
| Position not on Organization Chart | `resolve_position_chart_unit` returns unit not in org tree, or no org/site link | `position.py`, position form cascade + site fields |
| Branch positions under wrong unit | `organization_unit` resolved to shallow cascade instead of `org_branch` | `set_organization_unit_from_cascade`, chart priority |
| Site not on Location Chart | `location_1` blank on org unit | `organization_unit.json`, org unit form |
| Geography dropdown empty | Master inactive or parent filter mismatch | Region/Zone/City/Woreda status + `organization_unit.js` queries |
| Workspace missing after migrate | Orphan cleanup removed workspace | `setup.refresh_module` |
| Duplicate branch positions | `generate_positions_for_branch` run multiple times before idempotent count | `organization_unit.generate_positions_for_branch` |

---

## Related reading

- [README.md](README.md) — business model, ER diagram, validations summary
- Frappe Nested Set docs — `lft` / `rgt` tree mechanics for Organization Unit and Position

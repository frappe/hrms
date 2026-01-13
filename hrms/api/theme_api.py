from __future__ import annotations
import re
import frappe
from frappe import _


def _sanitize_css(css: str) -> str:
    """Basic sanitization: remove <script> blocks to avoid script injection.
    We keep this intentionally small — if you need stricter sanitization, use
    a proper CSS sanitizer or restrict who can edit `custom_css`.
    """
    if not css:
        return ""
    # remove script tags (and their content)
    css = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", css, flags=re.S | re.I)
    return css


def _validate_css_value(value: str, default: str = "") -> str:
    """Validate CSS color/value to prevent injection attacks.
    
    Allows:
    - Hex colors: #fff, #ffffff, #ffffff00
    - RGB/RGBA: rgb(255, 255, 255), rgba(255, 255, 255, 0.5)
    - HSL/HSLA: hsl(120, 100%, 50%), hsla(120, 100%, 50%, 0.5)
    - Named colors: red, blue, transparent, inherit, etc.
    - CSS keywords: inherit, transparent, currentColor, unset, initial
    
    Args:
        value: The CSS value to validate
        default: Default value to return if validation fails
        
    Returns:
        Validated value or default if invalid
    """
    if not value or not isinstance(value, str):
        return default
    
    value = value.strip()
    if not value:
        return default
    
    # Allow hex colors, rgb/rgba, hsl/hsla, named colors, CSS keywords
    # Pattern explanation:
    # - Hex: #[0-9a-fA-F]{3,8} (3, 4, 6, or 8 hex digits)
    # - Functions: rgb(a|hsl(a with parentheses and content
    # - Named/keywords: word characters
    pattern = r'^(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|[a-zA-Z][\w-]*)$'
    
    # Additional check: ensure no semicolons, braces, or other CSS-breaking chars
    if re.match(pattern, value) and not any(char in value for char in [';', '{', '}', '\n', '\r']):
        return value
    
    return default


@frappe.whitelist(allow_guest=True)
def get_theme() -> dict:
    """Return theme JSON (dict) from the Single DocType `Employee Self Service Portal Theme`.

    Maps the DocType fields to CSS variables used in main.css.
    """
    doc = frappe.get_single("Employee Self Service Portal Theme")
    return {
        # Primary button maps to --sp-primary
        "primary_button_color": getattr(doc, "button_background_color", None) or "",
        "primary_button_hover": getattr(doc, "button_hover_background_color", None) or "",
        "primary_button_text": getattr(doc, "button_text_color", None) or "",
        "primary_button_text_hover": getattr(doc, "button_hover_text_color", None) or "",
        
        # Secondary button maps to --sp-secondary
        "secondary_button_color": getattr(doc, "secondary_button_background_color", None) or "",
        "secondary_button_hover": getattr(doc, "secondary_button_hover_background_color", None) or "",
        "secondary_button_text": getattr(doc, "secondary_button_text_color", None) or "",
        "secondary_button_text_hover": getattr(doc, "secondary_button_hover_text_color", None) or "",
        
        # Body/text colors
        "body_content_box_text_color": getattr(doc, "main_body_content_box_text_color", None) or "",
        "body_content_box_text_secondary_color": getattr(doc, "main_body_content_box_text_secondary_color", None) or "",
        "body_bg": getattr(doc, "body_background_color", None) or "",
        "body_content_box_bg": getattr(doc, "main_body_content_box_background_color", None) or "",
        "page_heading_text_color": getattr(doc, "page_heading_text_color", None) or "",
        
        # Sidebar
        "sidebar_bg": getattr(doc, "sidebar_background_color", None) or "",
        "sidebar_text": getattr(doc, "sidebar_text_color", None) or "",
        
        # Login page
        "login_button_bg": getattr(doc, "login_button_background_color", None) or "",
        "login_button_hover_bg": getattr(doc, "login_page_button_hover_background_color", None) or "",
        "login_button_text": getattr(doc, "login_button_text_color", None) or "",
        "login_button_text_hover": getattr(doc, "login_page_button_hover_text_color", None) or "",
        "login_heading_text_color": getattr(doc, "login_heading_text_color", None) or "",
        "login_page_bg": getattr(doc, "login_page_background_color", None) or "",
        "login_box_bg": getattr(doc, "login_box_background_color", None) or "",
        "login_page_title": getattr(doc, "login_page_title", None) or "",
        
        # Link color
        "link_color": getattr(doc, "link_color", None) or "#0d6efd",
        
        # Input fields
        "input_bg": getattr(doc, "input_background_color", None) or "",
        "input_border": getattr(doc, "input_border_color", None) or "",
        "input_text": getattr(doc, "input_text_color", None) or "",
        "input_label": getattr(doc, "input_label_color", None) or "",
        
        "modified": str(getattr(doc, "modified", "")) if getattr(doc, "modified", None) else "",
    }


@frappe.whitelist(allow_guest=True)
def get_css() -> dict:
    """Return a rendered CSS string that matches the HRMS frontend main.css structure.

    The client-side will receive JSON like { "message": "<css...>", "modified": "..." }
    """
    data = get_theme()

    css = f"""
/* Service Portal Theme - Dynamic CSS Variables */
:root {{
  --sp-primary: {_validate_css_value(data['primary_button_color'], '#0d6efd')};
  --sp-secondary: {_validate_css_value(data['secondary_button_color'], '#6c757d')};
  --sp-text: {_validate_css_value(data['body_content_box_text_color'], '#212529')};
  --sp-text-secondary: {_validate_css_value(data.get('body_content_box_text_secondary_color'), 'inherit')};
  --sp-header-bg: {_validate_css_value(data.get('sidebar_bg'), '#f8f9fa')};
  --sp-button-bg: {_validate_css_value(data['primary_button_color'], '#0d6efd')};
  --sp-link: {_validate_css_value(data['link_color'], '#0d6efd')};
  
  /* Button hover colors */
  --sp-primary-hover: {_validate_css_value(data.get('primary_button_hover') or data['primary_button_color'], '#0b5ed7')};
  --sp-secondary-hover: {_validate_css_value(data.get('secondary_button_hover') or data['secondary_button_color'], '#5c636a')};
  
  /* Text colors */
  --sp-primary-text: {_validate_css_value(data.get('primary_button_text'), '#ffffff')};
  --sp-secondary-text: {_validate_css_value(data.get('secondary_button_text'), '#ffffff')};
  
  /* Body colors */
  --sp-body-bg: {_validate_css_value(data.get('body_bg'), '#f5f6f7')};
  --sp-content-box-bg: {_validate_css_value(data.get('body_content_box_bg'), '#ffffff')};
  
  /* Sidebar colors */
  --sp-sidebar-bg: {_validate_css_value(data.get('sidebar_bg'), '#f8f9fa')};
  --sp-sidebar-text: {_validate_css_value(data.get('sidebar_text'), '#212529')};
  
  /* Login page colors */
  --sp-login-button-bg: {_validate_css_value(data.get('login_button_bg') or data['primary_button_color'], '#0d6efd')};
  --sp-login-button-hover-bg: {_validate_css_value(data.get('login_button_hover_bg') or data['primary_button_color'], '#0b5ed7')};
  --sp-login-button-text: {_validate_css_value(data.get('login_button_text'), '#ffffff')};
  --sp-login-page-bg: {_validate_css_value(data.get('login_page_bg'), '#ffffff')};
  --sp-login-box-bg: {_validate_css_value(data.get('login_box_bg'), '#ffffff')};
  --sp-login-heading-color: {_validate_css_value(data.get('login_heading_text_color'), '#212529')};
  --sp-page-heading-color: {_validate_css_value(data.get('page_heading_text_color'), '#212529')};
  
  /* Input fields */
  --sp-input-bg: {_validate_css_value(data.get('input_bg'), '#ffffff')};
  --sp-input-border: {_validate_css_value(data.get('input_border'), '#ced4da')};
  --sp-input-text: {_validate_css_value(data.get('input_text'), '#212529')};
  --sp-input-label: {_validate_css_value(data.get('input_label'), '#374151')};
}}

/* Primary Buttons */
.btn-primary,
.button-primary,
button[type="submit"],
.button--primary {{
  background-color: var(--sp-primary) !important;
  border-color: var(--sp-primary) !important;
  color: var(--sp-primary-text) !important;
}}

.btn-primary:hover,
.button-primary:hover,
button[type="submit"]:hover,
.button--primary:hover {{
  background-color: var(--sp-primary-hover) !important;
  opacity: 0.9;
}}

/* Secondary Buttons */
.btn-secondary,
.button-secondary,
.button--secondary {{
  background-color: var(--sp-secondary) !important;
  border-color: var(--sp-secondary) !important;
  color: var(--sp-secondary-text) !important;
}}

.btn-secondary:hover,
.button-secondary:hover,
.button--secondary:hover {{
  background-color: var(--sp-secondary-hover) !important;
  opacity: 0.9;
}}

/* Links */
a:not(.no-theme) {{
  color: var(--sp-link) !important;
}}

a:hover:not(.no-theme) {{
  color: var(--sp-primary) !important;
  opacity: 0.8;
}}

/* Headers and Navigation / Sidebar */
.navbar,
.header,
.app-header,
ion-header,
ion-toolbar,
.sidebar,
nav {{
  background-color: var(--sp-header-bg) !important;
}}

.sidebar {{
  background-color: var(--sp-sidebar-bg) !important;
  color: var(--sp-sidebar-text) !important;
}}

/* Body and Content */
body {{
  color: var(--sp-text) !important;
  background-color: var(--sp-body-bg) !important;
}}

.content-box,
.card,
.box {{
  background-color: var(--sp-content-box-bg) !important;
}}

/* Ionic components */
ion-button[color="primary"] {{
  --background: var(--sp-primary);
  --background-activated: var(--sp-primary-hover);
  --background-focused: var(--sp-primary-hover);
  --background-hover: var(--sp-primary-hover);
  --color: var(--sp-primary-text);
}}

/* Tabs and active states */
.tab-active,
.active,
[aria-selected="true"] {{
  color: var(--sp-primary) !important;
  border-color: var(--sp-primary) !important;
}}

/* Form controls */
input,
textarea,
select,
.input,
.form-control {{
  background-color: var(--sp-input-bg) !important;
  border-color: var(--sp-input-border) !important;
  color: var(--sp-input-text) !important;
}}

input:focus,
textarea:focus,
select:focus,
.input:focus,
.form-control:focus {{
  border-color: var(--sp-primary) !important;
  outline-color: var(--sp-primary) !important;
}}

/* Form labels */
label,
.label,
.form-label {{
  color: var(--sp-input-label) !important;
}}

/* Utility classes */
.border-primary {{
  border-color: var(--sp-primary) !important;
}}

.bg-primary {{
  background-color: var(--sp-primary) !important;
}}

.text-primary {{
  color: var(--sp-primary) !important;
}}

/* Login Page Specific */
.login-page {{
  background-color: var(--sp-login-page-bg) !important;
}}

.login-box {{
  background-color: var(--sp-login-box-bg) !important;
}}

.login-page button,
.login-page .btn-primary {{
  background-color: var(--sp-login-button-bg) !important;
  color: var(--sp-login-button-text) !important;
}}

.login-page button:hover,
.login-page .btn-primary:hover {{
  background-color: var(--sp-login-button-hover-bg) !important;
}}

.login-page h1,
.login-page h2,
.login-page .heading,
.login-page .page-card-head {{
  color: var(--sp-login-heading-color) !important;
}}

.page-heading,
h1.page-title,
h2.page-title {{
  color: var(--sp-page-heading-color) !important;
}}
"""

    return {"message": css, "modified": data.get("modified")}


def on_theme_update(doc, method=None):
    """Called from hooks when the Service Portal Theme is updated.

    - publish a realtime event so clients can hot-reload
    - write a cache version token
    """
    try:
        # publish to any subscribed clients (service portal frontends can listen)
        frappe.publish_realtime("employee_self_service_portal_theme:update", {"modified": str(doc.modified)})
    except Exception:
        frappe.log_error(title="Theme update realtime publish failed")

    try:
        # store a simple version token in cache so other server-side code can quickly
        # check the current theme version without loading the DocType
        cache = frappe.cache()
        cache.set_value("employee_self_service_portal_theme:version", str(doc.modified))
    except Exception:
        # cache setting is non-critical; log but don't break the update
        frappe.log_error(title="Theme update cache set failed")


@frappe.whitelist()
def refresh_theme(theme_name: str) -> dict:
    """Manually trigger a theme refresh event to all connected clients.
    
    This is useful for testing or forcing a theme reload without modifying the doc.
    
    Args:
        theme_name: The name of the Employee Self Service Portal Theme document
    
    Returns:
        dict: Success status and message
    """
    try:
        # Verify the document exists and user has permission
        doc = frappe.get_doc("Employee Self Service Portal Theme", theme_name)
        
        # Trigger the realtime event
        frappe.publish_realtime("employee_self_service_portal_theme:update", {"modified": str(doc.modified)})
        
        return {
            "success": True,
            "message": _("Theme refresh event sent to all connected clients")
        }
    except frappe.PermissionError:
        frappe.throw(_("You don't have permission to refresh the theme"))
    except Exception as e:
        frappe.log_error(title="Manual theme refresh failed")
        frappe.throw(_("Failed to refresh theme: {0}").format(str(e)))


#!/usr/bin/env python3
"""
Custom WSGI application for serving Frappe with static files in production.
This is needed for environments like Coolify where nginx can't access shared volumes.
"""

import os
import sys

# Add frappe to path
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/sites')

from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from frappe.app import application as frappe_app

# Get sites path
sites_path = '/home/frappe/frappe-bench/sites'

# Wrap the frappe application with static file serving middleware
application = SharedDataMiddleware(frappe_app, {
    '/assets': os.path.join(sites_path, 'assets'),
    '/files': sites_path
})

# Add proxy fix for proper headers
application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 8000, application, use_debugger=True, use_reloader=True)
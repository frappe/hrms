<h2>{{ _("Leave Application Pending Approval") }}</h2>

<table class="table table-bordered small" style="max-width: 500px;">
    <tr><td>Employee</td><td>{{ doc.employee_name }}</td></tr>
    <tr><td>Leave Type</td><td>{{ doc.leave_type }}</td></tr>
    <tr><td>From Date</td><td>{{ doc.from_date }}</td></tr>
    <tr><td>To Date</td><td>{{ doc.to_date }}</td></tr>
    <tr><td>Status</td><td>{{ doc.status }}</td></tr>
</table>

<p><br>
<a class="btn btn-primary" href="{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}" target="_blank">{{ _('View Leave') }}</a></p>

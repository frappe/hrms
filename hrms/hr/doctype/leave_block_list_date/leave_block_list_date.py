# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


from frappe.model.document import Document


class LeaveBlockListDate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		block_date: DF.Date
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reason: DF.Text
	# end: auto-generated types

	pass

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from frappe.model.document import Document


class AppraisalTemplateGoal(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		key_result_area: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		per_weightage: DF.Percent
	# end: auto-generated types

	pass

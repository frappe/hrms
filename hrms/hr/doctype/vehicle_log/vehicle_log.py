import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class VehicleLog(Document):
    def validate(self):
        # 1️⃣ Odometer validation
        if flt(self.odometer) < flt(self.last_odometer):
            frappe.throw(
                _("Current Odometer Value should be greater than Last Odometer Value {0}").format(
                    self.last_odometer
                )
            )

        # 2️⃣ --- Fuel Calculations ---
        total_fuel_qty = 0
        total_fuel_amount = 0

        # Loop through child table refuling_details
        for row in self.refuling_details:
            total_fuel_qty += flt(row.fuel_qty)
            total_fuel_amount += flt(row.fuel_price)

        # Calculate average (avoid divide by zero)
        avg_fuel_rate = (total_fuel_amount / total_fuel_qty) if total_fuel_qty else 0

        # Save values back to parent fields
        self.total_amount = total_fuel_amount          # Grand total fuel cost
        self.total_fuel_qty_l = total_fuel_qty         # Total liters
        self.average_fuel_price = avg_fuel_rate        # Average price per liter

        # (Optional) If you also want mileage or other auto fields,
        # you can add similar calculations here.

    def on_submit(self):
        frappe.db.set_value("Vehicle", self.license_plate, "last_odometer", self.odometer)

    def on_cancel(self):
        distance_travelled = self.odometer - self.last_odometer
        if distance_travelled > 0:
            updated_odometer_value = (
                int(frappe.db.get_value("Vehicle", self.license_plate, "last_odometer")) - distance_travelled
            )
            frappe.db.set_value("Vehicle", self.license_plate, "last_odometer", updated_odometer_value)

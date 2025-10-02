frappe.ui.form.on("Vehicle Log", {
    setup: function (frm) {
        frm.set_query("employee", function () {
            return { filters: { status: "Active" } };
        });
    },

    refresh: function (frm) {
        // Odometer difference
        if (frm.doc.odometer && frm.doc.last_odometer) {
            let odometer_km = flt(frm.doc.odometer) - flt(frm.doc.last_odometer);
            frm.set_value('total_kms', odometer_km);
        }

        // Buttons if submitted
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(
                __("Expense Claim"),
                function () { frm.events.expense_claim(frm); },
                __("Create")
            );
            frm.page.set_inner_btn_group_as_primary(__("Create"));
        }

        // Fetch Data buttons
        frm.add_custom_button(__('Show Live Location'), () => {
            fetch_vehicle_live_location(frm, 'Show Live Location');
        }, 'Fetch Data');

        frm.add_custom_button(__('Fetch Vehicle History'), () => {
            show_date_popup(frm, 'Fetch Vehicle History');
        }, 'Fetch Data');

        // Recalculate everything
        recalc_fuel_totals(frm);
        recalc_amount_to_be_claimed(frm);
        recalc_total_km(frm);
        recalc_grand_totals(frm);
        recalc_mileage(frm);
    },

    validate: function(frm) {
        if (frm.doc.odometer && frm.doc.last_odometer) {
            let odometer_km = flt(frm.doc.odometer) - flt(frm.doc.last_odometer);
            frm.set_value('total_kms', odometer_km);
        }
        // Recalculate before save
        recalc_fuel_totals(frm);
        recalc_amount_to_be_claimed(frm);
        recalc_total_km(frm);
        recalc_grand_totals(frm);
        recalc_mileage(frm);
    },

    expense_claim: function (frm) {
        frappe.call({
            method: "hrms.hr.doctype.vehicle_log.vehicle_log.make_expense_claim",
            args: { docname: frm.doc.name },
            callback: function (r) {
                frappe.set_route("Form", "Expense Claim", r.message.name);
            },
        });
    }
});

/* ------------------ ✅ CHILD TABLE EVENTS ------------------ */
frappe.ui.form.on('Refuling Details', {
    fuel_qty: function(frm){ recalc_fuel_totals(frm); recalc_amount_to_be_claimed(frm); },
    fuel_price: function(frm){ recalc_fuel_totals(frm); recalc_amount_to_be_claimed(frm); },
    fuel_rate: function(frm){ recalc_fuel_totals(frm); recalc_amount_to_be_claimed(frm); },
    custom_fuel_card: function(frm){ recalc_fuel_totals(frm); recalc_amount_to_be_claimed(frm); }
});

frappe.ui.form.on("Extra Visit", {
    kms: function(frm) { recalc_total_km(frm); recalc_mileage(frm); },
    table_fygn_remove: function(frm) { recalc_total_km(frm); recalc_mileage(frm); }
});

/* ------------------ ✅ FUEL CARD CALCULATIONS ------------------ */
function recalc_fuel_totals(frm) {
    let total_qty = 0;
    let fuel_card_total = 0;
    let fuel_card_qty_total = 0;

    (frm.doc.refuling_details || []).forEach(row => {
        total_qty += flt(row.fuel_qty);
        if (row.custom_fuel_card) {
            fuel_card_total += flt(row.fuel_price);
            fuel_card_qty_total += flt(row.fuel_qty);
        }
    });

    frm.set_value('total_fuel_qty_l', total_qty);
    frm.set_value('fuel_card_price', fuel_card_total);
    frm.set_value('fuel_card_entitle_amount', fuel_card_total);
    frm.set_value('fuel_card_entitled_quantity', fuel_card_qty_total);
}

/* ------------------ ✅ AMOUNT TO BE CLAIMED ------------------ */
function recalc_amount_to_be_claimed(frm) {
    let total_amount = flt(frm.doc.total_amount || 0);
    let fuel_card_total = flt(frm.doc.fuel_card_entitle_amount || 0);
    let claimable = total_amount - fuel_card_total;

    frm.set_value('amount_to_be_claimed', claimable);
}

/* ------------------ ✅ TOTAL KM ------------------ */
function recalc_total_km(frm) {
    let total_km = 0;

    // From Extra Visit child table
    (frm.doc.table_fygn || []).forEach(row => {
        total_km += flt(row.kms || 0);
    });

    frm.set_value('total_km', total_km);
    frm.refresh_field('total_km');
}

/* ------------------ ✅ GRAND TOTAL ------------------ */
function recalc_grand_totals(frm) {
    let total_expense = flt(frm.doc.total_expense_amount || 0);
    let total_amount = flt(frm.doc.total_amount || 0);
    let amount_to_be_claimed = flt(frm.doc.amount_to_be_claimed || 0);

    frm.set_value('grand_total_inc_fuel_card', total_amount + total_expense);
    frm.set_value('claimable_grand_total', amount_to_be_claimed + total_expense);
}

/* ------------------ ✅ MILEAGE ------------------ */
function recalc_mileage(frm) {
    let total_km = flt(frm.doc.total_km || 0);
    let total_fuel = 0;

    (frm.doc.refuling_details || []).forEach(row => {
        total_fuel += flt(row.fuel_qty);
    });

    if (total_fuel > 0) {
        let mileage = total_km / total_fuel;
        frm.set_value('mileage_kml', mileage.toFixed(2));
    } else {
        frm.set_value('mileage_kml', 0);
    }
}

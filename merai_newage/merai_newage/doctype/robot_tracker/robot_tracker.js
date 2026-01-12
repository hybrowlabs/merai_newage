// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Robot Tracker", {
	refresh(frm) {

	},
	batch_number(frm) {
    if (!frm.doc.batch_number) return;

    frappe.db.get_value(
        "Batch",
        frm.doc.batch_number,
        "custom_batch_number"
    ).then(r => {
		console.log("r------------",r)
        if (r && r.message) {
            frm.set_value("batch_no", r.message.custom_batch_number);
        }
    });
}


});

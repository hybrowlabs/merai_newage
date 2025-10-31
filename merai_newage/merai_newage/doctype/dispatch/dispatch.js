// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Dispatch", {
    item_code(frm) {
        if (!frm.doc.item_code) return;

        // Fetch Item document (including its child table)
        frappe.db.get_doc("Item", frm.doc.item_code)
            .then(item_doc => {
                // Clear existing checklist in Dispatch
                frm.clear_table("dispatch_standard_checklist");

                (item_doc.custom_dispatch_checklist_details || []).forEach(row => {
                    console.log("row-----",row)
                    let new_row = frm.add_child("dispatch_standard_checklist");
                    new_row.product_code = row.product_name;
                    new_row.product_description = row.product_description;
                    // Add more fields here if needed
                });

                // Refresh child table to show new rows
                frm.refresh_field("dispatch_standard_checklist");
            })
            .catch(err => {
                frappe.msgprint(`Failed to fetch checklist details: ${err}`);
            });
    }
});

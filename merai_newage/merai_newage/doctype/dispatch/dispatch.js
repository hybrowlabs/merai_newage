// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

let used_batches_cache = null;
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
    },


refresh(frm) {
    frappe.call({
        method: "merai_newage.merai_newage.doctype.dispatch.dispatch.get_used_batch_numbers",
        callback: function(r) {
            let used_batches = r.message || [];

            frm.set_query("batch_no", () => {
                return {
                    query: "merai_newage.merai_newage.doctype.dispatch.dispatch.get_available_batches",
                    filters: {
                        item_code: frm.doc.item_code || "",
                        exclude_batches: used_batches
                    }
                };
            });
        }
    });

    if (frm.doc.docstatus==1) {
                    frm.add_custom_button(
                            "Installation",
                            function () {
                                frappe.call({
                                    method: "merai_newage.merai_newage.doctype.assign_installation.assign_installation.create_assign_installation",
                                    args: {
                                        doc: frm.doc
                                    },
                                    callback: function (r) {
                                        frappe.set_route("Form", "Assign Installation", r.message);
                                        frappe.show_alert({
                                            message: __("Assign Installation Created Successfully"),
                                            indicator: "green"
                                        });
                                    }
                                });
                            },
                            "Assign"
                        );

                }
}

,

  batch_no(frm) {
    if (!frm.doc.batch_no) return;

    frappe.call({
        method: "merai_newage.merai_newage.doctype.dispatch.dispatch.update_dispatch_details",
        args: { doc: frm.doc },
        callback: function (r) {
            if (!r.message) return;

            if (r.message.work_order) {
                frm.set_value("work_order", r.message.work_order);
            }
            if (r.message.std_batch_no) {
                frm.set_value("batch_number", r.message.std_batch_no);
            }

            const items = r.message.items || [];

            items.forEach(jc_row => {

                let existing = frm.doc.dispatch_standard_checklist.find(
                    d => d.product_code === jc_row.product_code
                );

                if (existing) {
                    // Update existing row
                    existing.batch_no = jc_row.batch_no;
                } else {
                    // Add new row
                    let child = frm.add_child("dispatch_standard_checklist");
                    child.product_code = jc_row.product_code;
                    child.batch_no = jc_row.batch_no;
                }
            });

            frm.refresh_field("dispatch_standard_checklist");
        }
    });
}



});

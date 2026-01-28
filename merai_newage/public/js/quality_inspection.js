frappe.ui.form.on("Quality Inspection", {
    refresh: function(frm) {
        handle_software_fields(frm);
        handle_qc_items_visibility(frm);
        fetch_purchase_order_reference(frm); 
        fetch_material_received_qty(frm);
    },
// before_save: function(frm) {
//   frappe.call({
//     method: "merai_newage.overrides.quality_inspection.get_employee_by_user",
//     args: {
//       user: frappe.session.user
//     },
//     callback: function(r) {
//       if (r.message) {
//         console.log("Employee:", r.message);
//       }
//     }
//   });
// },
    reference_type: function(frm) {
        handle_qc_items_visibility(frm);
        fetch_purchase_order_reference(frm); 
    },
   
    reference_name: function(frm) {
        fetch_material_received_qty(frm);
    },   

    after_save: function(frm) {
        handle_software_fields(frm);
    },

    item_code: function(frm) {
        fetch_material_received_qty(frm);
    },
    
});

function handle_software_fields(frm) {
    if (!frm.doc.reference_name) return;  

    frappe.db.get_value("Job Card", frm.doc.reference_name, "operation", function(r) {
        if (!r || !r.operation) return;

        const jobcard_operation = r.operation;
        const software_operations = [
            "MISSO Robotic Execution Software-Arm Cart",
            "MISSO Robotic Execution Software",
            "MISSO Planning Software"
        ];
        console.log("jobcard_operation=====",jobcard_operation)
        if (software_operations.includes(jobcard_operation)) {
            console.log("====25")
            frm.set_df_property("custom_software", "hidden", 0);
            frm.set_df_property("custom_verified", "hidden", 0);
            frm.set_df_property("custom_remarks", "hidden", 0);

            frm.set_value("custom_software", jobcard_operation);

            // Hide child table
            frm.clear_table("custom_qc_items");
            frm.refresh_field("custom_qc_items");
            frm.set_df_property("custom_qc_items", "hidden", 1);

        } else {
            // Hide software fields
            console.log("38===")
            frm.set_df_property("custom_software", "hidden", 1);
            frm.set_df_property("custom_verified", "hidden", 1);
            frm.set_df_property("custom_remarks", "hidden", 1);

            // Show child table
            frm.set_df_property("custom_qc_items", "hidden", 0);
        }

        frm.refresh_fields();
    });
}

// Show or hide QC Items child table based on reference type
function handle_qc_items_visibility(frm) {
    const show_fields_for = ["Stock Entry", "Job Card"];

    const should_show = show_fields_for.includes(frm.doc.reference_type);

    // Toggle fields based on condition
    frm.set_df_property("custom_qc_items", "hidden", !should_show);
    frm.set_df_property("custom_software", "hidden", !should_show);
    frm.set_df_property("custom_verified", "hidden", !should_show);
    frm.set_df_property("custom_remarks", "hidden", !should_show);

    frm.refresh_fields(["custom_qc_items", "custom_software", "custom_verified", "custom_remarks"]);
}

// Fetch and set the purchase order reference based on reference type and name
function fetch_purchase_order_reference(frm) {
    const ref_type = frm.doc.reference_type;
    const ref_name = frm.doc.reference_name;

    if (!ref_type || !ref_name) return;

    const child_doctypes = ["Purchase Receipt", "Purchase Invoice", "Subcontracting Receipt"];

    if (!child_doctypes.includes(ref_type)) {
        frm.set_value("custom_purchase_order_reference", null);
        return;
    }

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: ref_type,
            name: ref_name
        },
        callback: function(r) {
            if (r.message) {
                const doc = r.message;
                const items = doc.items || [];
                let purchase_order = null;

                for (let item of items) {
                    if (item.purchase_order) {
                        purchase_order = item.purchase_order;
                        break;
                    }
                }

                frm.set_value("custom_purchase_order_reference", purchase_order || null);
            }
        }
    });
}

// Fetch and set the material received quantity based on reference type and name
function fetch_material_received_qty(frm) {
    if (frm.doc.reference_type !== "Purchase Receipt" || !frm.doc.reference_name || !frm.doc.item_code) {
        frm.set_value("custom_material_received_quantity", null);
        return;
    }

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Purchase Receipt",
            name: frm.doc.reference_name
        },
        callback: function(r) {
            if (r.message) {
                const receipt = r.message;
                const item_row = (receipt.items || []).find(
                    row => row.item_code === frm.doc.item_code
                );

                if (item_row) {
                    frm.set_value("custom_material_received_quantity", item_row.qty || 0);
                } else {
                    frm.set_value("custom_material_received_quantity", 0);
                }
            }
        }
    });
}

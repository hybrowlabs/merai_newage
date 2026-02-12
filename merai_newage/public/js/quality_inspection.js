// frappe.ui.form.on("Quality Inspection", {
//     refresh: function(frm) {
//         handle_software_fields(frm);
//         handle_qc_items_visibility(frm);
//         fetch_purchase_order_reference(frm); 
//         fetch_material_received_qty(frm);
//     },
// // before_save: function(frm) {
// //   frappe.call({
// //     method: "merai_newage.overrides.quality_inspection.get_employee_by_user",
// //     args: {
// //       user: frappe.session.user
// //     },
// //     callback: function(r) {
// //       if (r.message) {
// //         console.log("Employee:", r.message);
// //       }
// //     }
// //   });
// // },
//     reference_type: function(frm) {
//         handle_qc_items_visibility(frm);
//         fetch_purchase_order_reference(frm); 
//     },
   
//     reference_name: function(frm) {
//         fetch_material_received_qty(frm);
//     },   

//     after_save: function(frm) {
//         handle_software_fields(frm);
//     },

//     item_code: function(frm) {
//         fetch_material_received_qty(frm);
//     },
    
// });

// function handle_software_fields(frm) {
//     if (!frm.doc.reference_name) return;  

//     frappe.db.get_value("Job Card", frm.doc.reference_name, "operation", function(r) {
//         if (!r || !r.operation) return;

//         const jobcard_operation = r.operation;
//         const software_operations = [
//             "MISSO Robotic Execution Software-Arm Cart",
//             "MISSO Robotic Execution Software",
//             "MISSO Planning Software"
//         ];
//         console.log("jobcard_operation=====",jobcard_operation)
//         if (software_operations.includes(jobcard_operation)) {
//             console.log("====25")
//             frm.set_df_property("custom_software", "hidden", 0);
//             frm.set_df_property("custom_verified", "hidden", 0);
//             frm.set_df_property("custom_remarks", "hidden", 0);

//             frm.set_value("custom_software", jobcard_operation);

//             // Hide child table
//             frm.clear_table("custom_qc_items");
//             frm.refresh_field("custom_qc_items");
//             frm.set_df_property("custom_qc_items", "hidden", 1);

//         } else {
//             // Hide software fields
//             console.log("38===")
//             frm.set_df_property("custom_software", "hidden", 1);
//             frm.set_df_property("custom_verified", "hidden", 1);
//             frm.set_df_property("custom_remarks", "hidden", 1);

//             // Show child table
//             frm.set_df_property("custom_qc_items", "hidden", 0);
//         }

//         frm.refresh_fields();
//     });
// }

// // Show or hide QC Items child table based on reference type
// function handle_qc_items_visibility(frm) {
//     const show_fields_for = ["Stock Entry", "Job Card"];

//     const should_show = show_fields_for.includes(frm.doc.reference_type);

//     // Toggle fields based on condition
//     frm.set_df_property("custom_qc_items", "hidden", !should_show);
//     frm.set_df_property("custom_software", "hidden", !should_show);
//     frm.set_df_property("custom_verified", "hidden", !should_show);
//     frm.set_df_property("custom_remarks", "hidden", !should_show);

//     frm.refresh_fields(["custom_qc_items", "custom_software", "custom_verified", "custom_remarks"]);
// }

// // Fetch and set the purchase order reference based on reference type and name
// function fetch_purchase_order_reference(frm) {
//     const ref_type = frm.doc.reference_type;
//     const ref_name = frm.doc.reference_name;

//     if (!ref_type || !ref_name) return;

//     const child_doctypes = ["Purchase Receipt", "Purchase Invoice", "Subcontracting Receipt"];

//     if (!child_doctypes.includes(ref_type)) {
//         frm.set_value("custom_purchase_order_reference", null);
//         return;
//     }

//     frappe.call({
//         method: "frappe.client.get",
//         args: {
//             doctype: ref_type,
//             name: ref_name
//         },
//         callback: function(r) {
//             if (r.message) {
//                 const doc = r.message;
//                 const items = doc.items || [];
//                 let purchase_order = null;

//                 for (let item of items) {
//                     if (item.purchase_order) {
//                         purchase_order = item.purchase_order;
//                         break;
//                     }
//                 }

//                 frm.set_value("custom_purchase_order_reference", purchase_order || null);
//             }
//         }
//     });
// }

// function fetch_material_received_qty(frm) {
//     if (frm.doc.reference_type !== "Purchase Receipt" || !frm.doc.reference_name || !frm.doc.item_code) {
//         frm.set_value("custom_material_received_quantity", null);
//         return;
//     }

//     frappe.call({
//         method: "frappe.client.get",
//         args: {
//             doctype: "Purchase Receipt",
//             name: frm.doc.reference_name
//         },
//         callback: function(r) {
//             if (r.message) {
//                 const receipt = r.message;
//                 const item_row = (receipt.items || []).find(
//                     row => row.item_code === frm.doc.item_code
//                 );

//                 if (item_row) {
//                     frm.set_value("custom_material_received_quantity", item_row.qty || 0);
//                 } else {
//                     frm.set_value("custom_material_received_quantity", 0);
//                 }
//             }
//         }
//     });
// }







frappe.ui.form.on("Quality Inspection", {
    refresh: function(frm) {
        handle_software_fields(frm);
        handle_qc_items_visibility(frm);
        fetch_purchase_order_reference(frm); 
        fetch_material_received_qty(frm);
        if (
            frm.doc.reference_type === "Purchase Receipt" &&
            frm.doc.reference_name &&
            !frm.doc.__islocal
        ) {
            frm.add_custom_button("Generate AR No", () => {
                generate_ar_no(frm);
            });
        }
    },

    reference_type: function(frm) {
        handle_qc_items_visibility(frm);
        fetch_purchase_order_reference(frm); 
    },
   
    reference_name: function(frm) {
        fetch_material_received_qty(frm);
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

        if (software_operations.includes(jobcard_operation)) {
            // Show software fields
            frm.set_df_property("custom_software", "hidden", 0);
            frm.set_df_property("custom_verified", "hidden", 0);
            frm.set_df_property("custom_remarks", "hidden", 0);

            // Set software value only if different (prevents infinite loop)
            if (frm.doc.custom_software !== jobcard_operation) {
                frm.set_value("custom_software", jobcard_operation);
            }

            // Hide child table
            frm.clear_table("custom_qc_items");
            frm.refresh_field("custom_qc_items");
            frm.set_df_property("custom_qc_items", "hidden", 1);

        } else {
            // Hide software fields
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

    if (!ref_type || !ref_name) {
        return;
    }

    const child_doctypes = ["Purchase Receipt", "Purchase Invoice", "Subcontracting Receipt"];

    if (!child_doctypes.includes(ref_type)) {
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

                // Only set if different (prevents infinite loop)
                if (frm.doc.custom_purchase_order_reference !== purchase_order) {
                    frm.set_value("custom_purchase_order_reference", purchase_order || null);
                }
            }
        }
    });
}

function fetch_material_received_qty(frm) {
    if (frm.doc.reference_type !== "Purchase Receipt" || !frm.doc.reference_name || !frm.doc.item_code) {
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

                const new_qty = item_row ? (item_row.qty || 0) : 0;
                
                // Only set if different (prevents infinite loop)
                if (frm.doc.custom_material_received_quantity !== new_qty) {
                    frm.set_value("custom_material_received_quantity", new_qty);
                }
            }
        }
    });
}

// function generate_ar_no(frm) {
//     if (
//         frm.doc.reference_type === "Purchase Receipt" &&
//         frm.doc.reference_name &&
//         frm.doc.item_code
//     ) {
//         frappe.call({
//             method: "merai_newage.overrides.quality_inspection.generate_ar_no",
//             args: {
//                 reference_name: frm.doc.reference_name,
//                 item_code: frm.doc.item_code,
//                 qi_docname: frm.doc.name
//             },
//             callback: function (r) {
//                 if (r.message && Array.isArray(r.message)) {

//                     frm.clear_table("custom_analytic_no_details");

//                     r.message.forEach(function (ar_no) {
//                         let row = frm.add_child("custom_analytic_no_details");
//                         row.ar_no = ar_no;
//                     });

//                     frm.refresh_field("custom_analytic_no_details");

//                     frappe.msgprint({
//                         title: "AR Numbers Generated",
//                         message: `${r.message.length} AR Numbers added`,
//                         indicator: "green"
//                     });
//                 }
//             }
//         });
//     }
// }



function generate_ar_no(frm) {
    if (
        frm.doc.reference_type !== "Purchase Receipt" ||
        !frm.doc.reference_name ||
        !frm.doc.item_code ||
        frm.doc.docstatus !== 0
    ) {
        return;
    }

    frappe.call({
        method: "merai_newage.overrides.quality_inspection.generate_ar_no",
        freeze: true,
        freeze_message: __("Generating AR Numbers..."),
        args: {
            reference_name: frm.doc.reference_name,
            item_code: frm.doc.item_code,
            qi_docname: frm.doc.name
        },
        callback: function (r) {
            if (!r.message || !Array.isArray(r.message)) return;

            // 🚀 FAST WAY: replace entire child table at once
            let rows = r.message.map(ar_no => ({
                ar_no: ar_no
            }));

            frm.doc.custom_serial_no_details = rows;
            frm.refresh_field("custom_serial_no_details");

            // Save AFTER bulk update
            frm.save().then(() => {
                frappe.msgprint({
                    title: "Success",
                    message: `${rows.length} AR Numbers generated`,
                    indicator: "green"
                });
            });
        }
    });
}

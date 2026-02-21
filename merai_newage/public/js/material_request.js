

frappe.ui.form.on("Material Request", {
       custom_plant: function (frm) {
               set_segment_filter(frm);

    },
    
    onload: function (frm) {
        set_segment_filter(frm);

        // frm.set_query("custom_segment_master", () => {
        //     return {
        //         filters: [
        //             ["Contact", "custom_contact_type", "=", "Clinical Specialist"]
        //         ]
        //     };
        // });


        // Set warehouse from work order - only on first load
        // if (!frm.doc.set_from_warehouse && frm.doc.work_order) {
        //     frappe.call({
        //         method: "merai_newage.overrides.material_request.get_warehouse_and_set_in_material_request",
        //         args: {
        //             work_order_name: frm.doc.work_order,
        //             name: frm.doc.name
        //         },
        //         callback: function (r) {
        //             if (r.message && r.message.status === "success") {
        //                 // Reload the document to show updated warehouse values
        //                 frm.reload_doc();
        //             } else if (r.message && r.message.status === "already_set") {
        //                 console.log("Warehouses already set:", r.message);
        //             }
        //         }
        //     });
        // }

        // Set requisitioner - only on first load when empty
        if (!frm.doc.custom_requisitioner) {
            set_requisitioner(frm);
        }
    },

    custom_asset_creation_request(frm) {
        let acr = frm.doc.custom_asset_creation_request;
        if (!acr) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Asset Creation Request",
                name: acr
            },
            // callback: function (r) {
            //     if (!r.message) return;

            //     let acr_doc = r.message;

            //     // Calculate available quantity
            //     let consumed_qty = acr_doc.consumed_qty || 0;
            //     let total_qty = acr_doc.qty || 0;
            //     let available_qty = total_qty - consumed_qty;
            //     let is_cwip = acr_doc.enable_cwip_accounting || 0;

            //     // Check if quantity is available
            //     if (available_qty <= 0 && !is_cwip) {
            //         frappe.msgprint({
            //             title: __('Not Available'),
            //             message: __('Asset Creation Request {0} has been fully consumed. Total Qty: {1}, Consumed: {2}', 
            //                 [acr, total_qty, consumed_qty]),
            //             indicator: 'red'
            //         });
            //         frm.set_value("custom_asset_creation_request", "");
            //         // return;
            //     }

            //     // Show available quantity
            //     frappe.msgprint({
            //         title: __('Available Quantity'),
            //         message: __('Total Qty: {0}<br>Consumed Qty: {1}<br><b>Available Qty: {2}</b>', 
            //             [total_qty, consumed_qty, available_qty]),
            //         indicator: 'blue'
            //     });

            //     frappe.db.get_value("Item", acr_doc.item, ["lead_time_days", "item_name"])
            //         .then(item_data => {

            //             frm.clear_table("items");
            //             frm.refresh_field("items");

            //             let is_asset = acr_doc.composite_item;

            //             // Use available quantity instead of total quantity
            //             if (is_asset) {
            //                 // For assets, add single row with available qty
            //                 add_item_row(frm, acr_doc, item_data, available_qty);
            //             } else {
            //                 // For non-assets, add multiple rows (qty = 1 each)
            //                 for (let i = 0; i < available_qty; i++) {
            //                     add_item_row(frm, acr_doc, item_data, 1);
            //                 }
            //             }

            //             frm.refresh_field("items");
            //         });
            // }


            callback: function (r) {
    if (!r.message) return;

    let acr_doc = r.message;

    let consumed_qty = acr_doc.consumed_qty || 0;
    let total_qty = acr_doc.qty || 0;
    let available_qty = total_qty - consumed_qty;
    let is_cwip = acr_doc.enable_cwip_accounting || 0;

    // ===============================
    // ✅ CWIP → SKIP ALL VALIDATIONS
    // ===============================
    if (!is_cwip) {
        // ❗ ALL validations only for NON-CWIP
        if (available_qty <= 0) {
            frappe.msgprint({
                title: __('Not Available'),
                message: __('Asset Creation Request {0} has been fully consumed.<br>Total Qty: {1}<br>Consumed Qty: {2}', 
                    [acr, total_qty, consumed_qty]),
                indicator: 'red'
            });
        }
    }

    // ===============================
    // ✅ ITEM FETCH SHOULD ALWAYS RUN
    // ===============================
    frappe.db.get_value("Item", acr_doc.item, ["lead_time_days", "item_name"])
        .then(item_data => {

            frm.clear_table("items");
            frm.refresh_field("items");

            let is_asset = acr_doc.composite_item;

            if (is_asset) {
                add_item_row(frm, acr_doc, item_data, available_qty > 0 ? available_qty : 1);
            } else {
                let qty_to_add = available_qty > 0 ? available_qty : 1;
                for (let i = 0; i < qty_to_add; i++) {
                    add_item_row(frm, acr_doc, item_data, 1);
                }
            }

            frm.refresh_field("items");
        });
}

        });
    },

    before_workflow_action(frm) {
        const action = frm.selected_workflow_action;
        console.log("Workflow action:", action);

        if (action !== "Reject") {
            return;
        }

        if (frm.doc.workflow_state === "Pending From Manager") {
            frappe.prompt(
                {
                    fieldname: "remarks",
                    label: "Manager Rejection Remarks",
                    fieldtype: "Small Text",
                    reqd: 1
                },
                (data) => {
                    frm.set_value("custom_reject_remarks", data.remarks);
                    frm.save();
                }
            );
            return false;
        }

        if (frm.doc.workflow_state === "Pending From Head") {
            frappe.prompt(
                {
                    fieldname: "remarks",
                    label: "Head Rejection Remarks",
                    fieldtype: "Small Text",
                    reqd: 1
                },
                (data) => {
                    frm.set_value("custom_head_reject_remarks", data.remarks);
                    frm.save();
                }
            );
            return false;
        }
    },

    refresh(frm) {
        console.log("----------------frm----------", frm);

        // Add custom button only for submitted documents
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button("Create RFQ Entry", function() {
                frappe.call({
                    method: "merai_newage.merai_newage.doctype.rfq_entry.rfq_entry.create_rfq_entry",
                    args: {source_name: frm.doc.name},
                    callback(r) {
                        frappe.set_route("Form", "RFQ Entry", r.message);
                    }
                });
            });
        }

        // Show ACR quantity status if linked
        if (frm.doc.custom_asset_creation_request && frm.doc.docstatus < 2) {
            show_acr_quantity_status(frm);
        }
    }
});

// Helper function to set requisitioner
function set_requisitioner(frm) {
    let user = frappe.session.user;
    console.log("user=====", user);
    
    frappe.db.get_list("Employee", {
        fields: ["name", "custom_user_email_for_creation"],
        filters: {
            user_id: user
        },
        limit: 1
    }).then(res => {
        if (res.length > 0) {
            frm.set_value("custom_requisitioner", res[0].name);
            frm.set_value("custom_requisitioner_email", res[0].custom_user_email_for_creation);
        }
    });
}

// Helper function to add item row
function add_item_row(frm, acr_doc, item_data, qty) {
    let row = frm.add_child("items");

    frappe.model.set_value(row.doctype, row.name, "item_code", acr_doc.item)
        .then(() => {
            frappe.model.set_value(row.doctype, row.name, "qty", qty);

            if (item_data?.message?.lead_time_days) {
                frappe.model.set_value(
                    row.doctype,
                    row.name,
                    "custom_lead_timein_days",
                    item_data.message.lead_time_days
                );
            }
        });
}

function show_acr_quantity_status(frm) {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Asset Creation Request",
            name: frm.doc.custom_asset_creation_request,
            fields: ["qty", "consumed_qty"]
        },
        callback: function(r) {
            if (r.message) {
                let total = r.message.qty || 0;
                let consumed = r.message.consumed_qty || 0;
                let available = total - consumed;
                
                frm.dashboard.add_indicator(
                    __('ACR Available Qty: {0} / {1}', [available, total]),
                    available > 0 ? 'blue' : 'red'
                );
            }
        }
    });
}

function set_segment_filter(frm) {
    frm.set_query("custom_segment_master", function() {
        console.log("Setting query for custom_segment_master with plant:", frm.doc.custom_plant);
        
        if (!frm.doc.custom_plant) {
            // If no plant selected, return empty result
            return {
                filters: {
                    "name": ["=", ""]  // This ensures nothing shows up
                }
            };
        }

        return {
            query: "merai_newage.overrides.material_request.get_segments_from_plant",
            filters: {
                custom_plant: frm.doc.custom_plant
            }
        };
    });
    
    // Refresh the field to apply the filter
    frm.refresh_field("custom_segment_master");
}
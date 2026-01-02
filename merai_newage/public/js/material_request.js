frappe.ui.form.on("Material Request", {
       custom_asset_creation_request(frm) {
        let acr = frm.doc.custom_asset_creation_request;
        if (!acr) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Asset Creation Request",
                name: acr
            },
            callback: function (r) {
                if (!r.message) return;

                let acr_doc = r.message;

                // Fetch item details including lead time
                frappe.db.get_value("Item", acr_doc.item, ["lead_time_days", "item_name"])
                    .then(item_data => {
                        // Clear existing items
                        frm.clear_table("items");
                        frm.refresh_field("items");

                        // Add item row and trigger item_code change
                        setTimeout(() => {
                            let row = frm.add_child("items");
                            frm.refresh_field("items");
                            
                            // Set item_code using model.set_value to trigger all events
                            frappe.model.set_value(row.doctype, row.name, "item_code", acr_doc.item)
                                .then(() => {
                                    // Set qty
                                    frappe.model.set_value(row.doctype, row.name, "qty", acr_doc.qty);
                                    
                                    // Set lead time if it exists
                                    if (item_data && item_data.message && item_data.message.lead_time_days) {
                                        frappe.model.set_value(row.doctype, row.name, "custom_lead_timein_days", item_data.message.lead_time_days);
                                    }
                                });
                        }, 100);
                    });
            }
        });
    },
    before_workflow_action(frm) {

        const action = frm.selected_workflow_action;
        console.log("Workflow action:", action);

        // Only for Reject
        if (action !== "Reject") {
            return;
        }

        // Manager rejection
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

        // Head rejection
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
    console.log("----------------frm----------",frm)
        // run only if field empty
        if (!frm.doc.custom_requisitioner) {

            // get logged-in user id
            let user = frappe.session.user;
            console.log("user=====",user)
            frappe.db.get_list("Employee", {
                fields: ["name","custom_user_email_for_creation"],
                filters: {
                    user_id: user
                },
                limit: 1
            }).then(res => {
                if (res.length > 0) {
                    frm.set_value("custom_requisitioner", res[0].name);
                    frm.set_value("custom_requisitioner_email",res[0].custom_user_email_for_creation)
                }
            });
        }
        if(frm.doc.docstatus==1){

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
    }
});

frappe.ui.form.on("Material Request", {
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
});

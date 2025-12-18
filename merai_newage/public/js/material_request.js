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
    }
});

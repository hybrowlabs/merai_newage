frappe.ui.form.on("Ticket Task Master", {
    refresh(frm) {
        frm._previous_workflow_state = frm.doc.workflow_state;
    },

    before_workflow_action: function(frm) {
        frm._previous_workflow_state = frm.doc.workflow_state;
        console.log("previous state captured:", frm._previous_workflow_state);

        if (
            frm.selected_workflow_action === "Resolve" ||
            frm.selected_workflow_action === "Send Material" ||
            frm.selected_workflow_action === "Acknowledge"
        ) {
            if (!frm.doc.remarks) {
                frappe.throw(__('Please fill in <b>Remarks</b> before proceeding.'));
            }
        }
    },

    after_workflow_action: function(frm) {
        console.log("frm.doc.workflow_state=========", frm.doc.workflow_state);
        console.log("previous state=========", frm._previous_workflow_state);

        if (frm.doc.workflow_state === "Approved") {

            frappe.call({
                method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.update_ticket_master",
                args: {
                    reference_name: frm.doc.ticket_master_reference || null,
                    task_doc: frm.doc,
                    previous_state: frm._previous_workflow_state
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Ticket Master updated successfully'),
                            indicator: 'green'
                        });

                        // Refresh Ticket Task Master doc
                        setTimeout(() => {
                            frm.reload_doc();
                        }, 1000);
                    }
                }
            });
        }
    }
});
// Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Ticket Task Master", {
	refresh(frm) {

	},

    after_workflow_action:function(frm){
        console.log("frm.doc.workflow_state=========",frm.doc.workflow_state)
        if(frm.doc.workflow_state === "Approved"){
``
    
            frappe.call({
                method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.update_ticket_master",
                args: {
                    reference_name: frm.doc.ticket_master_reference || null,
                    task_doc:frm.doc
                },
                callback:function(r){
                    if(r.message){
                        frappe.show_alert({
                            message: __('Ticket Master updated successfully'),
                            indicator: 'green'  
                        })
                    }
                }
            })
        }
    }

});

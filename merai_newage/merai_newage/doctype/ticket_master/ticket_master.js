// Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Ticket Master", {
    
    onload(frm){
         frm.set_query("robot_serial_no", () => {
            return {
                filters: [
                    ["Robot Tracker", "robot_status", "in", ["Installed", "Transfered"]]
                ]
            };
        });
        
         frm.set_query("surgery_no", () => {
            return {
                filters: {
                    installed_robot: frm.doc.robot_serial_no,
                    hospital_name:frm.doc.hospital_name
                }
            };
        });
        frm.set_query("assign_engineer", () => {
            return {
                filters: {
                    employment_type: "Backend Team"
                }
            };
        });
    },
	refresh(frm) {
    if (!frm.doc.raised_by) {
            let user = frappe.session.user;
            console.log("user=====",user)
            frappe.db.get_list("Employee", {
                fields: ["name"],
                filters: {
                    user_id: user
                },
                limit: 1
            }).then(res => {
                if (res.length > 0) {
                    frm.set_value("raised_by", res[0].name);
                }
            });
        }
	},
     robot_serial_no(frm) {
        if (!frm.doc.robot_serial_no) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Robot Tracker",
                name: frm.doc.robot_serial_no
            },
            callback: function(r) {
                if (r.message) {

                    let details = r.message.robot_tracker_details || [];

                    if (details.length > 0) {
                        let last_row = details[details.length - 1];

                        frm.set_value("hospital_name", last_row.location);
                    }
                }
            }
        });
    },
    // after_workflow_action(frm){
    //     if (frm.doc.workflow_state==="Pending From Backend Team"){
    //         frappe.call({
    //             method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.create_ticket_task",
    //             args: {
    //                 doc: frm.doc,
    //             },
    //             callback: function (r) {
    //                 if (r.message) {

    //                     frm.set_value("task_id", r.message);

    //                         frm.save();
    //                     } 
    //             }
    //         })
    //     }
    // }
    after_workflow_action(frm){
    if (frm.doc.workflow_state === "Pending From Backend Team"){
        frappe.call({
            method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.create_ticket_task",
            args: {
                doc: frm.doc,
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value("task_id", r.message);
                    
                    // Save the document first
                    frm.save().then(() => {
                        // Then send notification after task_id is saved
                        frappe.call({
                            method: "send_backend_notification",
                            doc: frm.doc,
                            callback: function(res) {
                                if (res.message && res.message.success) {
                                    frappe.show_alert({
                                        message: __('Engineer notified successfully'),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    });
                } 
            }
        });
    }
}
});

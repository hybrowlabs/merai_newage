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
        frm.set_query("backend_team_engineer", () => {
            return {
                filters: {
                    employment_type: "Backend Team"
                }
            };
        });
        frm.set_query("software_team_engineer", () => {
            return {
                filters: {
                    employment_type: "Software Team"
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

//     refresh(frm) {
//     // Remove old style and re-inject to ensure it applies
//     const existingStyle = document.getElementById("ticket-master-field-style");
//     if (existingStyle) existingStyle.remove();

//     const style = document.createElement("style");
//     style.id = "ticket-master-field-style";
//     style.textContent = `
//         .layout-main .form-control,
//         .layout-main input[type="text"],
//         .layout-main input[type="number"],
//         .layout-main input[type="email"],
//         .layout-main input[type="date"],
//         .layout-main input[type="time"],
//         .layout-main input[type="search"],
//         .layout-main textarea,
//         .layout-main select,
//         .layout-main .ql-editor,
//         .layout-main .ql-container,
//         .layout-main .ql-toolbar,
//         .layout-main .awesomplete input,
//         .layout-main .input-with-feedback,
//         .layout-main [contenteditable="true"] {
//             border: 1px solid #000000 !important;
//             border-radius: 4px !important;
//         }

//         .layout-main .form-control:focus,
//         .layout-main input:focus,
//         .layout-main textarea:focus,
//         .layout-main .ql-editor:focus {
//             border: 1px solid #000000 !important;
//             box-shadow: 0 0 0 1px rgba(0,0,0,0.15) !important;
//             outline: none !important;
//         }

//         .layout-main .grid-row .form-control,
//         .layout-main .grid-row input,
//         .layout-main .grid-row textarea,
//         .layout-main .grid-row select {
//             border: 1px solid #000000 !important;
//             border-radius: 1px !important;
//         }
//     `;
//     document.head.appendChild(style);

//     if (!frm.doc.raised_by) {
//         let user = frappe.session.user;
//         frappe.db.get_list("Employee", {
//             fields: ["name"],
//             filters: { user_id: user },
//             limit: 1
//         }).then(res => {
//             if (res.length > 0) {
//                 frm.set_value("raised_by", res[0].name);
//             }
//         });
//     }
//     setup_close_intercept(frm);

//     // Inside refresh(frm):
// if (frm.doc.workflow_state === "Closed") {
//     frm.toggle_reqd("issue_type", false);
//     frm.toggle_reqd("backend_team_engineer", false);
//     frm.toggle_reqd("system_admin_remarks", false); // already closed, no need
// } else {
//     frm.toggle_reqd("issue_type", true);
//     frm.toggle_reqd("backend_team_engineer", true);
//     frm.toggle_reqd("system_admin_remarks", false);
// }

// },
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
    after_workflow_action(frm) {
    if (frm.doc.workflow_state === "Pending From Backend Team") {

        frappe.call({
            method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.create_ticket_task",
            args: {
                doc: frm.doc,
            },
            callback: function (r) {

                if (r.message) {

                    // For Software + Service
                    if (frm.doc.issue_type === "Software + Service") {

                        frm.set_value("task_id", r.message.backend_task_id);
                        frm.set_value("software_task_id", r.message.software_task_id);

                    } else {

                        // Existing flow
                        frm.set_value("task_id", r.message);

                    }

                    frm.save().then(() => {

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


    if (frm.doc.workflow_state === "Raised New Ticket") {

            frappe.call({
                method: "merai_newage.merai_newage.doctype.ticket_master.ticket_master.create_ticket_again",
                args: {
                    old_doc: frm.doc.name
                },
                callback: function (r) {

                    if (r.message) {

                        frappe.model.with_doctype("Ticket Master", function () {

                            let doc = frappe.model.get_new_doc("Ticket Master");

                            doc.robot_serial_no = r.message.robot_serial_no;
                            doc.issue_reported = r.message.issue_reported;
                            doc.ticket_subject = r.message.ticket_subject;
                            doc.old_ticket_reference = r.message.old_ticket_reference;
                            doc.original_ticket_id = r.message.original_ticket_id;
                            doc.naming_series = r.message.naming_series;
                            doc.surgery_no=r.message.surgery_no

                            frappe.set_route("Form", "Ticket Master", doc.name);

                            frappe.show_alert({
                                message: __('New Ticket Draft Opened'),
                                indicator: 'green'
                            });
                        });
                    }
                }
            });
            
}

// if (frm.doc.workflow_state === "Raised New Ticket") {

//     frappe.call({
//         method: "merai_newage.merai_newage.doctype.ticket_master.ticket_master.create_ticket_again",
//         args: {
//             old_doc: frm.doc.name
//         },
//         callback: function (r) {

//             if (r.message) {

//                 // create new local doc
//                 let doc = frappe.model.get_new_doc("Ticket Master");

//                 // set values
//                 doc.robot_serial_no = r.message.robot_serial_no;
//                 doc.issue_reported = r.message.issue_reported;
//                 doc.ticket_subject = r.message.ticket_subject;
//                 doc.old_ticket_reference = r.message.old_ticket_reference;
//                 doc.surgery_no = r.message.surgery_no;

//                 // DO NOT set name here (important)
//                 doc.custom_retry_name = r.message.new_name; 
//                 // create custom field to show preview

//                 // open form
//                 frappe.set_route("Form", "Ticket Master", doc.name);

//                 frappe.show_alert({
//                     message: __('New Ticket Draft Opened'),
//                     indicator: 'green'
//                 });
//             }
//         }
//     });
// }



}
});


function setup_plus_button(frm, fieldname) {
    setTimeout(() => {
        const field = frm.fields_dict[fieldname];
        if (!field) return;

        const $wrapper = $(field.$input_wrapper);
        const $tsInput = $wrapper.find(".ts-input");

        if (!$tsInput.length) return;

        // Remove any existing + button to avoid duplicates
        $wrapper.find(".multiselect-plus-btn").remove();

        // Create + button
        const $plusBtn = $(`<span class="multiselect-plus-btn" title="Add more">＋</span>`);

        // Append + button after the ts-input container
        $tsInput.after($plusBtn);

        function update_input_visibility() {
            const hasItems = $tsInput.find(".item").length > 0;
            if (hasItems) {
                $tsInput.addClass("multiselect-hide-input");
                $plusBtn.show();
            } else {
                $tsInput.removeClass("multiselect-hide-input");
                $plusBtn.hide();
            }
        }

        // On + click, show input and focus
        $plusBtn.on("click", function () {
            $tsInput.removeClass("multiselect-hide-input");
            $tsInput.find("input").css({ width: "", opacity: "", "pointer-events": "" }).focus();
            $plusBtn.hide();
        });

        // Watch for tag additions/removals using MutationObserver
        const observer = new MutationObserver(() => {
            update_input_visibility();
        });

        observer.observe($tsInput[0], { childList: true, subtree: true });

        // Initial state
        update_input_visibility();

        // When user selects an option, hide input again
        $tsInput.find("input").on("blur", function () {
            setTimeout(update_input_visibility, 300);
        });

    }, 600);
}


function toggle_mandatory_fields(frm) {
    const state = frm.doc.workflow_state;
    const is_closing = state === "Closed"; // match your exact workflow state name

    // Fields to make NOT mandatory when closing
    const engineer_fields = ["issue_type", "backend_team_engineer"];

    engineer_fields.forEach(f => {
        frm.toggle_reqd(f, !is_closing);
    });

    // Remarks mandatory only when closing
    frm.toggle_reqd("system_admin_remarks", is_closing); // change field name if different
}
function setup_close_intercept(frm) {
    setTimeout(() => {
        $(document).off("click.close_intercept").on("click.close_intercept",
            ".actions-btn-group .dropdown-item, .btn-workflow-action",
            function () {
                const action = $(this).text().trim();

                if (action === "Close") {
                    // Immediately strip reqd from df before Frappe validates
                    ["issue_type", "backend_team_engineer", "priorty"].forEach(f => {
                        if (frm.fields_dict[f]) {
                            frm.fields_dict[f].df.reqd = 0;
                            frm.fields_dict[f].set_mandatory_class(false);
                        }
                    });

                    if (frm.fields_dict["system_admin_remarks"]) {
                        frm.fields_dict["system_admin_remarks"].df.reqd = 1;
                    }

                } else if (action === "Assign Engineer") {
                    ["issue_type", "backend_team_engineer", "priorty"].forEach(f => {
                        if (frm.fields_dict[f]) {
                            frm.fields_dict[f].df.reqd = 1;
                            frm.fields_dict[f].set_mandatory_class(true);
                        }
                    });

                    if (frm.fields_dict["system_admin_remarks"]) {
                        frm.fields_dict["system_admin_remarks"].df.reqd = 0;
                    }
                }
            }
        );
    }, 800);
}
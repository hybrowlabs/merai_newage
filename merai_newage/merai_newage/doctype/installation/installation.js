// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Installation", {
	refresh(frm) {

	},
});

frappe.ui.form.on("Safety Check And Precautions", {
    verify(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.safety_steps) {
            frappe.msgprint("Please select Safety Steps first.");
            return;
        }

        frappe.call({
            method: "merai_newage.merai_newage.doctype.installation.installation.get_safety_check_items",
            args: {
                safety_steps: row.safety_steps
            },
            callback(r) {
                if (!r.message) {
                    frappe.msgprint("No Safety Checks found.");
                    return;
                }

                show_safety_popup(r.message, frm, row);
            }
        });
    }
});


// function show_safety_popup(items, frm, row) {
//     let fields = [];

//     items.forEach(item => {
//         fields.push({
//             fieldname: item.check_name,
//             label: item.check_name,
//             fieldtype: "Select",
//             options: "Yes\nNo",
//             reqd: 1
//         });
//     });

//     let d = new frappe.ui.Dialog({
//         title: "Safety Check Verification",
//         fields: fields,
//         primary_action_label: "Save",
//         primary_action(values) {
//             console.log("Selected Values:", values);

//             // If you want to store results in row fields:
//             row.verification_result = JSON.stringify(values);
//             frm.refresh_fields("safety_check_and_precautions");

//             d.hide();
//         }
//     });

//     d.show();
// }


function show_safety_popup(items, frm, row) {

    let question_html = "<ul style='padding-left:15px;'>";

    items.forEach((item, idx) => {
        question_html += `<li style="margin-bottom:8px;">
            ${item.check_name}
        </li>`;
    });

    question_html += "</ul>";

    let dialog = new frappe.ui.Dialog({
        title: "Safety Check Verification",
        fields: [
            {
                fieldname: "questions",
                fieldtype: "HTML",
                options: `<div><b>Please verify the following steps:</b>${question_html}</div>`
            },
            {
                fieldname: "verification",
                label: "Verification Result",
                fieldtype: "Select",
                options: "Yes\nNo",
                reqd: 1
            },
            {
                fieldname: "remarks",
                label: "Remarks",
                fieldtype: "Small Text"
            }
        ],
        primary_action_label: "Save",
        primary_action(values) {

            row.remarks = values.remarks;  
            row.status = values.verification || "";  

            frm.refresh_field("safety_check_and_precautions");

            dialog.hide();
        }
    });

    dialog.show();
}



frappe.ui.form.on("Performance Check Details", {
    verify(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.performance_check) {
            frappe.msgprint("Please select Performance Check first.");
            return;
        }

        frappe.call({
            method: "merai_newage.merai_newage.doctype.installation.installation.get_safety_check_items",
            args: {
                safety_steps: row.performance_check
            },
            callback(r) {
                if (!r.message) {
                    frappe.msgprint("No Safety Checks found.");
                    return;
                }

                show_safety_popup(r.message, frm, row);
            }
        });
    }
});

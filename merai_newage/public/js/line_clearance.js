// frappe.ui.form.on("Job Card", {
//     refresh(frm) {
//         console.log("Job Card form refreshed");
//         if (frm.doc.operation) {
//             frappe.db.get_doc("Operation", frm.doc.operation).then(op => {
//                 if (op.custom_line_clearance_template) {
//                     let template_name = op.custom_line_clearance_template;

//                     frappe.db.get_doc("Line Clearance Template", template_name).then(template => {
//                         frm.clear_table("custom_line_clearance_checklist");

//                         (template.line_clearence_checkpoints || []).forEach(row => {
//                             let child = frm.add_child("custom_line_clearance_checklist");
//                             child.line_clearance_criteria = row.line_clearance_criteria;
//                             child.yesno = row.yesno;
//                         });

//                         frm.refresh_field("custom_line_clearance_checklist");
//                     });
//                 }
//             });
//         }
//     }
// });

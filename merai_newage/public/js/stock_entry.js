// frappe.ui.form.on("Stock Entry", {
//     onload: function(frm) {
//         check_batch_number(frm);
//     }
// });

// function check_batch_number(frm) {
//     if (frm.doc.stock_entry_type === "Manufacture" && frm.doc.work_order) {
//         frappe.db.get_doc("Work Order", frm.doc.work_order).then(work_order => {
//             let wo_item = work_order.production_item;
//             let wo_batch = work_order.custom_batch;

//             frm.doc.items.forEach(row => {
//                 if (row.item_code === wo_item) {
//                     console.log("=============",row.item_code)
//                     frappe.model.set_value(row.doctype, row.name, "batch_no", wo_batch);
//                 }
//             });
//         });
//     }
// }

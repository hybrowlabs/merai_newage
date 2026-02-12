// console.log("🔥 Custom request_for_quotation.js loaded");

// frappe.ui.form.on("Request for Quotation", {
//   refresh: function (frm) {
//     sync_rfq_workflow_table(frm);
//   },

//   after_save: function (frm) {
//     sync_rfq_workflow_table(frm);
//   }
// });

// function sync_rfq_workflow_table(frm) {
//   if (frm.is_new()) return;
//   if (frm.__sync_in_progress) return;

//   frm.__sync_in_progress = true;

//   frappe.call({
//     method: "merai_newage.overrides.workflow_attachment.sync_workflow_attachment",
//     args: {
//       doctype: frm.doc.doctype,
//       docname: frm.doc.name
//     },
//     callback: function (r) {
//       if (r && r.message && r.message.added) {
//         frm.reload_doc();
//       }
//     },
//     always: function () {
//       frm.__sync_in_progress = false;
//     }
//   });
// }

console.log("🔥 Custom rfq.js loaded");

frappe.ui.form.on("Request for Quotation", {
  refresh: function (frm) {
    merai.sync_workflow_attachment_table(frm);
  },

  after_save: function (frm) {
    merai.sync_workflow_attachment_table(frm);
  }
});

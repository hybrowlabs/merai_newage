console.log("🔥 workflow_attachment_utils.js loaded");

window.merai = window.merai || {};

merai.sync_workflow_attachment_table = function (frm) {

  if (frm.is_new()) return;
  if (frm.__sync_in_progress) return;

  frm.__sync_in_progress = true;

  frappe.call({
    method: "merai_newage.overrides.workflow_attachment.sync_workflow_attachment",
    args: {
      doctype: frm.doc.doctype,
      docname: frm.doc.name
    },
    callback: function (r) {

      if (r?.message && (r.message.added || r.message.removed)) {
        frm.reload_doc();
      }

    },
    always: function () {
      frm.__sync_in_progress = false;
    }
  });

};

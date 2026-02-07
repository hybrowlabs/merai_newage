frappe.ui.form.on("Workflow Attachment", {
  view(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.path) window.open(row.path, "_blank");
    else frappe.msgprint("Attachment path not found");
  }
});
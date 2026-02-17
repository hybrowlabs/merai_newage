frappe.ui.form.on("Workflow Attachment", {
  view(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.path) window.open(row.path, "_blank");
    else frappe.msgprint("Attachment path not found");
  }
});


// frappe.ui.form.on("Workflow Attachment", {
//   view(frm, cdt, cdn) {
//     console.log("VIEW CLICKED");

//     const row = locals[cdt][cdn];

//     if (!row.path) {
//       frappe.msgprint("Attachment path not found");
//       return;
//     }

//     let file_url = row.path;

//     // Handle private files properly
//     if (row.path.startsWith("/private/")) {
//       file_url = `/api/method/frappe.utils.file_manager.download_file?file_url=${encodeURIComponent(row.path)}`;
//     }

//     window.open(file_url, "_blank");
//   }
// });

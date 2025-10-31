frappe.ui.form.on("Dispatch Checklist Details", {
    product_name: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];  // Get the current child row
        console.log("row---",row)
        if (row.product_name) {
            // Fetch description from Item doctype
            frappe.db.get_value("Item", row.product_name, "description")
                .then(r => {
                    if (r && r.message && r.message.description) {
                        frappe.model.set_value(cdt, cdn, "product_description", r.message.description);
                    } else {
                        frappe.model.set_value(cdt, cdn, "product_description", "");
                    }
                });
        } else {
            frappe.model.set_value(cdt, cdn, "product_description", "");
        }
    }
});

frappe.ui.form.on("Purchase Order", {
    onload: function(frm) {
        if (frm.doc.custom_asset_creation_request) {
            frm.set_value("custom_purchase_type", "Asset");
        }
    }
});


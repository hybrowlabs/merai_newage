frappe.ui.form.on("Purchase Order", {
    custom_asset_creation_request: function(frm) {
        if (
            frm.doc.custom_asset_creation_request &&
            !frm.doc.custom_purchase_type
        ) {
            frm.set_value("custom_purchase_type", "Asset");
        }
    }
});

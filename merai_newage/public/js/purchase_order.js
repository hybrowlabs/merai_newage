frappe.ui.form.on("Purchase Order", {
    custom_asset_creation_request: function(frm) {

            frm.set_value("custom_purchase_type", "Asset");
        
    }
});

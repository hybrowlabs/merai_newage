frappe.ui.form.on("Asset", {
    refresh(frm){
        frm.set_df_property("purchase_receipt", "reqd", 0);
        frm.set_df_property("purchase_date", "reqd", 0);        
        frm.set_df_property("purchase_invoice", "reqd", 0);
    }
});

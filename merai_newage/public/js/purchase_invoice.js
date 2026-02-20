frappe.ui.form.on("Purchase Invoice", {

    onload(frm) {
        fetch_supplier_invoice_details(frm);
    },

    custom_purchase_receipt(frm) {
        fetch_supplier_invoice_details(frm);
    }

});


function fetch_supplier_invoice_details(frm) {

    if (!frm.doc.custom_purchase_receipt) return;

    // frm.set_value("custom_purchase_type", "General");

    frappe.db.get_value(
        "Purchase Receipt",
        frm.doc.custom_purchase_receipt,
        ["custom_supplier_document_no", "custom_supplier_document_date"]
    ).then(r => {
        console.log(r);
        if (!r.message) return;

        if (!frm.doc.custom_supplier_document_no && r.message.custom_supplier_document_no) {
            frm.set_value("bill_no", r.message.custom_supplier_document_no);
        }

        if (!frm.doc.custom_supplier_document_date && r.message.custom_supplier_document_date) {
            frm.set_value("bill_date", r.message.custom_supplier_document_date);
        }

    });

}

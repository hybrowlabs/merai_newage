frappe.ui.form.on("Purchase Receipt", {
    onload(frm) {

        if (
            frm.doc.items &&
            frm.doc.items.length > 0 &&
            !frm.doc.custom_supplier_document_no &&
            !frm.doc.custom_supplier_document_date
        ) {

            frappe.call({
                method: "merai_newage.overrides.purchase_receipt.get_supplier_document_details",
                args: {
                    doc: frm.doc
                },
                callback: function (r) {

                    if (r.message) {

                        frm.set_value(
                            "custom_supplier_document_no",
                            r.message.invoice_no
                        );

                        frm.set_value(
                            "custom_supplier_document_date",
                            r.message.invoice_date
                        );

                    }
                }
            });

        }

    }
});
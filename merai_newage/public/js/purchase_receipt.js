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
         if (frm.doc.custom_gate_entry_no) {

            frappe.call({
                method: "merai_newage.overrides.purchase_receipt.get_po_details_from_gate_entry",
                args: {
                    gate_entry: frm.doc.custom_gate_entry_no
                },
                callback: function (r) {

                    if (r.message) {

                        frm.set_value("cost_center", r.message.cost_center);
                        frm.set_value("plant", r.message.plant);

                    }
                }
            });

        }

    }
});
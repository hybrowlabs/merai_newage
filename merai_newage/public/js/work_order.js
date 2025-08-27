frappe.ui.form.on("Work Order", {
    refresh: function (frm) {
        if (frm.doc.docstatus ==1) {
            frm.add_custom_button("Print Work Order", function () {
                frappe.call({
                    method: "merai_newage.overrides.work_order.print_work_order_async",
                    args: {
                        name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Printing Work Order...",
                    callback: function (response) {
                        window.open(window.location.origin + response.filecontent)
                        // frappe.msgprint("Printing Work Order....<br> request queued successfully!");
                    }
                });
            })
        }
    }})
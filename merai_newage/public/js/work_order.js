frappe.ui.form.on("Work Order", {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button("Print DHR", function () {
                frappe.call({
                    method: "merai_newage.overrides.work_order.print_work_order_async",
                    args: {
                        name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Printing DHR...",
                    callback: function (response) {
                        window.open(window.location.origin + response.filecontent);
                    }
                });
            });
        }
        
        if (frm.doc.docstatus == 1 && frm.doc.custom_is_full_dhr === 1) {
            frm.add_custom_button("Print Full DHR", function () {
                frappe.call({
                    method: "merai_newage.overrides.work_order.print_full_bmr",
                    args: {
                        name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Printing Full DHR...",
                    callback: function (response) {
                        window.open(window.location.origin + response.filecontent);
                    }
                });
            });
        }
    }
});
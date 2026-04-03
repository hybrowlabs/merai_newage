frappe.require("/assets/merai_newage/js/pre_alert_rodtep_utils.js");

frappe.ui.form.on('Pre Alert', {

    refresh: function (frm) {
		if (!frm._attachment_sync_bound && frm.attachments) {
			frm._attachment_sync_bound = true;

			frm.attachments.on("change", function () {
				if (merai?.sync_workflow_attachment_table) {
					merai.sync_workflow_attachment_table(frm);
				}
			});
		}
	},

    after_save: function(frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
    },

    on_submit: function(frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
    },
    rfq_number: function(frm) {
        fetch_supplier_quotation(frm);
    },
    supplier: function(frm) {
        fetch_supplier_quotation(frm);
    }

});

function fetch_supplier_quotation(frm) {
    if (!frm.doc.rfq_number) return;

    frappe.call({
        method: "merai_newage.overrides.pre_alert.get_latest_supplier_quotation",
        args: {
            rfq: frm.doc.rfq_number,
            supplier: frm.doc.supplier || null
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("custom_supplier_quotation", r.message);
            }
        }
    });
}

frappe.ui.form.on('Pre-Alert Item Details', {
    igcr: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.igcr) {
            frappe.model.set_value(cdt, cdn, 'category', '9');
            frm.fields_dict.item_details.grid.toggle_enable('category', false);
        } else {
            frappe.model.set_value(cdt, cdn, 'category', null);
            frm.fields_dict.item_details.grid.toggle_enable('category', true);
        }
    }
});

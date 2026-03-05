frappe.ui.form.on("Pickup Request", {
	onload: function (frm) {
		frappe.require("/assets/merai_newage/js/dimension_calculation.js");
	},

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

	after_save: function (frm) {
		if (merai?.sync_workflow_attachment_table) {
			merai.sync_workflow_attachment_table(frm);
		}
	},

	on_submit: function (frm) {
		if (merai?.sync_workflow_attachment_table) {
			merai.sync_workflow_attachment_table(frm);
		}
	},
});

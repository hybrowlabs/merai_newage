// console.log("🔥 Custom pickup_request.js loaded");

// frappe.ui.form.on("Pickup Request", {
//   onload: function (frm) {
//     frappe.require("/assets/merai_newage/js/dimension_calculation.js");
//   },

//   refresh: function (frm) {
//     sync_workflow_table(frm);
//   },

//   after_save: function (frm) {
//     sync_workflow_table(frm);
//   }
// });

// function sync_workflow_table(frm) {
//   if (frm.is_new()) return;
//   if (frm.__sync_in_progress) return;

//   frm.__sync_in_progress = true;

//   frappe.call({
//     method: "merai_newage.overrides.workflow_attachment.sync_workflow_attachment",
//     args: {
//       doctype: frm.doc.doctype,
//       docname: frm.doc.name
//     },
//     callback: function (r) {
//       if (r && r.message && r.message.added) {
//         frm.reload_doc();
//       }
//     },
//     always: function () {
//       frm.__sync_in_progress = false;
//     }
//   });
// }

// console.log("🔥 Custom pickup_request.js loaded");

// frappe.ui.form.on("Pickup Request", {
//   onload: function (frm) {
//     frappe.require("/assets/merai_newage/js/dimension_calculation.js");
//   },

//   // refresh: function (frm) {
//   //   merai.sync_workflow_attachment_table(frm);
//   // },

//   after_save: function (frm) {
//     merai.sync_workflow_attachment_table(frm);
//   },
//   on_submit: function (frm) {
//     merai.sync_workflow_attachment_table(frm);
//   }
// });

console.log("🔥 Custom pickup_request.js loaded");

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

// console.log("🔥 Custom rfq.js loaded");

// frappe.ui.form.on("Request for Quotation", {

//   refresh: function (frm) {

//     frm.remove_custom_button("Revise RFQ");
//     frm.remove_custom_button("Revision History", "View");

//     if (frm.doc.docstatus === 1 && frm.doc.custom_is_latest_revision) {

//       frm.add_custom_button("Revise RFQ", function () {

//         frappe.confirm(
//           "Are you sure you want to revise this RFQ?",
//           function () {

//             frappe.call({
//               method: "merai_newage.overrides.rfq.revise_rfq",
//               args: { rfq_name: frm.doc.name },
//               freeze: true,
//               freeze_message: "Creating Revision..."
//             }).then(r => {

//               if (r.message) {
//                 frappe.show_alert({
//                   message: "Revision Created Successfully",
//                   indicator: "green"
//                 });

//                 frappe.set_route("Form", "Request for Quotation", r.message);
//               }

//             });

//           }
//         );

//       }).addClass("btn-primary");


//       frm.add_custom_button("Revision History", function () {

//         frappe.call({
//           method: "merai_newage.overrides.rfq.get_rfq_revisions",
//           args: { rfq_name: frm.doc.name }
//         }).then(r => {

//           if (!r.message) return;

//           let data = r.message.revisions || [];

//           if (!data.length) {
//             frappe.msgprint("No Revisions Found");
//             return;
//           }

//           let html = `
//             <div style="max-height:400px;overflow:auto;">
//               <table class="table table-bordered">
//                 <thead>
//                   <tr>
//                     <th style="width:10%; text-align:center;">#</th>
//                     <th>Revision Code</th>
//                     <th>RFQ Name</th>
//                     <th>Created On</th>
//                   </tr>
//                 </thead>
//                 <tbody>
//           `;

//           data.forEach((row, i) => {
//             html += `
//               <tr>
//                 <td style="text-align:center;">${i + 1}</td>
//                 <td><b>${row.custom_revision_code || "-"}</b></td>
//                 <td>
//                   <a href="/app/request-for-quotation/${row.name}" target="_blank">
//                     ${row.name}
//                   </a>
//                 </td>
//                 <td>${frappe.datetime.str_to_user(row.creation)}</td>
//               </tr>
//             `;
//           });

//           html += `
//                 </tbody>
//               </table>
//             </div>
//           `;

//           let d = new frappe.ui.Dialog({
//             title: "Revision History",
//             fields: [
//               { fieldtype: "HTML", fieldname: "revision_table" }
//             ]
//           });

//           d.fields_dict.revision_table.$wrapper.html(html);
//           d.show();

//         });

//       }, __("View"));
//     }
//   },

//   after_save: function (frm) {
//       merai.sync_workflow_attachment_table(frm);
//   },

//   on_submit: function (frm) {
//       merai.sync_workflow_attachment_table(frm);
//   }

// });


console.log("🔥 Custom rfq.js loaded");

frappe.ui.form.on("Request for Quotation", {

  refresh: function (frm) {

    frm.remove_custom_button("Revise RFQ");
    frm.remove_custom_button("Revision History", "View");

    if (!frm._attachment_sync_bound && frm.attachments) {

      frm._attachment_sync_bound = true;

      frm.attachments.on("change", function () {

        if (merai?.sync_workflow_attachment_table) {
          merai.sync_workflow_attachment_table(frm);
        }

      });
    }

    if (frm.doc.docstatus === 1 && frm.doc.custom_is_latest_revision) {

      frm.add_custom_button("Revise RFQ", function () {

        frappe.confirm(
          "Are you sure you want to revise this RFQ?",
          function () {

            frappe.call({
              method: "merai_newage.overrides.rfq.revise_rfq",
              args: { rfq_name: frm.doc.name },
              freeze: true,
              freeze_message: "Creating Revision..."
            }).then(r => {

              if (r.message) {
                frappe.show_alert({
                  message: "Revision Created Successfully",
                  indicator: "green"
                });

                frappe.set_route("Form", "Request for Quotation", r.message);
              }

            });

          }
        );

      }).addClass("btn-primary");

      frm.add_custom_button("Revision History", function () {

        frappe.call({
          method: "merai_newage.overrides.rfq.get_rfq_revisions",
          args: { rfq_name: frm.doc.name }
        }).then(r => {

          if (!r.message) return;

          let data = r.message.revisions || [];

          if (!data.length) {
            frappe.msgprint("No Revisions Found");
            return;
          }

          let html = `
            <div style="max-height:400px;overflow:auto;">
              <table class="table table-bordered">
                <thead>
                  <tr>
                    <th style="width:10%; text-align:center;">#</th>
                    <th>Revision Code</th>
                    <th>RFQ Name</th>
                    <th>Created On</th>
                  </tr>
                </thead>
                <tbody>
          `;

          data.forEach((row, i) => {
            html += `
              <tr>
                <td style="text-align:center;">${i + 1}</td>
                <td><b>${row.custom_revision_code || "-"}</b></td>
                <td>
                  <a href="/app/request-for-quotation/${row.name}" target="_blank">
                    ${row.name}
                  </a>
                </td>
                <td>${frappe.datetime.str_to_user(row.creation)}</td>
              </tr>
            `;
          });

          html += `
                </tbody>
              </table>
            </div>
          `;

          let d = new frappe.ui.Dialog({
            title: "Revision History",
            fields: [
              { fieldtype: "HTML", fieldname: "revision_table" }
            ]
          });

          d.fields_dict.revision_table.$wrapper.html(html);
          d.show();

        });

      }, __("View"));
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
  }

});

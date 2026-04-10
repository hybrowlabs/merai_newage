frappe.ui.form.on("Request for Quotation", {

  validate(frm) {
        const now = frappe.datetime.now_datetime();

        if (frm.doc.custom_quotation_deadline1) {
            if (frm.doc.custom_quotation_deadline1 <= now) {
                frappe.msgprint("Warning: Deadline already passed.");
            }
        }
    },

  refresh: function (frm) {

    if (frm.is_new()) return;
    if (frm.doc.docstatus !== 1) return;
    if (!frm.doc.custom_quotation_deadline1) return;

    // prevent multiple intervals
    if (frm._countdown_interval) {
      clearInterval(frm._countdown_interval);
    }

    function updateCountdown(){
      let deadline = moment(frm.doc.custom_quotation_deadline1);
      let now1 = moment();

      let diff = deadline.diff(now1, 'seconds');
      let display = "";

      if (diff <= 0) {
        display = "Expired";

        if (!frm._expiry_synced) {
          frm._expiry_synced = true;

          frappe.call({
            method: "merai_newage.merai_newage.utils.rfq_expiry.update_rfq_status",
            args: { name: frm.doc.name }
          }).then(() => {
            frm.reload_doc();
          });
        }

      } else if (diff > 86400) {
        let days = Math.floor(diff / 86400);
        let hours = Math.floor((diff % 86400) / 3600);
        display = `${days}d ${hours}h left`;

      } else if (diff > 3600) {
          let hours = Math.floor(diff / 3600);
          let mins = Math.floor((diff % 3600) / 60);
          display = `${hours}h ${mins}m left`;

      } else if (diff > 60) {
          let mins = Math.floor(diff / 60);
          let secs = diff % 60;
          display = `${mins}m ${secs}s left`;

      } else {
          display = `${diff}s left`;
      }

      //UI update only (NO dirty form)
      frm.fields_dict.custom_remaining_time.$wrapper
        .find('.control-value')
        .text(display);
    }
    updateCountdown();
    frm._countdown_interval = setInterval(updateCountdown, 1000);

    const now = frappe.datetime.now_datetime();

        if (frm.doc.custom_quotation_deadline1 &&
            frm.doc.custom_quotation_deadline1 <= now) {

            frm.dashboard.set_headline_alert(
                "This RFQ has expired",
                "red"
            );
        }
    // Revise RFQ 
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
  },

  // Filter Service provider on change of these fields
  custom_select_service: function(frm) {
    if (!frm.doc.custom_select_service) {
        frm.clear_table("suppliers");
        frm.refresh_field("suppliers");
        return;
    }

    let service_map = {
        "Send Notification To All Service Provider": "All Service Provider",
        "Send Notification To Specific Premium Service Provider": "Premium Service Provider",
        "Send Notification To Specific Courrier Partner": "Courrier Partner",
        "Send Notification To ADHOC Partner": "ADHOC Partner"
    };

    let selected_type = service_map[frm.doc.custom_select_service];

    if (!selected_type) {
        frm.clear_table("suppliers");
        frm.refresh_field("suppliers");
        return;
    }

    // Child table clear karo
    frm.clear_table("suppliers");

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Supplier",
            filters: {
                custom_service_provider_type: selected_type
            },
            fields: ["name", "supplier_name"]
        },
        callback: function(r) {
            if (r.message) {
                r.message.forEach(supplier => {
                    let row = frm.add_child("suppliers");
                    row.supplier = supplier.name;
                    row.supplier_name = supplier.supplier_name;
                });

                frm.refresh_field("suppliers");
            }
        }
    });
}

});

// frappe.listview_settings['Request for Quotation'] = {

//     // Quotation deadline
//     add_fields: ["custom_quotation_deadline1"],

//     get_indicator: function(doc) {
//         let now = frappe.datetime.now_datetime();

//         if (doc.custom_quotation_deadline1 &&
//             doc.custom_quotation_deadline1 <= now) {

//             return ['Expired', 'red'];
//         }

//         return [__(doc.status), 'blue'];
//     }
// };
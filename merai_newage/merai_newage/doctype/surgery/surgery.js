frappe.ui.form.on("Surgery", {
    onload(frm) {
        frm.set_value("sales_owner", frappe.session.user);

        frm.set_query("installed_robot", () => {
            return {
                filters: [
                    ["Robot Tracker", "robot_status", "in", ["Installed", "Transfered"]]
                ]
            };
        });

        frm.set_query("contactdocotoroperatorsurgeon", () => {
            return {
                filters: [
                    ["Contact", "custom_contact_type", "=", "Doctor/Operator/Surgeon"]
                ]
            };
        });
        frm.set_query("csrs", () => {
            return {
                filters: [
                    ["Contact", "custom_contact_type", "=", "CSR"]
                ]
            };
        });
        frm.set_query("clinical_application_specialists", () => {
            return {
                filters: [
                    ["Contact", "custom_contact_type", "=", "Clinical Specialist"]
                ]
            };
        });
    },
    installed_robot:function(frm){
        frappe.call({
                method: "merai_newage.merai_newage.doctype.surgery.surgery.get_robot_tracker_data",
                args: {
                    doc: JSON.stringify(frm.doc)
                },
                callback: function (r) {
                    if (r.message) {

                        frm.set_value("hospital_name", r.message.from_location);
                    }
                }
            });    },
        robot_surgery_end_time:function(frm){
            frappe.call({
                method: "merai_newage.merai_newage.doctype.surgery.surgery.total_minutes_for_surgery",
                args: {
                    doc: JSON.stringify(frm.doc)
                },
                callback: function (r) {
                    if (r.message) {

                        frm.set_value("overal_robotic_surgery_time_minutes", r.message);
                    }
                }
            });
        }

        
});

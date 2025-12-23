// frappe.ui.form.on("Employee", {
//     before_save(frm) {
//         if (frm.doc.custom_generate_user == 1 && !frm.doc.custom_user_created) {

//             return frappe.call({
//                 method: "merai_newage.overrides.employee.create_user_with_roles",
//                 args: {
//                     doc: JSON.stringify(frm.doc)
//                 },
//                 callback: function (r) {
//                     if (r.message) {
//                         frappe.msgprint("User Created: " + r.message);
//                         frm.set_value("custom_user_created", 1);
//                     }
//                 }
//             });
//         }
//     }
// });

frappe.ui.form.on("Employee", {

    before_save(frm) {

        if (frm.doc.custom_generate_user == 1 && !frm._user_created) {

            frappe.call({
                method: "merai_newage.overrides.employee.create_user_with_roles",
                args: { doc: JSON.stringify(frm.doc) },
                async: false,  // important: run synchronously, no popup
                callback: function (r) {
                    if (r.message) {
                        frm._generated_user_email = r.message;
                        frm._user_created = true;
                    }
                }
            });
        }
    },

    after_save(frm) {

        if (frm._generated_user_email) {

            frappe.db.set_value(
                "Employee",
                frm.doc.name,
                "user_id",
                frm._generated_user_email
            ).then(() => {

                frm._generated_user_email = null;
                frm._user_created = null;

                frm.reload_doc(); // reload silently
            });
        }
    }
});

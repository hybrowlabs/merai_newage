// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt


// frappe.ui.form.on("Robot Movement", {
//     refresh(frm) {
        
//         frm.set_query("item_code", () => {
//             return {
//                 query: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_item_code",
//             };
//         });

//         frm.set_query("robot_name", () => {
//             return {
//                 query: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_robot_names",
//             };
//         });

//     },

//     robot_name: function(frm) {
//         if (!frm.doc.robot_name) return;

//         frappe.call({
//             method: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_robot_tracker_data",
//             args: {
//                 doc: JSON.stringify(frm.doc)
//             },
//             callback: function(r) {
//                 if (r.message) {
//                     frm.set_value("item_code", r.message.item_code);
//                     frm.set_value("batch", r.message.batch);
//                     frm.set_value("robot_status", r.message.robot_status);
//                     frm.set_value("from_location", r.message.from_location);
//                     frm.set_value("work_order", r.message.work_order);
//                 }
//             }
//         });
//     }
// });



// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt
frappe.ui.form.on("Robot Movement", {
    refresh(frm) {
        
        frm.set_query("item_code", () => {
            return {
                query: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_item_code",
            };
        });

        frm.set_query("robot_name", () => {
            return {
                query: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_robot_names",
                filters: {
                    "robot_classification": frm.doc.robot_classification
                }
            };
        });

    },

    // Add this trigger to refresh the query when robot_classification changes
    robot_classification: function(frm) {
        frm.set_value("robot_name", "");
        frm.set_query("robot_name", () => {
            return {
                query: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_robot_names",
                filters: {
                    "robot_classification": frm.doc.robot_classification
                }
            };
        });
    },

    robot_name: function(frm) {
        if (!frm.doc.robot_name) return;

        frappe.call({
            method: "merai_newage.merai_newage.doctype.robot_movement.robot_movement.get_robot_tracker_data",
            args: {
                doc: JSON.stringify(frm.doc)
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("item_code", r.message.item_code);
                    frm.set_value("batch", r.message.batch);
                    frm.set_value("robot_status", r.message.robot_status);
                    frm.set_value("from_location", r.message.from_location);
                    frm.set_value("work_order", r.message.work_order);
                }
            }
        });
    }
});
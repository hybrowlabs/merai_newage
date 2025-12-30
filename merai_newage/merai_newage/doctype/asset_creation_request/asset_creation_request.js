frappe.ui.form.on("Asset Creation Request", {


    qty(frm) {
        let qty = cint(frm.doc.qty || 0);

        frm.clear_table("asset_code_details");

        if (qty <= 0) {
            frm.refresh_field("asset_code_details");
            return;
        }

        for (let i = 0; i < qty; i++) {
            frm.add_child("asset_code_details", {
                serial_no: ""   
            });
        }

        frm.refresh_field("asset_code_details");
    },
    generate_asset_codes(frm) {
        frappe.call({
            method: "merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_serial_nos",
            args: {
                doc: frm.doc
            },
            freeze: true,
            callback: function (r) {
                if (!r.message) return;

                // clear child table safely
                frm.clear_table("asset_code_details");

                r.message.forEach(row => {
                    let child = frm.add_child("asset_code_details");
                    child.serial_no = row.serial_no;
                });

                // refresh the child table field
                frm.refresh_field("asset_code_details");

                frappe.show_alert({
                    message: __("Serial Numbers generated successfully"),
                    indicator: "green"
                });
            }
        });
    },
    
    refresh(frm){
        if (!frm.doc.employee) {
            let user = frappe.session.user;
            console.log("user=====",user)
            frappe.db.get_list("Employee", {
                fields: ["name"],
                filters: {
                    user_id: user
                },
                limit: 1
            }).then(res => {
                if (res.length > 0) {
                    frm.set_value("employee", res[0].name);
                }
            });
        }
        frm.set_query("item", () => {
            return {
                filters: {
                    is_fixed_asset: 1,
                    is_stock_item:0
                }
            };
        });
    }
});
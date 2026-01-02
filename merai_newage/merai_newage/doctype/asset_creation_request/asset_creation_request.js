frappe.ui.form.on("Asset Creation Request", {


    // qty(frm) {
    //     let qty = cint(frm.doc.qty || 0);

    //     frm.clear_table("asset_code_details");

    //     if (qty <= 0) {
    //         frm.refresh_field("asset_code_details");
    //         return;
    //     }

    //     for (let i = 0; i < qty; i++) {
    //         frm.add_child("asset_code_details", {
    //             serial_no: ""   
    //         });
    //     }

    //     frm.refresh_field("asset_code_details");
    // },
    qty(frm) {
    update_asset_code_rows(frm);
},

composite_item(frm) {
    update_asset_code_rows(frm);
},
//     generate_asset_codes(frm) {
//     frappe.call({
//         method: "merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_assets_from_request",
//         args: {
//             doc: frm.doc
//         },
//         freeze: true,
//         callback: function (r) {
//             if (!r.message || !r.message.length) return;

//             frm.clear_table("asset_code_details");

//             r.message.forEach(row => {
//                 let child = frm.add_child("asset_code_details");
//                 child.asset_code = row.asset_code;
//             });

//             frm.refresh_field("asset_code_details");

//             frappe.show_alert({
//                 message: __("Asset Codes generated successfully"),
//                 indicator: "green"
//             });
//         }
//     });
// }


generate_asset_codes(frm) {
    if (frm.is_dirty()) {
        frm.save().then(() => {
            frm.trigger("generate_asset_codes");
        });
        return;
    }

    frappe.call({
        method: "merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_assets_from_request",
        args: {
            doc: frm.doc
        },
        freeze: true,
        callback: function (r) {
            if (!r.message || !r.message.length) return;

            frm.clear_table("asset_code_details");

            r.message.forEach(row => {
                let child = frm.add_child("asset_code_details");
                child.asset_code = row.asset_code;
            });

            frm.refresh_field("asset_code_details");
        }
    });
}

,
    
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


function update_asset_code_rows(frm) {
    let qty = cint(frm.doc.qty || 0);
    let is_composite = frm.doc.composite_item;

    frm.clear_table("asset_code_details");

    if (qty <= 0) {
        frm.refresh_field("asset_code_details");
        return;
    }

    let row_count = is_composite ? 1 : qty;

    for (let i = 0; i < row_count; i++) {
        frm.add_child("asset_code_details", {
            asset_code: ""
        });
    }

    frm.refresh_field("asset_code_details");
}

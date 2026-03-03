// frappe.ready(function () {
//     const urlParams = new URLSearchParams(window.location.search);
//     const poNumber = urlParams.get('po_number');
//     const vendorId = urlParams.get('vendor_id');
//     const vendorName = urlParams.get('vendor_name');

//     if (poNumber) {
//         frappe.call({
//             method: 'merai_newage.overrides.purchase_order.get_po_items',
//             args: { po_number: poNumber },
//             callback: function (r) {
//                 console.log("API response:", r);

//                 frappe.web_form.set_value('po_number', poNumber);
//                 if (vendorId) frappe.web_form.set_value('vendor_id', vendorId);
//                 if (vendorName) frappe.web_form.set_value('vendor_name', vendorName);

//                 if (r && r.message && r.message.length > 0) {
//                     // ✅ Assign with proper name fields Frappe expects
//                     frappe.web_form.doc.po_items = r.message.map(function (item, index) {
//                         return {
//                             doctype: 'PO Items',
//                             name: 'new-po-items-' + index,  // ✅ unique name is required
//                             __islocal: 1,
//                             __unsaved: 1,
//                             item: item.item_code,
//                             purchase_order: poNumber,
//                             item_description: item.description || item.item_name,
//                             required_qty: item.qty,
//                             dispatch_qty: 0,
//                             uom: item.uom,
//                             rate: item.rate,
//                             amount: item.amount,
//                             idx: index + 1
//                         };
//                     });

//                     // ✅ Refresh only the table field
//                     frappe.web_form.fields_dict['po_items'].refresh();
//                 }
//             }
//         });
//     }
// });



frappe.ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const poNumber = urlParams.get('po_number');
    const vendorId = urlParams.get('vendor_id');
    const vendorName = urlParams.get('vendor_name');

    if (poNumber) {
        frappe.call({
            method: 'merai_newage.overrides.purchase_order.get_po_items',
            args: { po_number: poNumber },
            callback: function (r) {
                console.log("API response:", r);

                frappe.web_form.set_value('po_number', poNumber);
                if (vendorId) frappe.web_form.set_value('vendor_id', vendorId);
                if (vendorName) frappe.web_form.set_value('vendor_name', vendorName);

                if (r && r.message && r.message.length > 0) {
                    frappe.web_form.doc.po_items = r.message.map(function (item, index) {
                        return {
                            doctype: 'PO Items',
                            name: 'new-po-items-' + index,
                            __islocal: 1,
                            __unsaved: 1,
                            item: item.item_code,
                            purchase_order: poNumber,
                            item_description: item.description || item.item_name,
                            required_qty: item.qty,
                            dispatch_qty: 0,
                            uom: item.uom,
                            rate: item.rate,
                            amount: item.amount,
                            idx: index + 1
                        };
                    });

                    frappe.web_form.fields_dict['po_items'].refresh();
                }
            }
        });
    }

    // ✅ Client-side validation before form submission
    frappe.web_form.on('po_items', function (frm, cdt, cdn) {
        validate_dispatch_qty();
    });

    frappe.web_form.validate = function () {
        return validate_dispatch_qty();
    };

    function validate_dispatch_qty() {
        const items = frappe.web_form.doc.po_items || [];
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const dispatchQty = parseFloat(item.dispatch_qty) || 0;
            const requiredQty = parseFloat(item.required_qty) || 0;

            if (dispatchQty < 0) {
                frappe.msgprint({
                    title: 'Validation Error',
                    message: `Row ${i + 1}: Dispatch Qty cannot be negative for item <b>${item.item}</b>`,
                    indicator: 'red'
                });
                return false; // ✅ blocks submission
            }

            if (dispatchQty > requiredQty) {
                frappe.msgprint({
                    title: 'Validation Error',
                    message: `Row ${i + 1}: Dispatch Qty (<b>${dispatchQty}</b>) cannot exceed Required Qty (<b>${requiredQty}</b>) for item <b>${item.item}</b>`,
                    indicator: 'red'
                });
                return false; // ✅ blocks submission
            }
        }
        return true; // ✅ allow submission
    }
});
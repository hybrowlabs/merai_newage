
frappe.ui.form.on("Asset Creation Request", {
    qty(frm) {
        update_asset_code_rows(frm);
    },
    
    composite_item(frm) {
        update_asset_code_rows(frm);
    },
    
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
    },
    
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            
            // 🆕 NEW: Create ERPNext Asset Button (only for composite items)
            if (frm.doc.target_asset_item_code) {
                frm.add_custom_button(__('Create Asset'), function () {
                    // Validation checks
                    if (!frm.doc.target_asset_item_code) {
                        frappe.msgprint({
                            title: __('Cannot Create Asset'),
                            indicator: 'red',
                            message: __('Please select an Item first.')
                        });
                        return;
                    }
                    
                    let target_item = frm.doc.target_asset_item_code;
                    let target_value = frm.doc.approx_cost || 0;
                    
                    frappe.confirm(
                        __('Create ERPNext Asset for Composite Item? <br><br>' +
                           '<b>Item:</b> {0}<br>' +
                           '<b>Approximate Cost:</b> ₹{1}<br>' +
                           '<b>Custodian:</b> {2}<br>' +
                           '<b>Location:</b> {3}<br>' +
                           '<b>Category:</b> {4}<br><br>' +
                           'This asset will be used as the target in Asset Capitalization.',
                           [target_item, format_currency(target_value), 
                            frm.doc.employee || 'Not Set', 
                            frm.doc.location || 'Not Set',
                            frm.doc.category_of_asset || 'Not Set']
                        ),
                        function() {
                            frappe.call({
                                method: 'merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_composite_erp_asset',
                                args: {
                                    acr_name: frm.doc.name
                                },
                                freeze: true,
                                freeze_message: __("Creating Asset..."),
                                callback: function(r) {
                                    if (r.message) {
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }, __('Create'));
            }
            
            // 🔹 Material Request Button
            frm.add_custom_button(__('Material Request'), function () {
                frappe.route_options = {
                    custom_asset_creation_request: frm.doc.name,
                    schedule_date: frappe.datetime.get_today(),
                    custom_purchase_types: "Asset",
                    company: frm.doc.entinty,
                    custom_requisitioner: frm.doc.employee
                };
                frappe.set_route('Form', 'Material Request', 'new-material-request');
            }, __('Create'));
          
            
            // 🆕 ENHANCED: Asset Capitalization Button with Asset Item Creation
            frm.add_custom_button(__('Asset Capitalization'), function () {
                // Check if target asset exists for composite items
                if (frm.doc.target_asset_item_code && !frm.doc.cwip_asset) {
                    frappe.msgprint({
                        title: __('Target Asset Required'),
                        indicator: 'orange',
                        message: __('Please create the target Asset first using the "Create Asset" button, then create Asset Capitalization.')
                    });
                    return;
                }
                
                // Show preview dialog
                let asset_items = frm.doc.custom_cwip_purchase_receipts.filter(r => {
                    return frappe.db.get_value("Item", r.item_code, "is_fixed_asset");
                });
                let stock_items = frm.doc.custom_cwip_purchase_receipts.filter(r => {
                    let item = frappe.db.get_value("Item", r.item_code, ["is_stock_item", "is_fixed_asset"]);
                    return item && item.is_stock_item && !item.is_fixed_asset;
                });
                let service_items = frm.doc.custom_cwip_purchase_receipts.filter(r => r.is_service_item);
                
                let total_prs = frm.doc.custom_cwip_purchase_receipts.length;
                
                frappe.confirm(
                    __('This will create Asset Capitalization with: <br><br>' +
                       '<b>Total PRs:</b> {0}<br>' +
                       '<b>Asset Items:</b> {1} (will create {1} Asset records)<br>' +
                       '<b>Stock Items:</b> {2}<br>' +
                       '<b>Service Items:</b> {3}<br><br>' +
                       'Continue?',
                       [total_prs, asset_items.length, stock_items.length, service_items.length]
                    ),
                    function() {
                        frappe.call({
                            method: "merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_asset_capitalization_from_acr",
                            args: {
                                acr_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating assets and capitalization..."),
                            callback: function (r) {
                                console.log("Asset Capitalization Creation Response:", r);
                                if (r.message) {
                                    // frm.reload_doc();
                                    // frappe.set_route("Form", "Asset Capitalization", r.message);
                                    window.location.href = `/app/asset-capitalization/${r.message}`;
                                }
                            }
                        });
                    }
                );
            }, __('Create'));
            
            // 🆕 NEW: View Created Assets Button
            if (frm.doc.custom_created_assets && frm.doc.custom_created_assets.length > 0) {
                frm.add_custom_button(__('View Created Assets'), function() {
                    show_created_assets_dialog(frm);
                }, __('CWIP Actions'));
            }
            
            // 🆕 NEW: View Target Asset Button (if composite and asset exists)
            if (frm.doc.target_asset_item_code && frm.doc.custom_cwip_asset) {
                frm.add_custom_button(__('View Target Asset'), function() {
                    frappe.set_route("Form", "Asset", frm.doc.custom_cwip_asset);
                }, __('CWIP Actions'));
            }
        }
        
        // Convert to Fixed Asset Button (existing)
        if (frm.doc.enable_cwip_accounting && 
            frm.doc.custom_cwip_purchase_receipts && 
            frm.doc.custom_cwip_purchase_receipts.length > 0 && 
            frm.doc.custom_cwip_asset) {
            
            frm.add_custom_button(__('Convert to Fixed Asset'), function() {
                let total_prs = frm.doc.custom_cwip_purchase_receipts.length;
                let total_amount = frm.doc.custom_total_cwip_amount || 0;
                let main_items = frm.doc.custom_cwip_purchase_receipts.filter(r => !r.is_service_item).length;
                let service_items = frm.doc.custom_cwip_purchase_receipts.filter(r => r.is_service_item).length;
                
                frappe.confirm(
                    __('Update CWIP Asset with accumulated costs? <br><br>' +
                       '<b>Total PRs:</b> {0}<br>' +
                       '<b>Main Asset Items:</b> {1}<br>' +
                       '<b>Service Items:</b> {2}<br>' +
                       '<b>Total Amount:</b> ₹{3}<br><br>' +
                       'This will update the asset amount.',
                       [total_prs, main_items, service_items, format_currency(total_amount)]
                    ),
                    function() {
                        frappe.call({
                            method: 'merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.convert_cwip_to_fixed_asset',
                            args: {
                                acr_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: __(r.message)
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }, __('CWIP Actions'));
            
            // Add button to view CWIP breakdown
            frm.add_custom_button(__('View Cost Breakdown'), function() {
                show_cwip_breakdown(frm);
            }, __('CWIP Actions'));
        }
        
        // Auto-set employee
        if (!frm.doc.employee) {
            let user = frappe.session.user;
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
        
        // Set queries
        frm.set_query("cost_centre", () => {
            return {
                filters: {
                    company: frm.doc.entinty,
                    is_group: 0
                }
            };
        });
        
        frm.set_query("item", () => {
            return {
                filters: {
                    is_fixed_asset: 1,
                    is_stock_item: 0
                }
            };
        });
    }
});

function update_asset_code_rows(frm) {
    let qty = cint(frm.doc.qty || 0);
    let is_composite = frm.doc.target_asset_item_code;
    
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

// 🆕 NEW FUNCTION: Show Created Assets Dialog
function show_created_assets_dialog(frm) {
    let assets = frm.doc.custom_created_assets || [];
    
    if (!assets.length) {
        frappe.msgprint(__("No assets created yet"));
        return;
    }
    
    let html = `
        <table class="table table-bordered" style="margin-top: 10px;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th>Asset</th>
                    <th>Item Code</th>
                    <th>Amount</th>
                    <th>Purchase Receipt</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let total = 0;
    assets.forEach(row => {
        total += flt(row.amount);
        html += `
            <tr>
                <td><b>${row.asset}</b></td>
                <td>${row.item_code}</td>
                <td>₹${format_number(row.amount)}</td>
                <td>${row.purchase_receipt}</td>
                <td><a href="/app/asset/${row.asset}" target="_blank">View</a></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
            <tfoot>
                <tr style="background-color: #f9f9f9; font-weight: bold;">
                    <td colspan="2">Total</td>
                    <td>₹${format_number(total)}</td>
                    <td colspan="2"></td>
                </tr>
            </tfoot>
        </table>
    `;
    
    frappe.msgprint({
        title: __("Created Assets from CWIP PRs"),
        message: html,
        indicator: "blue",
        wide: true
    });
}

// 🆕 ENHANCED: Show CWIP Breakdown (existing function - enhanced)
function show_cwip_breakdown(frm) {
    let prs = frm.doc.custom_cwip_purchase_receipts || [];
    
    if (!prs.length) {
        frappe.msgprint(__("No Purchase Receipts found"));
        return;
    }
    
    // Categorize items
    let asset_items = [];
    let stock_items = [];
    let service_items = [];
    
    prs.forEach(pr => {
        // This is approximate - in real scenario you'd check Item doctype
        if (pr.is_service_item) {
            service_items.push(pr);
        } else {
            // You might need to add a flag to distinguish asset vs stock
            stock_items.push(pr);
        }
    });
    
    let total_amount = prs.reduce((sum, pr) => sum + flt(pr.rate), 0);
    
    let html = `
        <div style="margin-bottom: 20px;">
            <h4>CWIP Cost Breakdown</h4>
            <table class="table table-bordered">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th>Category</th>
                        <th>Items</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Service Items</td>
                        <td>${service_items.length}</td>
                        <td>₹${format_number(service_items.reduce((s, i) => s + flt(i.rate), 0))}</td>
                    </tr>
                    <tr>
                        <td>Stock/Asset Items</td>
                        <td>${stock_items.length}</td>
                        <td>₹${format_number(stock_items.reduce((s, i) => s + flt(i.rate), 0))}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9; font-weight: bold;">
                        <td>TOTAL</td>
                        <td>${prs.length}</td>
                        <td>₹${format_number(total_amount)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <h4>Detailed List</h4>
        <table class="table table-bordered table-hover">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th>PR</th>
                    <th>Date</th>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Rate</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    prs.forEach(pr => {
        let type = pr.is_service_item ? 'Service' : 'Stock/Asset';
        html += `
            <tr>
                <td><b>${pr.purchase_receipt}</b></td>
                <td>${pr.pr_date || ''}</td>
                <td>${pr.item_code}<br><small>${pr.item_name || ''}</small></td>
                <td>${pr.qty || 1}</td>
                <td>₹${format_number(pr.rate)}</td>
                <td><span class="label label-${pr.is_service_item ? 'info' : 'primary'}">${type}</span></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    frappe.msgprint({
        title: __("CWIP Cost Breakdown"),
        message: html,
        indicator: "blue",
        wide: true
    });
}
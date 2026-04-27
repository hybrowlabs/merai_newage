
// frappe.ready(function () {
//     const params = new URLSearchParams(window.location.search);
//     const rfq = params.get("rfq");
//     const supplier = params.get("supplier");

//     if (supplier) {
//         frappe.web_form.set_value("supplier", supplier);

//         frappe.call({
//             method: "frappe.client.get_value",
//             args: {
//                 doctype: "Supplier",
//                 filters: { name: supplier },
//                 fieldname: ["supplier_name"]
//             },
//             callback: function (r) {
//                 if (r.message) {
//                     frappe.web_form.set_value("supplier_name", r.message.supplier_name);
//                 }
//             }
//         });
//     }

//     if (rfq) {
//         frappe.call({
//             method: "frappe.client.get",
//             args: { doctype: "Request for Quotation", name: rfq },
//             callback: function (r) {
//                 if (r.message) {
//                     const doc = r.message;

//                     frappe.web_form.set_value("company", doc.company);
//                     frappe.web_form.set_value("plant", doc.custom_plant || "");
//                     frappe.web_form.set_value("cost_center", doc.cost_center || "");
//                     frappe.web_form.set_value("quotation_number", doc.name);
//                     frappe.web_form.set_value("custom_rfq_reference", rfq);
//                     frappe.web_form.set_value("custom_type", doc.custom_type);
//                     frappe.web_form.set_value("custom_quotation_deadline", doc.custom_quotation_deadline1);

//                     if (doc.custom_quotation_deadline1) {
//                         // ✅ Check immediately on load — if already expired, show page right away
//                         const deadline = new Date(doc.custom_quotation_deadline1);
//                         if (deadline - new Date() <= 0) {
//                             show_expired_page(doc.custom_quotation_deadline1, doc.name);
//                             return; // stop further execution
//                         }

//                         start_countdown_timer(doc.custom_quotation_deadline1, doc.name);
//                     }

//                     if (doc.items && doc.items.length > 0) {
//                         frappe.web_form.doc.items = doc.items.map(function (item, index) {
//                             return {
//                                 doctype: "Supplier Quotation Item",
//                                 name: "new-items-" + index,
//                                 __islocal: 1,
//                                 __unsaved: 1,
//                                 idx: index + 1,
//                                 item_code: item.item_code,
//                                 item_name: item.item_name || "",
//                                 description: item.description || "",
//                                 qty: item.qty,
//                                 uom: item.uom,
//                                 warehouse: item.warehouse || "",
//                                 rate: 0,
//                                 amount: 0,
//                                 request_for_quotation: rfq
//                             };
//                         });

//                         frappe.web_form.fields_dict['items'].refresh();

//                         frappe.web_form.fields_dict['items'].grid.wrapper
//                             .on('change', 'input[data-fieldname="rate"]', function () {
//                                 recalculate_amounts();
//                             });
//                     }
//                 }
//             }
//         });
//     }

//    function show_expired_page(deadline_str, rfq_name) {
//     // ✅ Hide everything in the page body except navbar
//     $('body').children().not('header, nav, .navbar, #navbar, .navbar-fixed-top').hide();
    
//     // Also hide the web form section specifically
//     $('.web-form-container, .form-page, [data-web-form], .container.with-padding, section').hide();

//     $('#quotation-expired-page').remove();

//     const expired_html = `
//         <div id="quotation-expired-page" style="
//             position: fixed;
//             top: 0;
//             left: 0;
//             width: 100%;
//             height: 100%;
//             background: #fff;
//             z-index: 99999;
//             display: flex;
//             flex-direction: column;
//             align-items: center;
//             justify-content: center;
//             text-align: center;
//             padding: 40px 20px;
//             font-family: inherit;
//             overflow-y: auto;
//         ">
//             <div style="
//                 width: 130px;
//                 height: 130px;
//                 background: #f8d7da;
//                 border-radius: 50%;
//                 display: flex;
//                 align-items: center;
//                 justify-content: center;
//                 margin-bottom: 30px;
//                 animation: pulse 2s infinite;
//             ">
//                 <span style="font-size: 65px;">⏰</span>
//             </div>

//             <h1 style="
//                 font-size: 38px;
//                 font-weight: 700;
//                 color: #721c24;
//                 margin: 0 0 14px 0;
//             ">Oops! Time's Up</h1>

//             <p style="
//                 font-size: 18px;
//                 color: #555;
//                 margin: 0 0 8px 0;
//                 max-width: 500px;
//             ">The deadline for this quotation has passed.</p>

//             <p style="
//                 font-size: 15px;
//                 color: #888;
//                 margin: 0 0 28px 0;
//             ">You can no longer submit a quotation for 
//                 <strong>${rfq_name || 'this RFQ'}</strong>.
//             </p>

//             <div style="
//                 background: #fff3cd;
//                 border: 1px solid #ffc107;
//                 border-radius: 8px;
//                 padding: 14px 32px;
//                 margin-bottom: 32px;
//                 font-size: 15px;
//                 color: #856404;
//             ">
//                 ⏳ Deadline was: <strong>${deadline_str}</strong>
//             </div>

//             <div style="
//                 background: #f8f9fa;
//                 border: 1px solid #dee2e6;
//                 border-radius: 8px;
//                 padding: 16px 32px;
//                 max-width: 420px;
//             ">
//                 <p style="
//                     font-size: 14px;
//                     color: #666;
//                     margin: 0;
//                     line-height: 1.7;
//                 ">
//                     📩 If you believe this is an error or need an extension,<br/>
//                     please contact the <strong>procurement team</strong>.
//                 </p>
//             </div>

//             <style>
//                 @keyframes pulse {
//                     0%   { transform: scale(1);    box-shadow: 0 0 0 0 rgba(220,53,69,0.4); }
//                     70%  { transform: scale(1.05); box-shadow: 0 0 0 16px rgba(220,53,69,0); }
//                     100% { transform: scale(1);    box-shadow: 0 0 0 0 rgba(220,53,69,0); }
//                 }
//             </style>
//         </div>
//     `;

//     // ✅ Append to body - position:fixed covers everything
//     $('body').append(expired_html);
//     window.scrollTo(0, 0);
// }
//     // ✅ Countdown Timer Function
//     function start_countdown_timer(deadline_str, rfq_name) {
//         $('#quotation-timer-banner').remove();

//         const timer_html = `
//             <div id="quotation-timer-banner" style="
//                 position: sticky;
//                 top: 0;
//                 z-index: 1000;
//                 background: #fff3cd;
//                 border: 1px solid #ffc107;
//                 border-radius: 6px;
//                 padding: 12px 20px;
//                 margin-bottom: 16px;
//                 display: flex;
//                 align-items: center;
//                 gap: 12px;
//                 font-size: 15px;
//                 font-weight: 500;
//                 color: #856404;
//                 box-shadow: 0 2px 6px rgba(0,0,0,0.08);
//             ">
//                 <span style="font-size:20px;">⏳</span>
//                 <span>Quotation Deadline:</span>
//                 <span id="quotation-timer-display" style="
//                     font-size: 17px;
//                     font-weight: 700;
//                     letter-spacing: 1px;
//                     color: #856404;
//                 ">Calculating...</span>
//                 <span style="margin-left:auto; font-size:13px; color:#aaa;">
//                     Deadline: ${deadline_str}
//                 </span>
//             </div>
//         `;

//         $('.web-form-container, .form-page, [data-web-form]').first().prepend(timer_html);

//         if (!$('#quotation-timer-banner').length) {
//             $('main, .container').first().prepend(timer_html);
//         }

//         const deadline      = new Date(deadline_str);
//         const timer_display = $('#quotation-timer-display');
//         const banner        = $('#quotation-timer-banner');

//         function update_timer() {
//             const now  = new Date();
//             const diff = deadline - now;

//             if (diff <= 0) {
//                 clearInterval(timer_interval);
//                 // ✅ Show expired full page when timer hits zero
//                 show_expired_page(deadline_str, rfq_name);
//                 return;
//             }

//             const days    = Math.floor(diff / (1000 * 60 * 60 * 24));
//             const hours   = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
//             const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
//             const seconds = Math.floor((diff % (1000 * 60)) / 1000);

//             let display = days > 0
//                 ? `${days}d ${hours}h ${minutes}m ${seconds}s left`
//                 : hours > 0
//                     ? `${hours}h ${minutes}m ${seconds}s left`
//                     : `${minutes}m ${seconds}s left`;

//             timer_display.text(display);

//             if (diff < 30 * 60 * 1000) {
//                 banner.css({ background: "#f8d7da", border: "1px solid #f5c6cb", color: "#721c24" });
//                 timer_display.css("color", "#721c24");
//             } else if (diff < 60 * 60 * 1000) {
//                 banner.css({ background: "#ffe5d0", border: "1px solid #fd7e14", color: "#7d3c07" });
//                 timer_display.css("color", "#c0390e");
//             }
//         }

//         update_timer();
//         const timer_interval = setInterval(update_timer, 1000);
//     }

//     // ✅ Recalculate amounts
//     $(document).on('change', '.grid-body input', function () {
//         recalculate_amounts();
//     });

//     function recalculate_amounts() {
//         const items = frappe.web_form.doc.items || [];
//         let updated = false;

//         items.forEach(function (item) {
//             const rate      = parseFloat(item.rate) || 0;
//             const qty       = parseFloat(item.qty)  || 0;
//             const newAmount = rate * qty;

//             if (item.amount !== newAmount) {
//                 item.amount = newAmount;
//                 updated = true;
//             }
//         });

//         if (updated) {
//             frappe.web_form.fields_dict['items'].refresh();
//         }
//     }

//     // ✅ Validate before submit
//     frappe.web_form.validate = function () {
//         if ($('#quotation-expired-page').length) {
//             frappe.msgprint({
//                 title: "Deadline Passed",
//                 message: "The quotation deadline has passed. You can no longer submit.",
//                 indicator: "red"
//             });
//             return false;
//         }

//         const items = frappe.web_form.doc.items || [];
//         for (let i = 0; i < items.length; i++) {
//             const item  = items[i];
//             const rate  = parseFloat(item.rate) || 0;
//             const qty   = parseFloat(item.qty)  || 0;

//             if (rate <= 0) {
//                 frappe.msgprint({
//                     title: "Validation Error",
//                     message: `Row ${i + 1}: Please enter Rate for item <b>${item.item_code}</b>`,
//                     indicator: "red"
//                 });
//                 return false;
//             }
//             item.amount = rate * qty;
//         }
//         return true;
//     };
// });




frappe.ready(function () {
    const params = new URLSearchParams(window.location.search);
    const rfq = params.get("rfq");
    const supplier = params.get("supplier");

    if (!rfq || !supplier) return;

    // ─────────────────────────────────────────
    // STEP 1: Check auction eligibility FIRST
    // ─────────────────────────────────────────
    frappe.call({
        method: "merai_newage.overrides.rfq.check_auction_eligibility",
        args: { rfq: rfq, supplier: supplier },
        callback: function (r) {
            if (!r.message) return;

            const result = r.message;

            // ❌ Not eligible — show blocked page
            if (!result.eligible) {
                if (result.is_last_hour && !result.has_existing_bid) {
                    show_last_hour_blocked_page(rfq);
                } else {
                    show_expired_page("", rfq);
                }
                return;
            }

            // ✅ Eligible — load form normally
            load_form(result);
        }
    });

// ─────────────────────────────────────────
// Fill items table — FIXED
// ─────────────────────────────────────────
function fill_items(rfq_items, existing_rates, rfq_name) {
    if (!rfq_items || !rfq_items.length) return;

    const rate_map = {};
    (existing_rates || []).forEach(function (i) {
        rate_map[i.item_code] = i.rate;
    });

    frappe.web_form.doc.items = rfq_items.map(function (item, index) {
        return {
            doctype: "Supplier Quotation Item",
            name: "new-items-" + index,
            __islocal: 1,
            __unsaved: 1,
            idx: index + 1,
            item_code: item.item_code,
            item_name: item.item_name || "",
            description: item.description || "",
            qty: item.qty,
            uom: item.uom,
            warehouse: item.warehouse || "",
            rate: item.custom_rate || rate_map[item.item_code] || 1,
            amount: (rate_map[item.item_code] || 1) * item.qty,
            request_for_quotation: rfq_name
        };
    });

    // ✅ Use setTimeout to ensure grid is rendered before refresh
    setTimeout(function () {
        frappe.web_form.fields_dict['items'].refresh();

        frappe.web_form.fields_dict['items'].grid.wrapper
            .off('change')  // remove duplicate listeners
            .on('change', 'input[data-fieldname="rate"]', function () {
                recalculate_amounts();
            });
    }, 300);
}


// ─────────────────────────────────────────
// load_form — FIXED existing bidder block
// ─────────────────────────────────────────
function load_form(auction_status) {
    frappe.web_form.set_value("supplier", supplier);

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Supplier",
            filters: { name: supplier },
            fieldname: ["supplier_name"]
        },
        callback: function (r) {
            if (r.message) {
                frappe.web_form.set_value("supplier_name", r.message.supplier_name);
            }
        }
    });

    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Request for Quotation", name: rfq },
        callback: function (r) {
            if (!r.message) return;

            const doc = r.message;

            frappe.web_form.set_value("company", doc.company);
            frappe.web_form.set_value("plant", doc.custom_plant || "");
            frappe.web_form.set_value("cost_center", doc.cost_center || "");
            frappe.web_form.set_value("quotation_number", doc.name);
            frappe.web_form.set_value("custom_rfq_reference", rfq);
            frappe.web_form.set_value("custom_type", doc.custom_type);
            frappe.web_form.set_value("custom_quotation_deadline", doc.custom_quotation_deadline1);

            if (doc.custom_quotation_deadline1) {
                const deadline = new Date(doc.custom_quotation_deadline1);
                if (deadline - new Date() <= 0) {
                    show_expired_page(doc.custom_quotation_deadline1, doc.name);
                    return;
                }
                start_countdown_timer(
                    doc.custom_quotation_deadline1,
                    doc.name,
                    auction_status.is_last_hour,
                    auction_status.has_existing_bid
                );
            }

            // ✅ FIXED: Always fetch RFQ items first
            // Then overlay existing bid rates if available
            if (auction_status.has_existing_bid) {
                frappe.call({
                    method: "merai_newage.overrides.rfq.get_existing_bid",
                    args: { rfq: rfq, supplier: supplier },
                    callback: function (res) {
                        const bid = res.message || {};
                        const bid_items = (res.message && res.message.items) || [];

                        // ✅ Always use RFQ items as base, overlay rates from existing bid
                        fill_items(doc.items, bid_items, rfq);
                        show_revision_banner(res.message && res.message.name);

                        setTimeout(function () {
                if (bid.custom_shipment_mode)
                    frappe.web_form.set_value("custom_shipment_mode", bid.custom_shipment_mode);
                if (bid.custom_airline_name)
                    frappe.web_form.set_value("custom_airline_name", bid.custom_airline_name);
                if (bid.custom_cw)
                    frappe.web_form.set_value("custom_cw", bid.custom_cw);
                if (bid.custom_rate_kg)
                    frappe.web_form.set_value("custom_rate_kg", bid.custom_rate_kg);
                if (bid.custom_fsc)
                    frappe.web_form.set_value("custom_fsc", bid.custom_fsc);
                if (bid.custom_sc)
                    frappe.web_form.set_value("custom_sc", bid.custom_sc);
                if (bid.custom_xray)
                    frappe.web_form.set_value("custom_xray", bid.custom_xray);
                if (bid.custom_pick_uporigin)
                    frappe.web_form.set_value("custom_pick_uporigin", bid.custom_pick_uporigin);
                if(bid.custom_ex_words)
                    frappe.web_form.set_value("custom_ex_words",bid.custom_ex_words)
                if (bid.custom_total_freight)
                    frappe.web_form.set_value("custom_total_freight", bid.custom_total_freight);
                if(bid.custom_dc_inr)
                    frappe.web_form.set_value("custom_dc_inr",bid.custom_dc_inr)
                if(bid.custom_shipping_line_charges)
                    frappe.web_form.set_value("custom_shipping_line_charges",bid.custom_shipping_line_charges)
                if(bid.custom_cfs_charges)
                    frappe.web_form.set_value("custom_cfs_charges",bid.custom_cfs_charges)
                if (bid.custom_from_currency)
                    frappe.web_form.set_value("custom_from_currency", bid.custom_from_currency);
                if (bid.custom_to_currency)
                    frappe.web_form.set_value("custom_to_currency", bid.custom_to_currency);
                if (bid.custom_xrxe_com)
                    frappe.web_form.set_value("custom_xrxe_com", bid.custom_xrxe_com);
                if (bid.custom_total_freight_inr)
                    frappe.web_form.set_value("custom_total_freight_inr", bid.custom_total_freight_inr);
                if (bid.custom_total_landing_pricecinr)
                    frappe.web_form.set_value("custom_total_landing_pricecinr", bid.custom_total_landing_pricecinr);
                if(bid.custom_transit_day)
                    frappe.web_form.set_value("custom_transit_day",bid.custom_transit_day)
                if(bid.custom_pickup_location)
                    frappe.web_form.set_value("custom_pickup_location",bid.custom_pickup_location)
            }, 400);
                    }
                });
            } else {
                // ✅ New bidder — just fill from RFQ items with rate=0
                fill_items(doc.items, [], rfq);
            }
        }
    });
}

    // ─────────────────────────────────────────
    // Revision banner for existing bidders
    // ─────────────────────────────────────────
    function show_revision_banner(sq_name) {
        $('#revision-banner').remove();
        const html = `
            <div id="revision-banner" style="
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                border-radius: 6px;
                padding: 12px 20px;
                margin-bottom: 16px;
                font-size: 14px;
                color: #0c5460;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="font-size:18px;">🔄</span>
                <span>You are <strong>revising</strong> your existing quotation
                ${sq_name ? '<strong>(' + sq_name + ')</strong>' : ''}.
                Your previous rates have been prefilled.</span>
            </div>`;

        $('.web-form-container, .form-page, [data-web-form]').first().prepend(html);
    }


    // ─────────────────────────────────────────
    // Last hour blocked page (new bidders only)
    // ─────────────────────────────────────────
    function show_last_hour_blocked_page(rfq_name) {
        $('body').children().not('header, nav, .navbar, #navbar').hide();
        $('#last-hour-blocked-page').remove();

        $('body').append(`
            <div id="last-hour-blocked-page" style="
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: #fff;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px 20px;
                font-family: inherit;
            ">
                <div style="
                    width: 130px; height: 130px;
                    background: #fff3cd;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 30px;
                    animation: pulse-yellow 2s infinite;
                ">
                    <span style="font-size:65px;">🔒</span>
                </div>

                <h1 style="font-size:34px;font-weight:700;color:#856404;margin:0 0 14px;">
                    Auction Closing Soon
                </h1>

                <p style="font-size:17px;color:#555;max-width:500px;margin:0 0 10px;">
                    The auction for <strong>${rfq_name || 'this RFQ'}</strong> 
                    is in its <strong>final 1 hour</strong>.
                </p>

                <p style="font-size:15px;color:#888;max-width:480px;margin:0 0 28px;">
                    New quotations are <strong>not accepted</strong> during the last hour.<br/>
                    Only existing bidders can revise their bids.
                </p>

                <div style="
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 8px;
                    padding: 14px 32px;
                    margin-bottom: 28px;
                    font-size: 15px;
                    color: #856404;
                ">
                    ⏰ Bidding window for new participants has closed.
                </div>

                <div style="
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 16px 32px;
                    max-width: 420px;
                ">
                    <p style="font-size:14px;color:#666;margin:0;line-height:1.7;">
                        📩 If you have already submitted a bid, 
                        please use your original quotation link.<br/>
                        For assistance, contact the 
                        <strong>procurement team</strong>.
                    </p>
                </div>

                <style>
                    @keyframes pulse-yellow {
                        0%   { box-shadow: 0 0 0 0 rgba(255,193,7,0.5); }
                        70%  { box-shadow: 0 0 0 16px rgba(255,193,7,0); }
                        100% { box-shadow: 0 0 0 0 rgba(255,193,7,0); }
                    }
                </style>
            </div>
        `);
        window.scrollTo(0, 0);
    }


    // ─────────────────────────────────────────
    // Expired page
    // ─────────────────────────────────────────
    function show_expired_page(deadline_str, rfq_name) {
        $('body').children().not('header, nav, .navbar, #navbar').hide();
        $('#quotation-expired-page').remove();

        $('body').append(`
            <div id="quotation-expired-page" style="
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: #fff;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px 20px;
                font-family: inherit;
            ">
                <div style="
                    width: 130px; height: 130px;
                    background: #f8d7da;
                    border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    margin-bottom: 30px;
                    animation: pulse 2s infinite;
                ">
                    <span style="font-size:65px;">⏰</span>
                </div>

                <h1 style="font-size:38px;font-weight:700;color:#721c24;margin:0 0 14px;">
                    Oops! Time's Up
                </h1>
                <p style="font-size:18px;color:#555;max-width:500px;margin:0 0 8px;">
                    The deadline for this quotation has passed.
                </p>
                <p style="font-size:15px;color:#888;margin:0 0 28px;">
                    You can no longer submit a quotation for 
                    <strong>${rfq_name || 'this RFQ'}</strong>.
                </p>
                ${deadline_str ? `
                <div style="
                    background:#fff3cd;border:1px solid #ffc107;
                    border-radius:8px;padding:14px 32px;
                    margin-bottom:32px;font-size:15px;color:#856404;
                ">
                    ⏳ Deadline was: <strong>${deadline_str}</strong>
                </div>` : ''}
                <div style="
                    background:#f8f9fa;border:1px solid #dee2e6;
                    border-radius:8px;padding:16px 32px;max-width:420px;
                ">
                    <p style="font-size:14px;color:#666;margin:0;line-height:1.7;">
                        📩 If you believe this is an error or need an extension,<br/>
                        please contact the <strong>procurement team</strong>.
                    </p>
                </div>
                <style>
                    @keyframes pulse {
                        0%   { transform:scale(1);    box-shadow:0 0 0 0 rgba(220,53,69,0.4); }
                        70%  { transform:scale(1.05); box-shadow:0 0 0 16px rgba(220,53,69,0); }
                        100% { transform:scale(1);    box-shadow:0 0 0 0 rgba(220,53,69,0); }
                    }
                </style>
            </div>
        `);
        window.scrollTo(0, 0);
    }


    // ─────────────────────────────────────────
    // Countdown Timer
    // ─────────────────────────────────────────
    function start_countdown_timer(deadline_str, rfq_name, is_last_hour, has_existing_bid) {
        $('#quotation-timer-banner').remove();

        // Last hour warning for existing bidders
        const last_hour_warning = is_last_hour && has_existing_bid ? `
            <span style="
                margin-left: 16px;
                background: #721c24;
                color: white;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 13px;
            ">⚠️ Final Hour — Revision Only</span>` : '';

        const timer_html = `
            <div id="quotation-timer-banner" style="
                position: sticky;
                top: 0; z-index: 1000;
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 6px;
                padding: 12px 20px;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 15px;
                font-weight: 500;
                color: #856404;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            ">
                <span style="font-size:20px;">⏳</span>
                <span>Auction Closes In:</span>
                <span id="quotation-timer-display" style="
                    font-size:17px;font-weight:700;
                    letter-spacing:1px;color:#856404;
                ">Calculating...</span>
                ${last_hour_warning}
                <span style="margin-left:auto;font-size:13px;color:#aaa;">
                    Deadline: ${deadline_str}
                </span>
            </div>`;

        $('.web-form-container, .form-page, [data-web-form]').first().prepend(timer_html);
        if (!$('#quotation-timer-banner').length) {
            $('main, .container').first().prepend(timer_html);
        }

        const deadline      = new Date(deadline_str);
        const timer_display = $('#quotation-timer-display');
        const banner        = $('#quotation-timer-banner');

        function update_timer() {
            const diff = deadline - new Date();

            if (diff <= 0) {
                clearInterval(timer_interval);
                show_expired_page(deadline_str, rfq_name);
                return;
            }

            const days    = Math.floor(diff / 86400000);
            const hours   = Math.floor((diff % 86400000) / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);

            const display = days > 0
                ? `${days}d ${hours}h ${minutes}m ${seconds}s`
                : hours > 0
                    ? `${hours}h ${minutes}m ${seconds}s`
                    : `${minutes}m ${seconds}s`;

            timer_display.text(display);

            // Last hour — show red + warning for existing bidders
            if (diff < 3600000) {
                banner.css({ background: "#f8d7da", border: "1px solid #f5c6cb", color: "#721c24" });
                timer_display.css("color", "#721c24");

                // If new bidder enters last hour mid-session, block them
                if (!has_existing_bid) {
                    clearInterval(timer_interval);
                    show_last_hour_blocked_page(rfq_name);
                }
            } else if (diff < 3 * 3600000) {
                banner.css({ background: "#ffe5d0", border: "1px solid #fd7e14", color: "#7d3c07" });
                timer_display.css("color", "#c0390e");
            }
        }

        update_timer();
        const timer_interval = setInterval(update_timer, 1000);
    }


    // ─────────────────────────────────────────
    // Recalculate amounts
    // ─────────────────────────────────────────
    $(document).on('change', '.grid-body input', function () {
        recalculate_amounts();
    });

    function recalculate_amounts() {
        const items = frappe.web_form.doc.items || [];
        let updated = false;
        items.forEach(function (item) {
            const rate = parseFloat(item.rate) || 0;
            const qty  = parseFloat(item.qty)  || 0;
            const newAmount = rate * qty;
            if (item.amount !== newAmount) {
                item.amount = newAmount;
                updated = true;
            }
        });
        if (updated) frappe.web_form.fields_dict['items'].refresh();
    }


    // ─────────────────────────────────────────
    // Validate before submit
    // ─────────────────────────────────────────
    frappe.web_form.validate = function () {
        if ($('#quotation-expired-page').length || $('#last-hour-blocked-page').length) {
            frappe.msgprint({
                title: "Submission Blocked",
                message: "You are not allowed to submit at this time.",
                indicator: "red"
            });
            return false;
        }

        const items = frappe.web_form.doc.items || [];
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const rate = parseFloat(item.rate) || 0;
            const qty  = parseFloat(item.qty)  || 0;
            if (rate <= 0) {
                frappe.msgprint({
                    title: "Validation Error",
                    message: `Row ${i + 1}: Please enter Rate for item <b>${item.item_code}</b>`,
                    indicator: "red"
                });
                return false;
            }
            item.amount = rate * qty;
        }
        return true;
    };
});


// ─────────────────────────────────────────
// Exchange Rate — attach after form loads
// ─────────────────────────────────────────
frappe.web_form.after_load = function () {
    attach_currency_listeners();
    attach_landing_price_listeners();
    attach_freight_listeners();   
};

// Also attach after a short delay as fallback
setTimeout(function () {
    attach_currency_listeners();
    attach_freight_listeners();
}, 1000);

function attach_currency_listeners() {
    // Remove duplicate listeners first
    $(document)
        .off('change', '[data-fieldname="custom_from_currency"]')
        .off('change', '[data-fieldname="custom_to_currency"]');

    $(document).on('change', '[data-fieldname="custom_from_currency"]', function () {
        fetch_exchange_rate_webform();
    });

    $(document).on('change', '[data-fieldname="custom_to_currency"]', function () {
        fetch_exchange_rate_webform();
    });
}

function fetch_exchange_rate_webform() {
    const from_currency = frappe.web_form.get_value("custom_from_currency");
    const to_currency   = frappe.web_form.get_value("custom_to_currency");

    if (!from_currency || !to_currency) return;

    frappe.call({
        method: "merai_newage.merai_newage.api.get_exchange_rate",
        args: {
            from_currency: from_currency,
            to_currency: to_currency
        },
        callback: function (r) {
            if (r && r.message !== undefined) {
                frappe.web_form.set_value("custom_xrxe_com", r.message);

                // Small delay to ensure xr value is set before calculating
                setTimeout(function () {
                    calculate_freight_inr_webform();
                }, 200);
            }
        }
    });
}

// Calculate freight in INR whenever total freight or exchange rate changes
function calculate_freight_inr_webform() {
    const total_freight = parseFloat(frappe.web_form.get_value("custom_total_freight")) || 0;
    const xr            = parseFloat(frappe.web_form.get_value("custom_xrxe_com"))      || 0;

    if (total_freight && xr) {
        frappe.web_form.set_value("custom_total_freight_inr", total_freight * xr);

        //  IMPORTANT: trigger landing price calculation
        setTimeout(function () {
            calculate_total_landing_price_inr_webform();
        }, 100);
    }
}

// Calculate total landing price in INR whenever any of the components change
function calculate_total_landing_price_inr_webform() {
    const freight_inr = parseFloat(frappe.web_form.get_value("custom_total_freight_inr")) || 0;
    const dc          = parseFloat(frappe.web_form.get_value("custom_dc_inr")) || 0;
    const shipping    = parseFloat(frappe.web_form.get_value("custom_shipping_line_charges")) || 0;
    const cfs         = parseFloat(frappe.web_form.get_value("custom_cfs_charges")) || 0;

    const total = freight_inr + dc + shipping + cfs;

    frappe.web_form.set_value("custom_total_landing_pricecinr", total);
}


function attach_landing_price_listeners() {
    const fields = [
        "custom_dc_inr",
        "custom_shipping_line_charges",
        "custom_cfs_charges"
    ];

    fields.forEach(field => {
        const selector = `input[data-fieldname="${field}"]`;

        $(document)
            .off('input change blur', selector)
            .on('input change blur', selector, function () {
                calculate_total_landing_price_inr_webform();
            });
    });
}

// Fallback: watch DOM for success page appearance
const success_observer = new MutationObserver(function () {
    const submit_another = $('a:contains("Submit another response"), button:contains("Submit another response")');
    if (submit_another.length) {
        submit_another.hide();
        success_observer.disconnect();
    }
});

success_observer.observe(document.body, { childList: true, subtree: true });



function calculate_total_freight_webform() {
    const rate    = parseFloat(frappe.web_form.get_value("custom_rate_kg")) || 0;
    const fsc     = parseFloat(frappe.web_form.get_value("custom_fsc")) || 0;
    const sc      = parseFloat(frappe.web_form.get_value("custom_sc")) || 0;
    const xray    = parseFloat(frappe.web_form.get_value("custom_xray")) || 0;
    const weight  = parseFloat(frappe.web_form.get_value("custom_cw")) || 0;
    const exwords = parseFloat(frappe.web_form.get_value("custom_ex_words")) || 0;

    const total_rate = rate + fsc + sc + xray;
    const freight    = (total_rate * weight) + exwords;

    frappe.web_form.set_value("custom_total_freight", freight);

    // CRITICAL: chain next calculation
    setTimeout(function () {
        calculate_freight_inr_webform();
    }, 100);
}


function attach_freight_listeners() {
    const fields = [
        "custom_rate_kg",
        "custom_fsc",
        "custom_sc",
        "custom_xray",
        "custom_cw",
        "custom_ex_words"
    ];

    fields.forEach(field => {
        const selector = `input[data-fieldname="${field}"]`;

        $(document)
            .off('input change blur', selector)
            .on('input change blur', selector, function () {
                calculate_total_freight_webform();
            });
    });
}
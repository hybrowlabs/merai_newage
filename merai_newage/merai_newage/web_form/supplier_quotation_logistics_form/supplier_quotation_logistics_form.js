

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

//                     // ✅ Start countdown timer
//                     if (doc.custom_quotation_deadline1) {
//                         start_countdown_timer(doc.custom_quotation_deadline1);
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

//     // ✅ Countdown Timer Function
//     function start_countdown_timer(deadline_str) {
//         // Remove existing timer if any
//         $('#quotation-timer-banner').remove();

//         // Insert timer banner at the very top of the web form
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

//         // Insert before the web form container
//         $('.web-form-container, .form-page, [data-web-form]')
//             .first()
//             .prepend(timer_html);

//         // Fallback: prepend to main content area
//         if (!$('#quotation-timer-banner').length) {
//             $('main, .container').first().prepend(timer_html);
//         }

//         const deadline = new Date(deadline_str);
//         const timer_display = $('#quotation-timer-display');
//         const banner = $('#quotation-timer-banner');

//         function update_timer() {
//             const now = new Date();
//             const diff = deadline - now; // milliseconds remaining

//             if (diff <= 0) {
//                 // ✅ Expired
//                 banner.css({
//                     background: "#f8d7da",
//                     border: "1px solid #f5c6cb",
//                     color: "#721c24"
//                 });
//                 timer_display.css("color", "#721c24").text("EXPIRED");
//                 clearInterval(timer_interval);

//                 // Disable submit button when expired
//                 $('button[data-action="submit"], .btn-submit-web-form').prop('disabled', true)
//                     .text('Deadline Passed');
//                 return;
//             }

//             const days    = Math.floor(diff / (1000 * 60 * 60 * 24));
//             const hours   = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
//             const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
//             const seconds = Math.floor((diff % (1000 * 60)) / 1000);

//             let display = "";
//             if (days > 0) {
//                 display = `${days}d ${hours}h ${minutes}m ${seconds}s left`;
//             } else if (hours > 0) {
//                 display = `${hours}h ${minutes}m ${seconds}s left`;
//             } else {
//                 display = `${minutes}m ${seconds}s left`;
//             }

//             timer_display.text(display);

//             // ✅ Change color to red when less than 30 minutes left
//             if (diff < 30 * 60 * 1000) {
//                 banner.css({
//                     background: "#f8d7da",
//                     border: "1px solid #f5c6cb",
//                     color: "#721c24"
//                 });
//                 timer_display.css("color", "#721c24");
//             }
//             // ✅ Change color to orange when less than 1 hour left
//             else if (diff < 60 * 60 * 1000) {
//                 banner.css({
//                     background: "#ffe5d0",
//                     border: "1px solid #fd7e14",
//                     color: "#7d3c07"
//                 });
//                 timer_display.css("color", "#c0390e");
//             }
//         }

//         update_timer(); // run immediately
//         const timer_interval = setInterval(update_timer, 1000); // update every second
//     }

//     // ✅ Recalculate amounts
//     $(document).on('change', '.grid-body input', function () {
//         recalculate_amounts();
//     });

//     function recalculate_amounts() {
//         const items = frappe.web_form.doc.items || [];
//         let updated = false;

//         items.forEach(function (item) {
//             const rate = parseFloat(item.rate) || 0;
//             const qty  = parseFloat(item.qty)  || 0;
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
//         // Block submission if deadline passed
//         const banner = $('#quotation-timer-banner');
//         if ($('#quotation-timer-display').text() === "EXPIRED") {
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

    if (supplier) {
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
    }

    if (rfq) {
        frappe.call({
            method: "frappe.client.get",
            args: { doctype: "Request for Quotation", name: rfq },
            callback: function (r) {
                if (r.message) {
                    const doc = r.message;

                    frappe.web_form.set_value("company", doc.company);
                    frappe.web_form.set_value("plant", doc.custom_plant || "");
                    frappe.web_form.set_value("cost_center", doc.cost_center || "");
                    frappe.web_form.set_value("quotation_number", doc.name);
                    frappe.web_form.set_value("custom_rfq_reference", rfq);
                    frappe.web_form.set_value("custom_type", doc.custom_type);
                    frappe.web_form.set_value("custom_quotation_deadline", doc.custom_quotation_deadline1);

                    if (doc.custom_quotation_deadline1) {
                        // ✅ Check immediately on load — if already expired, show page right away
                        const deadline = new Date(doc.custom_quotation_deadline1);
                        if (deadline - new Date() <= 0) {
                            show_expired_page(doc.custom_quotation_deadline1, doc.name);
                            return; // stop further execution
                        }

                        start_countdown_timer(doc.custom_quotation_deadline1, doc.name);
                    }

                    if (doc.items && doc.items.length > 0) {
                        frappe.web_form.doc.items = doc.items.map(function (item, index) {
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
                                rate: 0,
                                amount: 0,
                                request_for_quotation: rfq
                            };
                        });

                        frappe.web_form.fields_dict['items'].refresh();

                        frappe.web_form.fields_dict['items'].grid.wrapper
                            .on('change', 'input[data-fieldname="rate"]', function () {
                                recalculate_amounts();
                            });
                    }
                }
            }
        });
    }

   function show_expired_page(deadline_str, rfq_name) {
    // ✅ Hide everything in the page body except navbar
    $('body').children().not('header, nav, .navbar, #navbar, .navbar-fixed-top').hide();
    
    // Also hide the web form section specifically
    $('.web-form-container, .form-page, [data-web-form], .container.with-padding, section').hide();

    $('#quotation-expired-page').remove();

    const expired_html = `
        <div id="quotation-expired-page" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #fff;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 20px;
            font-family: inherit;
            overflow-y: auto;
        ">
            <div style="
                width: 130px;
                height: 130px;
                background: #f8d7da;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 30px;
                animation: pulse 2s infinite;
            ">
                <span style="font-size: 65px;">⏰</span>
            </div>

            <h1 style="
                font-size: 38px;
                font-weight: 700;
                color: #721c24;
                margin: 0 0 14px 0;
            ">Oops! Time's Up</h1>

            <p style="
                font-size: 18px;
                color: #555;
                margin: 0 0 8px 0;
                max-width: 500px;
            ">The deadline for this quotation has passed.</p>

            <p style="
                font-size: 15px;
                color: #888;
                margin: 0 0 28px 0;
            ">You can no longer submit a quotation for 
                <strong>${rfq_name || 'this RFQ'}</strong>.
            </p>

            <div style="
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                padding: 14px 32px;
                margin-bottom: 32px;
                font-size: 15px;
                color: #856404;
            ">
                ⏳ Deadline was: <strong>${deadline_str}</strong>
            </div>

            <div style="
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px 32px;
                max-width: 420px;
            ">
                <p style="
                    font-size: 14px;
                    color: #666;
                    margin: 0;
                    line-height: 1.7;
                ">
                    📩 If you believe this is an error or need an extension,<br/>
                    please contact the <strong>procurement team</strong>.
                </p>
            </div>

            <style>
                @keyframes pulse {
                    0%   { transform: scale(1);    box-shadow: 0 0 0 0 rgba(220,53,69,0.4); }
                    70%  { transform: scale(1.05); box-shadow: 0 0 0 16px rgba(220,53,69,0); }
                    100% { transform: scale(1);    box-shadow: 0 0 0 0 rgba(220,53,69,0); }
                }
            </style>
        </div>
    `;

    // ✅ Append to body - position:fixed covers everything
    $('body').append(expired_html);
    window.scrollTo(0, 0);
}
    // ✅ Countdown Timer Function
    function start_countdown_timer(deadline_str, rfq_name) {
        $('#quotation-timer-banner').remove();

        const timer_html = `
            <div id="quotation-timer-banner" style="
                position: sticky;
                top: 0;
                z-index: 1000;
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
                <span>Quotation Deadline:</span>
                <span id="quotation-timer-display" style="
                    font-size: 17px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    color: #856404;
                ">Calculating...</span>
                <span style="margin-left:auto; font-size:13px; color:#aaa;">
                    Deadline: ${deadline_str}
                </span>
            </div>
        `;

        $('.web-form-container, .form-page, [data-web-form]').first().prepend(timer_html);

        if (!$('#quotation-timer-banner').length) {
            $('main, .container').first().prepend(timer_html);
        }

        const deadline      = new Date(deadline_str);
        const timer_display = $('#quotation-timer-display');
        const banner        = $('#quotation-timer-banner');

        function update_timer() {
            const now  = new Date();
            const diff = deadline - now;

            if (diff <= 0) {
                clearInterval(timer_interval);
                // ✅ Show expired full page when timer hits zero
                show_expired_page(deadline_str, rfq_name);
                return;
            }

            const days    = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours   = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            let display = days > 0
                ? `${days}d ${hours}h ${minutes}m ${seconds}s left`
                : hours > 0
                    ? `${hours}h ${minutes}m ${seconds}s left`
                    : `${minutes}m ${seconds}s left`;

            timer_display.text(display);

            if (diff < 30 * 60 * 1000) {
                banner.css({ background: "#f8d7da", border: "1px solid #f5c6cb", color: "#721c24" });
                timer_display.css("color", "#721c24");
            } else if (diff < 60 * 60 * 1000) {
                banner.css({ background: "#ffe5d0", border: "1px solid #fd7e14", color: "#7d3c07" });
                timer_display.css("color", "#c0390e");
            }
        }

        update_timer();
        const timer_interval = setInterval(update_timer, 1000);
    }

    // ✅ Recalculate amounts
    $(document).on('change', '.grid-body input', function () {
        recalculate_amounts();
    });

    function recalculate_amounts() {
        const items = frappe.web_form.doc.items || [];
        let updated = false;

        items.forEach(function (item) {
            const rate      = parseFloat(item.rate) || 0;
            const qty       = parseFloat(item.qty)  || 0;
            const newAmount = rate * qty;

            if (item.amount !== newAmount) {
                item.amount = newAmount;
                updated = true;
            }
        });

        if (updated) {
            frappe.web_form.fields_dict['items'].refresh();
        }
    }

    // ✅ Validate before submit
    frappe.web_form.validate = function () {
        if ($('#quotation-expired-page').length) {
            frappe.msgprint({
                title: "Deadline Passed",
                message: "The quotation deadline has passed. You can no longer submit.",
                indicator: "red"
            });
            return false;
        }

        const items = frappe.web_form.doc.items || [];
        for (let i = 0; i < items.length; i++) {
            const item  = items[i];
            const rate  = parseFloat(item.rate) || 0;
            const qty   = parseFloat(item.qty)  || 0;

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
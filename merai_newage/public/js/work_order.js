frappe.ui.form.on("Work Order", {
	on_submit(frm) {
		frappe.show_alert({
			message: __("Work Order Submitted"),
			indicator: "green",
		});

		// Reload document to reflect server-side changes
		frm.reload_doc();
	},
	refresh: function (frm) {
		console.log("-----work order refresh js called-----");
		setTimeout(function () {
			$('[data-original-title="Print"], .btn[title="Print"]').hide();

			frm.page.btn_secondary.find('.btn[data-original-title="Print"]').hide();

			$('.icon-btn svg use[href="#icon-printer"]').closest(".btn").hide();
		}, 100);
		if (frm.doc.docstatus === 1) {
			frappe.db
				.count("Job Card", {
					filters: { work_order: frm.doc.name },
				})
				.then((count) => {
					if (count > 0) {
						frm.remove_custom_button("Create Job Card");
						frm.remove_custom_button("Material Consumption");
						frm.remove_custom_button("Create Pick List");
						frm.remove_custom_button("Finish");
						frm.remove_custom_button("Start");
					}
				});
		}
		if (frm.doc.status === "Completed") {
			frm.add_custom_button("Print DHR", function () {
				frappe.call({
					method: "merai_newage.overrides.work_order.print_work_order_async",
					args: {
						name: frm.doc.name,
					},
					freeze: true,
					freeze_message: "Printing DHR...",
					callback: function (response) {
						window.open(window.location.origin + response.filecontent);
					},
				});
			});
		}

		if (frm.doc.status === "Completed" && frm.doc.custom_is_full_dhr === 1) {
			frm.add_custom_button("Print Full DHR", function () {
				frappe.call({
					method: "merai_newage.overrides.work_order.print_full_bmr",
					args: {
						name: frm.doc.name,
					},
					freeze: true,
					freeze_message: "Printing Full DHR...",
					callback: function (response) {
						window.open(window.location.origin + response.filecontent);
					},
				});
			});
		}

		setTimeout(() => {
			var completed = true;
			console.log("-----324------", frm.doc.operations);
			if (
				frm.doc.operations &&
				Array.isArray(frm.doc.operations) &&
				frm.doc.operations.length > 0
			) {
				frm.doc.operations.forEach(function (row) {
					if (row.completed_qty <= 0) {
						completed = false;
					}
				});
			} else {
				console.warn("⚠️ No operations found in the document (yet).");
				completed = false;
			}

			console.log("-----------328---------", completed);

			if (frm.doc.status == "In Process" && completed) {
				let btn = frm.add_custom_button("Completed Work Order", async function () {
					try {
						// 1st call
						let first = await frappe.call({
							method: "merai_newage.overrides.work_order.complete_work_order",
							args: { doc_name: frm.doc.name },
						});

						if (first.message) {
							frappe.show_alert({
								message: __("Work Order Completed Successfully"),
								indicator: "green",
							});
							await frm.reload_doc();
						}
						let batch_no = first.message.batch_no;

						// 2nd call (runs only after first is finished)
						let second = await frappe.call({
							method: "merai_newage.overrides.work_order.create_fg_consumption_entry",
							args: {
								doc_name: frm.doc.name,
								batch_no: batch_no,
							},
						});

						if (second.message) {
							frappe.show_alert({
								message: __("FG Consumption Entry Created Successfully"),
								indicator: "green",
							});
						}
					} catch (e) {
						frappe.msgprint(__("Something went wrong: ") + e.message);
					}
				});
				// btn.removeClass('btn-default').addClass('btn-dark');
			} else {
				frappe.message("All Operations must be completed to complete the Work Order");
			}
		}, 500);

		//workorder button for create and material request

		if (frm.doc.docstatus === 1) {
			// ---------- RESERVE BUTTON ----------
			frm.add_custom_button(
				__("Reserve"),
				function () {
					let d = new frappe.ui.Dialog({
						title: __("Reserve Items"),
						fields: [
							{
								label: __("Set Warehouse"),
								fieldname: "set_warehouse",
								fieldtype: "Link",
								options: "Warehouse",
							},
							{
								label: __("Items to Reserve"),
								fieldname: "items_to_reserve",
								fieldtype: "Table",
								fields: [
									{
										label: __("Item Code"),
										fieldname: "item_code",
										fieldtype: "Link",
										options: "Item",
										in_list_view: 1,
									},
									{
										label: __("Item Name"),
										fieldname: "item_name",
										fieldtype: "Data",
										in_list_view: 1,
									},
									{
										label: __("Quantity"),
										fieldname: "qty",
										fieldtype: "Float",
										in_list_view: 1,
									},
									{
										label: __("Warehouse"),
										fieldname: "warehouse",
										fieldtype: "Link",
										options: "Warehouse",
										in_list_view: 1,
									},
									{
										label: __("Batch No"),
										fieldname: "batch_no",
										fieldtype: "Link",
										options: "Batch",
										in_list_view: 1,
									},
								],
							},
						],
						size: "large",
						primary_action_label: __("Reserve"),
						primary_action(values) {
							frappe.call({
								method: "chatnext_manufacturing.config.py.work_order_methods.create_stock_reservation",
								args: {
									warehouse: values.set_warehouse,
									items_data: values.items_to_reserve,
									voucher_no: frm.doc.name,
								},
								callback(r) {
									if (!r.exc) {
										frappe.show_alert({
											message: __("Stock reservation created successfully"),
											indicator: "green",
										});
										d.hide();
										frm.reload_doc();
									}
								},
							});
						},
					});

					d.show();

					frappe.call({
						method: "frappe.client.get",
						args: {
							doctype: "Work Order",
							name: frm.doc.name,
						},
						callback(response) {
							let items = [];

							response.message.required_items.forEach((row) => {
								if (!row.custom_reseved) {
									items.push({
										item_code: row.item_code,
										item_name: row.item_name,
										qty: row.required_qty,
										warehouse: row.source_warehouse,
									});
								}
							});

							d.fields_dict.items_to_reserve.df.data = items;
							d.fields_dict.items_to_reserve.grid.refresh();
						},
					});
				},
				__("Create")
			);

			// ---------- MATERIAL REQUEST BUTTON ----------
			frm.add_custom_button(
				__("Material Request"),
				function () {
					frappe.call({
						method: "merai_newage.overrides.work_order.create_material_request",
						args: { data: frm.doc },
						callback(response) {
							if (response.message?.status === "success") {
								frappe.set_route(
									"Form",
									"Material Request",
									response.message.material_request
								);
								frappe.show_alert({
									message: __("Material Request created successfully"),
									indicator: "green",
								});
								frm.reload_doc();
							} else {
								frappe.msgprint({
									title: __("No Requirement"),
									message:
										response.message?.message ||
										__("No material requirement for this Work Order."),
									indicator: "orange",
								});
							}
						},
					});
				},
				__("Create")
			);

			// ---------- REMOVE UNWANTED DEFAULT BUTTONS ----------
			frm.remove_custom_button("Create Pick List");
			frm.remove_custom_button("Material Consumption");
			frm.remove_custom_button("Start");
		}
	},
});

// frappe.ui.form.on("Work Order", {

//     on_submit(frm) {
//         frappe.show_alert({
//             message: __("Work Order Submitted"),
//             indicator: "green"
//         });

//         // Reload document to reflect server-side changes
//         frm.reload_doc();
//     }
// ,
//     refresh: function (frm) {
//  setTimeout(function() {
//         $('[data-original-title="Print"], .btn[title="Print"]').hide();

//         frm.page.btn_secondary.find('.btn[data-original-title="Print"]').hide();

//         $('.icon-btn svg use[href="#icon-printer"]').closest('.btn').hide();
//     }, 100);
//          if (frm.doc.docstatus===1) {
//             frappe.db.count("Job Card", {
//                 filters: { work_order: frm.doc.name }
//             }).then(count => {
//                 if (count > 0) {
//                     frm.remove_custom_button("Create Job Card");
//                     frm.remove_custom_button("Material Consumption");
//                     frm.remove_custom_button("Create Pick List");
//                     frm.remove_custom_button("Finish");
//                     frm.remove_custom_button("Start");

//                 }
//             });
//         }
//         if (frm.doc.status === "Completed") {
//             frm.add_custom_button("Print DHR", function () {
//                 frappe.call({
//                     method: "merai_newage.overrides.work_order.print_work_order_async",
//                     args: {
//                         name: frm.doc.name
//                     },
//                     freeze: true,
//                     freeze_message: "Printing DHR...",
//                     callback: function (response) {
//                         window.open(window.location.origin + response.filecontent);
//                     }
//                 });
//             });
//         }

//         if (frm.doc.docstatus == 1 && frm.doc.custom_is_full_dhr === 1) {
//             frm.add_custom_button("Print Full DHR", function () {
//                 frappe.call({
//                     method: "merai_newage.overrides.work_order.print_full_bmr",
//                     args: {
//                         name: frm.doc.name
//                     },
//                     freeze: true,
//                     freeze_message: "Printing Full DHR...",
//                     callback: function (response) {
//                         window.open(window.location.origin + response.filecontent);
//                     }
//                 });
//             });
//         }

//         setTimeout(() => {
//                         var completed = true;
//                         console.log("-----324------",frm.doc.operations)
//                         if (frm.doc.operations && Array.isArray(frm.doc.operations) && frm.doc.operations.length > 0) {
//                             frm.doc.operations.forEach(function (row) {
//                                 if (row.completed_qty <= 0) {
//                                     completed = false;
//                                 }
//                             });
//                         } else {
//                             console.warn("⚠️ No operations found in the document (yet).");
//                             completed = false;
//                         }

//                         console.log("-----------328---------", completed);

//                 if (frm.doc.status == "In Process" && completed) {
//                     let btn = frm.add_custom_button("Completed Work Order", async function () {
//                         try {
//                             // 1st call
//                             let first = await frappe.call({
//                                 method: "merai_newage.overrides.work_order.complete_work_order",
//                                 args: { doc_name: frm.doc.name }
//                             });

//                             if (first.message) {
//                                 frappe.show_alert({
//                                     message: __("Work Order Completed Successfully"),
//                                     indicator: "green"
//                                 });
//                                 await frm.reload_doc();
//                             }
//                             let batch_no = first.message.batch_no;

//                             // 2nd call (runs only after first is finished)
//                             let second = await frappe.call({
//                                 method: "merai_newage.overrides.work_order.create_fg_consumption_entry",
//                                 args: {
//                                     doc_name: frm.doc.name,
//                                     batch_no: batch_no
//                                 }
//                             });

//                             if (second.message) {
//                                 frappe.show_alert({
//                                     message: __("FG Consumption Entry Created Successfully"),
//                                     indicator: "green"
//                                 });
//                             }
//                         } catch (e) {
//                             frappe.msgprint(__("Something went wrong: ") + e.message);
//                         }
//                     });
//                     // btn.removeClass('btn-default').addClass('btn-dark');
//                 }
//                 else {
//                     frappe.message("All Operations must be completed to complete the Work Order")

//                 }
//                                     }, 500);
//     }
// });

frappe.ui.form.on("Work Order", {
	on_submit(frm) {
		frappe.show_alert({
			message: __("Work Order Submitted"),
			indicator: "green",
		});

		// reload to reflect server-side changes
		frm.reload_doc();
	},

	refresh(frm) {
		// 🔑 Fetch Manufacturing Settings (Single Doctype)
		frappe.db
			.get_single_value("Meril Manufacturing Settings", "auto_stock")
			.then((auto_stock) => {
				if (!auto_stock) {
					return;
				}

				setTimeout(function () {
					$('[data-original-title="Print"], .btn[title="Print"]').hide();
					frm.page.btn_secondary.find('.btn[data-original-title="Print"]').hide();
					$('.icon-btn svg use[href="#icon-printer"]').closest(".btn").hide();
				}, 100);

				if (frm.doc.docstatus === 1) {
					frappe.db
						.count("Job Card", {
							filters: { work_order: frm.doc.name },
						})
						.then((count) => {
							if (count > 0) {
								frm.remove_custom_button("Create Job Card");
								frm.remove_custom_button("Material Consumption");
								frm.remove_custom_button("Create Pick List");
								frm.remove_custom_button("Finish");
								frm.remove_custom_button("Start");
							}
						});
				}

				if (frm.doc.status === "Completed") {
					frm.add_custom_button("Print DHR", function () {
						frappe.call({
							method: "merai_newage.overrides.work_order.print_work_order_async",
							args: { name: frm.doc.name },
							freeze: true,
							freeze_message: "Printing DHR...",
							callback: function (response) {
								window.open(window.location.origin + response.filecontent);
							},
						});
					});
					frm.add_custom_button("Create BRC", function () {
						frappe.call({
							method: "merai_newage.merai_newage.doctype.batch_release_certificate.batch_release_certificate.create_brc",
							args: {
								work_order: frm.doc.name, // send name clearly
							},
							freeze: true,
							callback: function (r) {
								if (r.message) {
									frappe.set_route(
										"Form",
										"Batch Release Certificate",
										r.message
									);
								}
							},
						});
					});
				}

				if (frm.doc.status === "Completed" && frm.doc.custom_is_full_dhr === 1) {
					frm.add_custom_button("Print Full DHR", function () {
						frappe.call({
							method: "merai_newage.overrides.work_order.print_full_bmr",
							args: { name: frm.doc.name },
							freeze: true,
							freeze_message: "Printing Full DHR...",
							callback: function (response) {
								window.open(window.location.origin + response.filecontent);
							},
						});
					});
				}

				setTimeout(() => {
					let completed = true;

					if (
						frm.doc.operations &&
						Array.isArray(frm.doc.operations) &&
						frm.doc.operations.length > 0
					) {
						frm.doc.operations.forEach((row) => {
							if (row.completed_qty <= 0) {
								completed = false;
							}
						});
					} else {
						completed = false;
					}

					if (frm.doc.status === "In Process" && completed) {
						frm.add_custom_button("Completed Work Order", async function () {
							try {
								// 1️⃣ Complete WO
								let first = await frappe.call({
									method: "merai_newage.overrides.work_order.complete_work_order",
									args: { doc_name: frm.doc.name },
								});

								if (first.message) {
									frappe.show_alert({
										message: __("Work Order Completed Successfully"),
										indicator: "green",
									});
									await frm.reload_doc();
								}

								let batch_no = first.message.batch_no;

								// 2️⃣ FG Consumption
								let second = await frappe.call({
									method: "merai_newage.overrides.work_order.create_fg_consumption_entry",
									args: {
										doc_name: frm.doc.name,
										batch_no: batch_no,
									},
								});

								if (second.message) {
									frappe.show_alert({
										message: __("FG Consumption Entry Created Successfully"),
										indicator: "green",
									});
								}
							} catch (e) {
								frappe.msgprint(__("Something went wrong: ") + e.message);
							}
						});
					} else if (frm.doc.status === "In Process") {
						frappe.msgprint(
							__("All Operations must be completed to complete the Work Order")
						);
					}
				}, 500);
			}); // 🔚 Manufacturing Settings check
	},
});

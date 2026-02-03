frappe.ui.form.on("Pickup Request", {
  onload: function (frm) {
    frappe.require("/assets/merai_newage/js/dimension_calculation.js");
  }
});
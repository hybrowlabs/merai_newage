import frappe
from merai_newage.merai_newage.utils.rfq_expiry  import update_single_rfq_expiry


def set_rfq_expiry_fields(doc, method=None):
    update_single_rfq_expiry(doc)
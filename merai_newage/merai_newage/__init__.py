# apps/merai_newage/merai_newage/__init__.py

import frappe
from erpnext.controllers.buying_controller import BuyingController

# Store original method
_original_auto_make_assets = BuyingController.auto_make_assets

def custom_auto_make_assets(self, asset_items):
    """Suppress popup for ACR-linked PRs"""
    
    # Check if PR is linked to ACR
    if hasattr(self, 'custom_asset_creation_request') and self.custom_asset_creation_request:
        # Suppress popup
        return
    
    # Call original for non-ACR PRs
    return _original_auto_make_assets(self, asset_items)

# Apply monkey patch
BuyingController.auto_make_assets = custom_auto_make_assets
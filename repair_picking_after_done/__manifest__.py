# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair picking after done",
    "version": "17.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "summary": "Transfer repaired move to another location directly from repair order",
    "category": "Repair",
    "depends": ["repair_type", "repair_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/repair.xml",
        "wizards/repair_move_transfer_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "license": "AGPL-3",
    "application": False,
    "post_load": "post_load_hook",
}

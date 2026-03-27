# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import models


def _post_init_set_default_grouped_repair_stages(env):
    """Set 'Draft' as the default stage for 'Add Grouped Repair' button visibility.

    Runs once after module installation. Does nothing if no 'Draft' stage exists.
    """
    env["res.config.settings"]._set_default_add_grouped_repair_stages()

# Copyright Cetmix OU 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(cr, registry):
    """Backfill sequence per repair using current order by id."""
    # Assign sequence = row_number()*10 for records where sequence is NULL
    cr.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY repair_id ORDER BY id) AS rn
            FROM repair_line
            WHERE sequence IS NULL
        )
        UPDATE repair_line rl
           SET sequence = ranked.rn * 10
          FROM ranked
         WHERE rl.id = ranked.id
        """
    )

    # Helpful index for ordering/filtering within a repair
    cr.execute(
        "CREATE INDEX IF NOT EXISTS repair_line_repair_id_sequence_idx "
        "ON repair_line (repair_id, sequence)"
    )

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    discord_user_id = fields.Char(
        string='Discord User ID',
        help=(
            'ID numerik akun Discord (bukan username). '
            'Cara dapat: Discord → Settings → Advanced → aktifkan Developer Mode → '
            'klik kanan nama user → Copy User ID.'
        ),
    )

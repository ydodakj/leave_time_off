from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ydod_discord_user_id = fields.Char(
        string='Discord User ID',
        help='Discord numeric user ID for @mentions in leave notifications.',
        groups='hr.group_hr_user',
    )


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _notify_discord(self, event):
        cfg_model = self.env['ydod.discord.webhook.config'].sudo()
        for leave in self:
            cfg_model.send_leave_notification(leave, event)

    def action_confirm(self):
        result = super().action_confirm()
        self._notify_discord('confirm')
        return result

    def action_validate(self):
        result = super().action_validate()
        self._notify_discord('validate')
        return result

    def action_refuse(self):
        result = super().action_refuse()
        self._notify_discord('refuse')
        return result

    def action_draft(self):
        result = super().action_draft()
        self._notify_discord('reset')
        return result

import logging
import requests
from datetime import datetime, timezone, timedelta
from odoo import api, models

_logger = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))

EVENT_LABEL = {
    'confirm': ('📋', 'Leave Request Diajukan'),
    'validate': ('✅', 'Leave Request Disetujui'),
    'refuse':   ('❌', 'Leave Request Ditolak'),
    'reset':    ('🔄', 'Leave Request Direset ke Draft'),
}


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_discord_webhook(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'discord.leave.webhook.url', ''
        )

    def _get_mention_str(self, employee):
        user = employee.user_id
        if user and user.discord_user_id:
            return f'<@{user.discord_user_id}>'
        return f'**{employee.name}**'

    def _now_str(self):
        return datetime.now(tz=WIB).strftime('%d %b %Y %H:%M:%S WIB')

    def _build_message(self, event):
        self.ensure_one()
        icon, label = EVENT_LABEL.get(event, ('📋', 'Leave Update'))
        employee = self.employee_id
        mention = self._get_mention_str(employee)
        leave_type = self.holiday_status_id.name or '-'
        duration = self.number_of_days
        date_from = self.date_from.date() if self.date_from else '-'
        date_to = self.date_to.date() if self.date_to else '-'

        lines = [
            f'{icon} **{label}**\n',
            f'👤 Karyawan: {mention}',
            f'📝 Jenis Cuti: **{leave_type}**',
            f'📅 Tanggal: **{date_from}** s/d **{date_to}** ({duration} hari)',
        ]
        if self.name:
            lines.append(f'💬 Alasan: {self.name}')
        if event == 'refuse' and hasattr(self, 'refuse_reason') and self.refuse_reason:
            lines.append(f'🚫 Alasan Tolak: {self.refuse_reason}')

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        leave_url = f'{base_url}/odoo/time-off/{self.id}'
        lines.append(f'🕐 Waktu: **{self._now_str()}**')
        lines.append(f'\n🔗 {leave_url}')

        return '\n'.join(lines)

    def _send_discord(self, event):
        webhook_url = self._get_discord_webhook()
        if not webhook_url:
            _logger.warning('discord.leave.webhook.url belum dikonfigurasi di System Parameters.')
            return
        for leave in self:
            content = leave._build_message(event)
            try:
                resp = requests.post(webhook_url, json={'content': content}, timeout=10)
                resp.raise_for_status()
                _logger.info('Discord leave notification sent: %s event=%s', leave.id, event)
            except Exception as exc:
                _logger.error('Gagal kirim Discord leave notification: %s', exc)

    def action_confirm(self):
        result = super().action_confirm()
        self._send_discord('confirm')
        return result

    def action_validate(self):
        result = super().action_validate()
        self._send_discord('validate')
        return result

    def action_refuse(self):
        result = super().action_refuse()
        self._send_discord('refuse')
        return result

    def action_draft(self):
        result = super().action_draft()
        self._send_discord('reset')
        return result

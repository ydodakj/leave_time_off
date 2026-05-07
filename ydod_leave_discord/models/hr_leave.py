import logging
import requests
from datetime import datetime, timezone, timedelta
from odoo import models

_logger = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))

# Semua state hr.leave → (icon, label pesan Discord)
STATE_EVENT = {
    'confirm':   ('📋', 'Leave Diajukan'),
    'validate1': ('👍', 'Leave Disetujui — Approval Pertama'),
    'validate':  ('✅', 'Leave Disetujui'),
    'refuse':    ('❌', 'Leave Ditolak'),
    'cancel':    ('🚫', 'Leave Dibatalkan'),
    'draft':     ('🔄', 'Leave Direset ke Draft'),
}


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # ── helpers ──────────────────────────────────────────────────────────────

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

    def _build_message(self, state):
        self.ensure_one()
        icon, label = STATE_EVENT.get(state, ('📋', 'Leave Update'))
        employee = self.employee_id
        mention  = self._get_mention_str(employee)
        leave_type = self.holiday_status_id.name or '-'
        duration   = self.number_of_days
        date_from  = self.date_from.date() if self.date_from else '-'
        date_to    = self.date_to.date() if self.date_to else '-'

        lines = [
            f'{icon} **{label}**\n',
            f'👤 Karyawan: {mention}',
            f'📝 Jenis: **{leave_type}**',
            f'📅 Tanggal: **{date_from}** s/d **{date_to}** ({duration} hari)',
        ]
        if self.name:
            lines.append(f'💬 Alasan: {self.name}')
        if state == 'refuse' and getattr(self, 'refuse_reason', None):
            lines.append(f'🚫 Alasan Tolak: {self.refuse_reason}')

        base_url  = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        leave_url = f'{base_url}/odoo/time-off/{self.id}'
        lines.append(f'🕐 Waktu: **{self._now_str()}**')
        lines.append(f'\n🔗 {leave_url}')
        return '\n'.join(lines)

    def _send_discord(self, state):
        webhook_url = self._get_discord_webhook()
        if not webhook_url:
            _logger.warning('discord.leave.webhook.url belum dikonfigurasi di System Parameters.')
            return
        for leave in self:
            content = leave._build_message(state)
            try:
                resp = requests.post(webhook_url, json={'content': content}, timeout=10)
                resp.raise_for_status()
                _logger.info('Discord leave notification sent: leave=%s state=%s', leave.id, state)
            except Exception as exc:
                _logger.error('Gagal kirim Discord leave notification: %s', exc)

    # ── write override — tangkap semua perubahan state ────────────────────────

    def write(self, vals):
        old_states = {}
        if 'state' in vals:
            old_states = {leave.id: leave.state for leave in self}

        result = super().write(vals)

        if 'state' in vals:
            new_state = vals['state']
            if new_state in STATE_EVENT:
                changed = self.filtered(
                    lambda l: old_states.get(l.id) != new_state
                )
                if changed:
                    changed._send_discord(new_state)

        return result

    # ── manual button ─────────────────────────────────────────────────────────

    def action_send_discord_manual(self):
        """Kirim notifikasi Discord sesuai state saat ini (tombol manual)."""
        for leave in self:
            if leave.state in STATE_EVENT:
                leave._send_discord(leave.state)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Discord',
                'message': 'Notifikasi berhasil dikirim ke Discord.',
                'type': 'success',
            },
        }

import re
import requests
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

DISCORD_COLORS = {
    'confirm': 16776960,    # Yellow — submitted
    'validate': 65280,      # Green — approved
    'refuse': 16711680,     # Red — refused
    'reset': 8421504,       # Gray — reset to draft
}

WEBHOOK_RE = re.compile(
    r'^https://discord(?:app)?\.com/api/webhooks/\d+/[\w-]+$'
)


class DiscordWebhookConfig(models.Model):
    _name = 'ydod.discord.webhook.config'
    _description = 'Discord Webhook Configuration'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    webhook_url = fields.Char(
        string='Webhook URL',
        required=True,
        help='Discord webhook URL: https://discord.com/api/webhooks/...',
    )
    is_global = fields.Boolean(
        string='Global (all leave types)',
        default=True,
        help='Apply to all leave types when enabled.',
    )
    leave_type_ids = fields.Many2many(
        'hr.leave.type',
        string='Leave Types',
        help='Specific leave types when not global.',
    )

    # Notification triggers
    notify_submit = fields.Boolean('Notify on Submit', default=True)
    notify_approve = fields.Boolean('Notify on Approve', default=True)
    notify_refuse = fields.Boolean('Notify on Refuse', default=True)
    notify_reset = fields.Boolean('Notify on Reset to Draft', default=False)

    # Message customisation
    username = fields.Char(default='Odoo HR')
    avatar_url = fields.Char(string='Bot Avatar URL')
    mention_employee = fields.Boolean(
        string='Mention Employee (Discord User ID)',
        default=False,
        help='If the employee has a Discord User ID set, mention them.',
    )

    @api.constrains('webhook_url')
    def _check_webhook_url(self):
        for rec in self:
            if not WEBHOOK_RE.match(rec.webhook_url):
                raise ValidationError(_(
                    'Invalid Discord webhook URL: %(url)s',
                    url=rec.webhook_url,
                ))

    def action_test_webhook(self):
        self.ensure_one()
        payload = {
            'username': self.username or 'Odoo HR',
            'embeds': [{
                'title': 'Webhook Test',
                'description': 'Connection successful from Odoo!',
                'color': 3447003,
            }],
        }
        try:
            resp = requests.post(
                self.webhook_url, json=payload, timeout=10
            )
            resp.raise_for_status()
        except Exception as exc:
            raise UserError(_('Test failed: %s') % exc)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Discord webhook responded successfully.'),
                'type': 'success',
            },
        }

    def _build_embed(self, leave, event):
        """Return a Discord embed dict for the given leave and event."""
        employee = leave.employee_id
        leave_type = leave.holiday_status_id
        duration = leave.number_of_days

        titles = {
            'confirm': f'Leave Request Submitted — {employee.name}',
            'validate': f'Leave Approved — {employee.name}',
            'refuse': f'Leave Refused — {employee.name}',
            'reset': f'Leave Reset to Draft — {employee.name}',
        }

        fields_embed = [
            {'name': 'Employee', 'value': employee.name, 'inline': True},
            {'name': 'Leave Type', 'value': leave_type.name, 'inline': True},
            {
                'name': 'Duration',
                'value': f'{duration} day(s)',
                'inline': True,
            },
            {
                'name': 'From',
                'value': str(leave.date_from.date()) if leave.date_from else '-',
                'inline': True,
            },
            {
                'name': 'To',
                'value': str(leave.date_to.date()) if leave.date_to else '-',
                'inline': True,
            },
        ]
        if leave.name:
            fields_embed.append({'name': 'Reason', 'value': leave.name, 'inline': False})

        if event == 'refuse' and leave.refuse_reason:
            fields_embed.append(
                {'name': 'Refuse Reason', 'value': leave.refuse_reason, 'inline': False}
            )

        manager_name = (
            leave.holiday_status_id.responsible_ids[:1].name
            if leave.holiday_status_id.responsible_ids
            else '-'
        )
        fields_embed.append({'name': 'Manager', 'value': manager_name, 'inline': True})

        embed = {
            'title': titles.get(event, 'Leave Update'),
            'color': DISCORD_COLORS.get(event, 8421504),
            'fields': fields_embed,
            'footer': {'text': 'Odoo HR • YDOD Leave Discord Integration'},
        }

        if employee.image_128:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            embed['thumbnail'] = {
                'url': f'{base_url}/web/image/hr.employee/{employee.id}/image_128'
            }

        return embed

    def send_leave_notification(self, leave, event):
        """Send a Discord notification for event on leave."""
        configs = self.search([('active', '=', True)])
        for cfg in configs:
            trigger_map = {
                'confirm': cfg.notify_submit,
                'validate': cfg.notify_approve,
                'refuse': cfg.notify_refuse,
                'reset': cfg.notify_reset,
            }
            if not trigger_map.get(event):
                continue
            if not cfg.is_global:
                if leave.holiday_status_id not in cfg.leave_type_ids:
                    continue

            content = ''
            if cfg.mention_employee:
                discord_uid = leave.employee_id.ydod_discord_user_id
                if discord_uid:
                    content = f'<@{discord_uid}>'

            payload = {
                'username': cfg.username or 'Odoo HR',
                'content': content,
                'embeds': [cfg._build_embed(leave, event)],
            }
            if cfg.avatar_url:
                payload['avatar_url'] = cfg.avatar_url

            try:
                resp = requests.post(cfg.webhook_url, json=payload, timeout=10)
                resp.raise_for_status()
            except Exception as exc:
                _logger.error(
                    'Discord webhook [%s] failed for leave %s: %s',
                    cfg.name, leave.id, exc,
                )

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ImportIndonesianHolidayWizard(models.TransientModel):
    _name = 'ydod.import.indonesian.holiday.wizard'
    _description = 'Import Indonesian Public Holidays Wizard'

    year = fields.Integer(
        required=True,
        default=lambda self: datetime.now().year,
    )
    import_mode = fields.Selection([
        ('global', 'Global Public Holidays (muncul di Time Off > Public Holidays)'),
        ('calendar', 'Per Work Schedule (terapkan ke jadwal kerja tertentu)'),
        ('both', 'Keduanya'),
    ], string='Import Mode', required=True, default='global')

    calendar_ids = fields.Many2many(
        'resource.calendar',
        string='Work Schedules',
        help='Kosongkan untuk semua jadwal aktif. Hanya relevan jika mode "Per Work Schedule".',
    )
    skip_existing = fields.Boolean(
        string='Skip Duplikat',
        default=True,
    )
    dry_run = fields.Boolean(
        string='Preview Saja (tidak import)',
        default=False,
    )
    preview_html = fields.Html(readonly=True)

    def _get_calendars(self):
        if self.calendar_ids:
            return self.calendar_ids
        return self.env['resource.calendar'].search([('active', '=', True)])

    def _existing_global_dates(self):
        leaves = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', False),
            ('resource_id', '=', False),
        ])
        return {l.date_from.date() for l in leaves if l.date_from}

    def _existing_calendar_dates(self, calendar):
        leaves = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),
        ])
        return {l.date_from.date() for l in leaves if l.date_from}

    def action_preview(self):
        provider = self.env['ydod.indonesian.holiday.provider']
        holidays = provider.get_holidays(self.year)
        if not holidays:
            raise UserError(_('Tidak ada data hari libur untuk tahun %d.') % self.year)

        rows = ''.join(
            f'<tr><td>{h["holiday_date"]}</td><td>{h["holiday_name"]}</td></tr>'
            for h in sorted(holidays, key=lambda x: x['holiday_date'])
        )
        self.preview_html = (
            f'<table class="table table-sm table-bordered">'
            f'<thead><tr><th>Tanggal</th><th>Nama Hari Libur</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<p class="text-muted">Total: {len(holidays)} hari libur untuk tahun {self.year}.</p>'
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        if self.dry_run:
            return self.action_preview()

        provider = self.env['ydod.indonesian.holiday.provider']
        holidays = provider.get_holidays(self.year)
        if not holidays:
            raise UserError(_('Tidak ada data hari libur untuk tahun %d.') % self.year)

        global_created = 0
        calendar_created = 0
        skipped = 0

        if self.import_mode in ('global', 'both'):
            existing = self._existing_global_dates() if self.skip_existing else set()
            for h in holidays:
                try:
                    hdate = provider.parse_date(h['holiday_date'])
                except ValueError:
                    continue
                if hdate in existing:
                    skipped += 1
                    continue
                self.env['resource.calendar.leaves'].create({
                    'name': h['holiday_name'],
                    'calendar_id': False,
                    'resource_id': False,
                    'date_from': datetime(hdate.year, hdate.month, hdate.day, 0, 0, 0),
                    'date_to': datetime(hdate.year, hdate.month, hdate.day, 23, 59, 59),
                    'time_type': 'leave',
                })
                existing.add(hdate)
                global_created += 1

        if self.import_mode in ('calendar', 'both'):
            for calendar in self._get_calendars():
                existing = self._existing_calendar_dates(calendar) if self.skip_existing else set()
                for h in holidays:
                    try:
                        hdate = provider.parse_date(h['holiday_date'])
                    except ValueError:
                        continue
                    if hdate in existing:
                        skipped += 1
                        continue
                    self.env['resource.calendar.leaves'].create({
                        'name': h['holiday_name'],
                        'calendar_id': calendar.id,
                        'resource_id': False,
                        'date_from': datetime(hdate.year, hdate.month, hdate.day, 0, 0, 0),
                        'date_to': datetime(hdate.year, hdate.month, hdate.day, 23, 59, 59),
                        'time_type': 'leave',
                    })
                    existing.add(hdate)
                    calendar_created += 1

        parts = []
        if global_created:
            parts.append(f'{global_created} global public holiday')
        if calendar_created:
            parts.append(f'{calendar_created} per-calendar entry')
        if skipped:
            parts.append(f'{skipped} dilewati (duplikat)')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hari Libur Indonesia Diimport'),
                'message': ', '.join(parts) + f' untuk tahun {self.year}.',
                'type': 'success',
                'sticky': True,
            },
        }

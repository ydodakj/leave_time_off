"""
Fetch Indonesian national public holidays.

Primary source  : https://api-harilibur.vercel.app/api?month=0&year=YYYY
Fallback source : https://dayoffapi.vercel.app/api?year=YYYY
Offline fallback: built-in data for years where the API may not yet have data.
"""

import requests
import logging
from datetime import date, datetime
from odoo import models, _

_logger = logging.getLogger(__name__)

_API_HARI_LIBUR = 'https://api-hari-libur.vercel.app/api'
_API_DAYOFF = 'https://dayoffapi.vercel.app/api'

# Offline fallback — Indonesia 2025 holidays (Keppres/SKB)
_OFFLINE_2025 = [
    {'holiday_date': '2025-01-01', 'holiday_name': 'Tahun Baru Masehi'},
    {'holiday_date': '2025-01-27', 'holiday_name': 'Isra Mi\'raj Nabi Muhammad SAW'},
    {'holiday_date': '2025-01-28', 'holiday_name': 'Cuti Bersama Isra Mi\'raj'},
    {'holiday_date': '2025-01-29', 'holiday_name': 'Tahun Baru Imlek 2576'},
    {'holiday_date': '2025-03-28', 'holiday_name': 'Hari Suci Nyepi (Tahun Baru Saka 1947)'},
    {'holiday_date': '2025-03-29', 'holiday_name': 'Wafat Isa Al-Masih'},
    {'holiday_date': '2025-03-31', 'holiday_name': 'Cuti Bersama Idul Fitri'},
    {'holiday_date': '2025-03-30', 'holiday_name': 'Cuti Bersama Idul Fitri'},
    {'holiday_date': '2025-03-31', 'holiday_name': 'Hari Raya Idul Fitri 1446 H (1)'},
    {'holiday_date': '2025-04-01', 'holiday_name': 'Hari Raya Idul Fitri 1446 H (2)'},
    {'holiday_date': '2025-04-02', 'holiday_name': 'Cuti Bersama Idul Fitri'},
    {'holiday_date': '2025-04-03', 'holiday_name': 'Cuti Bersama Idul Fitri'},
    {'holiday_date': '2025-04-04', 'holiday_name': 'Cuti Bersama Idul Fitri'},
    {'holiday_date': '2025-04-18', 'holiday_name': 'Wafat Isa Al-Masih'},
    {'holiday_date': '2025-05-01', 'holiday_name': 'Hari Buruh Internasional'},
    {'holiday_date': '2025-05-12', 'holiday_name': 'Hari Raya Waisak 2569 BE'},
    {'holiday_date': '2025-05-13', 'holiday_name': 'Cuti Bersama Waisak'},
    {'holiday_date': '2025-05-29', 'holiday_name': 'Kenaikan Isa Al-Masih'},
    {'holiday_date': '2025-06-01', 'holiday_name': 'Hari Lahir Pancasila'},
    {'holiday_date': '2025-06-06', 'holiday_name': 'Hari Raya Idul Adha 1446 H'},
    {'holiday_date': '2025-06-07', 'holiday_name': 'Cuti Bersama Idul Adha'},
    {'holiday_date': '2025-06-27', 'holiday_name': 'Tahun Baru Islam 1447 H'},
    {'holiday_date': '2025-08-17', 'holiday_name': 'Hari Kemerdekaan Republik Indonesia'},
    {'holiday_date': '2025-09-05', 'holiday_name': 'Maulid Nabi Muhammad SAW'},
    {'holiday_date': '2025-12-25', 'holiday_name': 'Hari Raya Natal'},
    {'holiday_date': '2025-12-26', 'holiday_name': 'Cuti Bersama Natal'},
]

# Offline fallback — Indonesia 2026 holidays (estimated)
_OFFLINE_2026 = [
    {'holiday_date': '2026-01-01', 'holiday_name': 'Tahun Baru Masehi'},
    {'holiday_date': '2026-02-17', 'holiday_name': 'Tahun Baru Imlek 2577'},
    {'holiday_date': '2026-03-17', 'holiday_name': 'Hari Suci Nyepi (Tahun Baru Saka 1948)'},
    {'holiday_date': '2026-03-20', 'holiday_name': 'Isra Mi\'raj Nabi Muhammad SAW'},
    {'holiday_date': '2026-03-21', 'holiday_name': 'Hari Raya Idul Fitri 1447 H (1)'},
    {'holiday_date': '2026-03-22', 'holiday_name': 'Hari Raya Idul Fitri 1447 H (2)'},
    {'holiday_date': '2026-04-03', 'holiday_name': 'Wafat Isa Al-Masih'},
    {'holiday_date': '2026-05-01', 'holiday_name': 'Hari Buruh Internasional'},
    {'holiday_date': '2026-05-14', 'holiday_name': 'Kenaikan Isa Al-Masih'},
    {'holiday_date': '2026-05-31', 'holiday_name': 'Hari Raya Waisak 2570 BE'},
    {'holiday_date': '2026-06-01', 'holiday_name': 'Hari Lahir Pancasila'},
    {'holiday_date': '2026-05-27', 'holiday_name': 'Hari Raya Idul Adha 1447 H'},
    {'holiday_date': '2026-08-17', 'holiday_name': 'Hari Kemerdekaan Republik Indonesia'},
    {'holiday_date': '2026-12-25', 'holiday_name': 'Hari Raya Natal'},
]

_OFFLINE_DATA = {
    2025: _OFFLINE_2025,
    2026: _OFFLINE_2026,
}


class IndonesianHolidayProvider(models.AbstractModel):
    _name = 'ydod.indonesian.holiday.provider'
    _description = 'Indonesian Public Holiday Data Provider'

    def _fetch_from_hari_libur(self, year):
        resp = requests.get(
            _API_HARI_LIBUR, params={'year': year}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        result = []
        for item in data:
            d = item.get('holiday_date') or item.get('tanggal')
            name = item.get('holiday_name') or item.get('keterangan') or ''
            is_national = item.get('is_national_holiday', True)
            if d and is_national:
                result.append({'holiday_date': d, 'holiday_name': name})
        return result

    def _fetch_from_dayoff(self, year):
        resp = requests.get(_API_DAYOFF, params={'year': year}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = []
        for item in data:
            d = item.get('tanggal') or item.get('date')
            name = item.get('keterangan') or item.get('name') or ''
            if d:
                result.append({'holiday_date': d, 'holiday_name': name})
        return result

    def get_holidays(self, year):
        """
        Return list of dicts: {holiday_date: 'YYYY-MM-DD', holiday_name: str}
        Tries primary API → fallback API → offline data.
        """
        for fetcher in (self._fetch_from_hari_libur, self._fetch_from_dayoff):
            try:
                holidays = fetcher(year)
                if holidays:
                    _logger.info(
                        'Indonesian holidays for %d fetched from %s: %d records',
                        year, fetcher.__name__, len(holidays),
                    )
                    return holidays
            except Exception as exc:
                _logger.warning('Holiday API fetch failed (%s): %s', fetcher.__name__, exc)

        # Use offline fallback
        offline = _OFFLINE_DATA.get(year, [])
        _logger.warning(
            'Using offline holiday data for %d (%d records)', year, len(offline)
        )
        return list(offline)

    def parse_date(self, date_str):
        """Parse date string in various formats to a date object."""
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f'Cannot parse date: {date_str}')

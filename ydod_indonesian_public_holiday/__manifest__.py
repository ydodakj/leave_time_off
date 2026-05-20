{
    'name': 'Indonesian Public Holiday',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Import Indonesian public holidays into Odoo Time Off (Odoo 19)',
    'description': """
        Automatically fetch and import Indonesian national public holidays
        into Odoo's Work Schedule (resource.calendar.leaves) and / or
        Global Time Off (hr.leave.public.holiday).

        Data sources:
        - API Hari Libur Indonesia (api-harilibur.vercel.app)
        - Keputusan Bersama Pemerintah RI (fallback / offline data)

        Features:
        - Wizard to import holidays for a selected year
        - Prevents duplicate entries
        - Supports multiple work calendars
        - Optional: auto-create a global public holiday entry
        - Optional: dry-run preview before importing
    """,
    'author': 'Dody Ahmad Kusuma Jaya',
    'website': 'https://cv.dodyakj.online/',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'resource'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_holiday_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'images': [
        'static/description/indonesian_holiday_demo.gif',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

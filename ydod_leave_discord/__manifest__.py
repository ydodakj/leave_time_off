{
    'name': 'Leave Discord Integration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Send Discord notifications for leave requests (create, approve, refuse, reset)',
    'description': """
        Integrate Odoo Leave Management with Discord.
        - Notify Discord channel when leave is submitted
        - Notify when leave is approved or refused
        - Notify when leave is reset to draft
        - Configurable webhook URL per leave type or global
        - Customizable message templates with dynamic fields
        - Support for multiple Discord channels
    """,
    'author': 'Dody Ahmad Kusuma Jaya',
    'website': 'https://github.com/dodyakj',
    'license': 'LGPL-3',
    'depends': ['hr_holidays','hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/discord_config_data.xml',
        'views/discord_config_views.xml',
        'views/hr_leave_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

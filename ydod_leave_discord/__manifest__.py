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
        - Webhook URL configured via System Parameters
        - Employee mention via Discord User ID on res.users
    """,
    'author': 'Dody Ahmad Kusuma Jaya',
    'website': 'https://github.com/dodyakj',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

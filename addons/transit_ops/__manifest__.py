{
    'name': 'TransitOps — Smart Transport Operations Platform',
    'version': '18.0.1.0.0',
    'category': 'Operations/Fleet',
    'summary': 'End-to-end transport operations: vehicles, drivers, trips, maintenance, fuel, and analytics.',
    'author': 'Hackathon Team',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security — load first
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data / Sequences
        'data/sequences.xml',
        'data/cron_jobs.xml',

        # Views
        'views/vehicle_views.xml',
        'views/driver_views.xml',
        'views/trip_views.xml',
        'views/maintenance_views.xml',
        'views/fuel_log_views.xml',
        'views/expense_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',

        # Reports
        'reports/report_actions.xml',
        'reports/report_templates.xml',

        # Wizards
        'wizard/report_wizard_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'transit_ops/static/src/css/dashboard.css',
            'transit_ops/static/src/xml/dashboard.xml',
            'transit_ops/static/src/js/dashboard.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}

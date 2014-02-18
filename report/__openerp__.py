{
    'name': 'Report',
    'category': 'Website',
    'summary': 'Report',
    'version': '1.0',
    'description': """
Report
        """,
    'author': 'OpenERP SA',
    'depends': ['base', 'website'],
    'data': [
        'views/layouts.xml',
        'views/paperformat_view.xml',
        'views/res_company_view.xml',
        'data/report_paperformat.xml',
        'security/ir.model.access.csv',
    ],
    'js': [
        'static/src/js/qwebactionmanager.js',
    ],
    'installable': True,
}

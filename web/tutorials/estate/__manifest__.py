{
    'name': 'Real Estate',
    'version': '1.0',
    'summary': 'Real Estate Management',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_property_action.xml',  # Load action file first
        'views/estate_menus.xml',            # Then load the menu file
    ],
    'application': True,
}


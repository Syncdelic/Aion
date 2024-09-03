{
    'name': 'WhatsApp Chatbot Template',
    'version': '1.0.0',
    'category': 'Tools',
    'author': 'Rodrigo Rea',
    'description': """A module that integrates Twilio and LangChain to handle WhatsApp messages.""",
    'depends': ['base', 'twilio_base', 'openai_base'],
    'data': [],
    'external_dependencies': {
        'python': ['langchain', 'langchain_openai', 'twilio', 'langchain_core'],
    },
    'installable': True,
    'application': False,
}


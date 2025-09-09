# Form choices and constants

FONT_FAMILY_CHOICES = [
    ('Inter', 'Inter (Moderna y limpia)'),
    ('Poppins', 'Poppins (Geométrica y amigable)'),
    ('Roboto', 'Roboto (Clásica de Google)'),
    ('Montserrat', 'Montserrat (Elegante y versátil)'),
    ('Open Sans', 'Open Sans (Muy legible)'),
    ('Lato', 'Lato (Humanista y cálida)'),
    ('Source Sans Pro', 'Source Sans Pro (Profesional)'),
    ('Nunito', 'Nunito (Redondeada y amigable)'),
    ('Raleway', 'Raleway (Sofisticada)'),
    ('Ubuntu', 'Ubuntu (Moderna)'),
    ('Playfair Display', 'Playfair Display (Serif elegante)'),
    ('Merriweather', 'Merriweather (Serif tradicional)'),
    ('PT Serif', 'PT Serif (Serif clásica)'),
    ('Libre Baskerville', 'Libre Baskerville (Serif para texto)'),
    ('Crimson Text', 'Crimson Text (Serif literaria)'),
    ('Inconsolata', 'Inconsolata (Monospace para código)'),
    ('Fira Mono', 'Fira Mono (Monospace moderna)'),
    ('JetBrains Mono', 'JetBrains Mono (Para desarrolladores)'),
    ('Dancing Script', 'Dancing Script (Script elegante)'),
    ('Pacifico', 'Pacifico (Script casual)'),
    ('Amatic SC', 'Amatic SC (Manuscrita)'),
    ('Caveat', 'Caveat (Manuscrita natural)'),
    ('Kalam', 'Kalam (Manuscrita india)'),
    ('Patrick Hand', 'Patrick Hand (Manuscrita personal)')
]

LAYOUT_CHOICES = [
    ('classic', 'Clásico'),
    ('modern', 'Moderno'),
    ('minimal', 'Minimalista')
]

AVATAR_SHAPE_CHOICES = [
    ('circle', 'Circular'),
    ('rounded', 'Redondeado'),
    ('square', 'Cuadrado'),
    ('rectangle', 'Rectangular (ideal para logos)')
]

# Social networks configuration - Primary networks (top priority)
SOCIAL_NETWORKS_PRIMARY = [
    {
        'name': 'Instagram',
        'field': 'instagram',
        'icon': 'fab fa-instagram',
        'color': '#E4405F',
        'base_url': 'https://instagram.com/',
        'priority': 1
    },
    {
        'name': 'Facebook',
        'field': 'facebook',
        'icon': 'fab fa-facebook',
        'color': '#1877F2',
        'base_url': 'https://facebook.com/',
        'priority': 1
    },
    {
        'name': 'WhatsApp Business',
        'field': 'whatsapp_business',
        'icon': 'fab fa-whatsapp',
        'color': '#25D366',
        'base_url': 'https://wa.me/',
        'priority': 1
    },
    {
        'name': 'Email',
        'field': 'email_public',
        'icon': 'fas fa-envelope',
        'color': '#EA4335',
        'base_url': 'mailto:',
        'priority': 1
    },
    {
        'name': 'LinkedIn',
        'field': 'linkedin',
        'icon': 'fab fa-linkedin',
        'color': '#0A66C2',
        'base_url': 'https://linkedin.com/in/',
        'priority': 1
    },
    {
        'name': 'X (Twitter)',
        'field': 'twitter',
        'icon': 'fab fa-x-twitter',
        'color': '#000000',
        'base_url': 'https://x.com/',
        'priority': 1
    },
    {
        'name': 'YouTube',
        'field': 'youtube',
        'icon': 'fab fa-youtube',
        'color': '#FF0000',
        'base_url': 'https://youtube.com/@',
        'priority': 1
    },
    {
        'name': 'TikTok',
        'field': 'tiktok',
        'icon': 'fab fa-tiktok',
        'color': '#000000',
        'base_url': 'https://tiktok.com/@',
        'priority': 1
    }
]

# Social networks configuration - Secondary networks (bottom priority)
SOCIAL_NETWORKS_SECONDARY = [
    {
        'name': 'Telegram',
        'field': 'telegram',
        'icon': 'fab fa-telegram',
        'color': '#0088CC',
        'base_url': 'https://t.me/',
        'priority': 2
    },
    {
        'name': 'GitHub',
        'field': 'github',
        'icon': 'fab fa-github',
        'color': '#181717',
        'base_url': 'https://github.com/',
        'priority': 2
    },
    {
        'name': 'Behance',
        'field': 'behance',
        'icon': 'fab fa-behance',
        'color': '#1769FF',
        'base_url': 'https://behance.net/',
        'priority': 2
    },
    {
        'name': 'Dribbble',
        'field': 'dribbble',
        'icon': 'fab fa-dribbble',
        'color': '#EA4C89',
        'base_url': 'https://dribbble.com/',
        'priority': 2
    },
    {
        'name': 'Pinterest',
        'field': 'pinterest',
        'icon': 'fab fa-pinterest',
        'color': '#BD081C',
        'base_url': 'https://pinterest.com/',
        'priority': 2
    },
    {
        'name': 'Sitio Web',
        'field': 'website',
        'icon': 'fas fa-globe',
        'color': '#6B7280',
        'base_url': '',
        'priority': 2
    }
]

# Combined social networks for backward compatibility
SOCIAL_NETWORKS = SOCIAL_NETWORKS_PRIMARY + SOCIAL_NETWORKS_SECONDARY
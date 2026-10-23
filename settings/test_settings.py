from .settings import *
from random import choice
from string import ascii_lowercase
from os import makedirs

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(TMP_ROOT, ''.join(choice(ascii_lowercase) for _ in range(10)))
makedirs(MEDIA_ROOT, exist_ok=True)

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'api/tests/fixtures'),
)


CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'shared': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'shared', 'TIMEOUT': None},
}

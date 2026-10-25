from .web import generate_web
from .android import generate_android
from .ios import generate_ios
from .cli import generate_cli

BACKENDS = {"web": generate_web, "android": generate_android, "ios": generate_ios, "cli": generate_cli}

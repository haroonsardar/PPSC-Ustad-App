[app]
title = PPSC Ustad
package.name = ppscustad
package.domain = org.haroon
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,json
version = 0.1
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,android

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Icon and Presplash (Ensure logo.png is in assets folder)
icon.filename = %(source.dir)s/assets/logo.png
presplash.filename = %(source.dir)s/assets/logo.png

# Android Specifics
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
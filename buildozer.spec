[app]
title = Cyber Dash Legends
package.name = cyberdash
package.domain = org.game
source.dir = .
source.include_exts = py,wav,png,json
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 1
android.permissions =
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

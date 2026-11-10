
[app]

title = Subway Surfers
package.name = subwaysurfers
package.domain = org.example

version = 1.0.0

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,wav,mp3,ogg,json
source.exclude_dirs = tests,bin,.git,.github

requirements = python3,kivy

orientation = portrait
fullscreen = 1

android.permissions = INTERNET
android.minapi = 23
android.api = 35
android.archs = arm64-v8a

android.accept_sdk_license = True

p4a.bootstrap = sdl2

android.numeric_version = 1
android.allow_backup = False

log_level = 2

[buildozer]

log_level = 2
warn_on_root = 1

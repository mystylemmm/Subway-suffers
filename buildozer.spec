
[app]

# Application title
title = Subway Surfers

# Package information
package.name = subwaysurfers
package.domain = org.example

# Application version
version = 1.0.0

# Source code directory
source.dir = .

# Included files
source.include_exts = py,png,jpg,jpeg,kv,atlas,wav,mp3,ogg,json

# Excluded directories
source.exclude_dirs = tests,bin,.git,.github

# Application requirements
requirements = python3,kivy

# Screen orientation
orientation = portrait

# Fullscreen
fullscreen = 1

# Android permissions
android.permissions = INTERNET

# Android configuration
android.minapi = 23
android.archs = arm64-v8a

# Android application name
android.entrypoint = org.kivy.android.PythonActivity

# Build settings
p4a.bootstrap = sdl2

# Version information
android.numeric_version = 1

# Logging
log_level = 2

# Android backup
android.allow_backup = False

# iOS settings
ios.codesign.allowed = false

[buildozer]

# Build directory
log_level = 2

# Warnings
warn_on_root = 1

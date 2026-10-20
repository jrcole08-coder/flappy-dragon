[app]
title = Flappy Dragon
package.name = flappydragon
package.domain = org.dragon
source.dir = .
source.include_exts = py
version = 0.1
requirements = hostpython3==3.10.14,python3==3.10.14,pygame
orientation = landscape
fullscreen = 1
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

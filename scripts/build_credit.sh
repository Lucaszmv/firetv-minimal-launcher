#!/usr/bin/env bash
export ANDROID_HOME="C:/Users/Usuario/AppData/Local/android-sdk"
export JAVA_HOME="C:/Program Files/Microsoft/jdk-21.0.12.101-hotspot"
cd "$(dirname "$0")/../free-my-tv" || exit 1
bash build.sh && "$ANDROID_HOME/build-tools/34.0.0/apksigner.bat" verify --print-certs FreeMyTV.apk && echo CREDIT_BUILD_OK

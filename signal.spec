Name:		signal-desktop
Version:	5.0.0
Release:	1%{?dist}
Summary:	Private messaging from your desktop
License:	GPLv3
URL:		https://github.com/signalapp/Signal-Desktop/

#			https://updates.signal.org/desktop/apt/pool/main/s/signal-desktop/signal-desktop_1.3.0_amd64.deb
Source0:	https://github.com/signalapp/Signal-Desktop/archive/v%{version}.tar.gz
Source1:	https://github.com/atom/node-spellchecker/archive/613ff91dd2d9a5ee0e86be8a3682beecc4e94887.tar.gz

#ExclusiveArch:	x86_64
BuildRequires: binutils, git, python2, gcc, gcc-c++, yarn, openssl-devel, bsdtar, jq, zlib, xz
BuildRequires: nodejs, ca-certificates, xz, git-lfs
%if 0%{?fedora} > 28
BuildRequires: python-unversioned-command
%endif
%if 0%{?fedora} > 29
BuildRequires: libxcrypt-compat
%endif
%if 0%{?fedora} > 31
BuildRequires: libxcrypt-compat, vips-devel
%endif
%if 0%{?el8}
BuildRequires: platform-python-devel, python3
%endif

AutoReqProv: no
#AutoProv: no
Provides: signal-desktop
Requires: GConf2, libnotify, libappindicator-gtk3, libXtst, nss, libXScrnSaver

%global __requires_exclude_from ^/%{_libdir}/%{name}/release/.*$
%define _build_id_links none


%description
Private messaging from your desktop

%prep
# prepare zkgroup lib
#tar xfz %{S:2}

rm -rf Signal-Desktop-%{version}
tar xfz %{S:0}

pwd

# allow node 10
# sed -i 's/"node": "^8.9.3"/"node": ">=8.9.3"/' package.json

# + avoid using fedora's node-gyp
#yarn --no-default-rc add --dev node-gyp

cd Signal-Desktop-%{version}

node --version

# Set system Electron version for ABI compatibility
#sed -r 's#("electron": ").*"#\16.1.4"#' -i package.json

# Allow higher Node versions
sed 's#"node": "#&>=#' -i package.json

# Fix spellchecker for Fedora-based distributions
# TODO: unsure if still needed after signal 1.33.0
#sed -r 's#("spellchecker": ").*"#\1file:../../SOURCES/613ff91dd2d9a5ee0e86be8a3682beecc4e94887.tar.gz"#' -i package.json
#sed -r 's!/usr/share/hunspell!/usr/share/myspell!' -i js/spell_check.js

# avoid building deb/appimage packages, since we're repacking the unpacked sources
# this also solves build failure on epel 7 due to a too outdated 'tar' command when building the .deb file
patch --no-backup-if-mismatch -Np1 << 'EOF'
--- a/package.json
+++ b/package.json
284,330d283
<     "mac": {
<       "asarUnpack": [
<         "**/*.node",
<         "node_modules/zkgroup/libzkgroup.*",
<         "node_modules/libsignal-client/build/*.node"
<       ],
<       "artifactName": "${name}-mac-${version}.${ext}",
<       "category": "public.app-category.social-networking",
<       "darkModeSupport": true,
<       "hardenedRuntime": true,
<       "entitlements": "./build/entitlements.mac.plist",
<       "icon": "build/icons/mac/icon.icns",
<       "publish": [
<         {
<           "provider": "generic",
<           "url": "https://updates.signal.org/desktop"
<         }
<       ],
<       "target": [
<         "zip",
<         "dmg"
<       ],
<       "bundleVersion": "1"
<     },
<     "win": {
<       "asarUnpack": [
<         "**/*.node",
<         "node_modules/spellchecker/vendor/hunspell_dictionaries",
<         "node_modules/sharp",
<         "node_modules/zkgroup/libzkgroup.*",
<         "node_modules/libsignal-client/build/*.node"
<       ],
<       "artifactName": "${name}-win-${version}.${ext}",
<       "certificateSubjectName": "Signal (Quiet Riddle Ventures, LLC)",
<       "certificateSha1": "77B2AA4421E5F377454B8B91E573746592D1543D",
<       "publisherName": "Signal (Quiet Riddle Ventures, LLC)",
<       "icon": "build/icons/win/icon.ico",
<       "publish": [
<         {
<           "provider": "generic",
<           "url": "https://updates.signal.org/desktop"
<         }
<       ],
<       "target": [
<         "nsis"
<       ]
<     },
346,348d298
<       "target": [
<         "deb"
<       ],
350,358d299
<     },
<     "deb": {
<       "depends": [
<         "libnotify4",
<         "libxtst6",
<         "libnss3",
<         "libasound2",
<         "libxss1"
<       ]
EOF

# fsevents for Apple MacOS also breaks linux build
patch --no-backup-if-mismatch -Np1 << 'EOF'
--- a/yarn.lock
+++ b/yarn.lock
4901,4902d4900
<   optionalDependencies:
<     fsevents "^1.2.7"
8005,8012d8002
< 
< fsevents@^1.2.2, fsevents@^1.2.7:
<   version "1.2.9"
<   resolved "https://registry.yarnpkg.com/fsevents/-/fsevents-1.2.9.tgz#3f5ed66583ccd6f400b5a00db6f7e861363e388f"
<   integrity sha512-oeyj2H3EjjonWcFjD5NvZNE9Rqe4UW+nQBU2HNeKw0koVLEFIhtyETyAakeAM3de7Z/SW5kcA+fZUait9EApnw==
<   dependencies:
<     nan "^2.12.1"
<     node-pre-gyp "^0.12.0"
EOF

# fix sqlcipher generic python invocation, incompatible with el8 
%if 0%{?el8}
#yarn install || true
#sed -i 's/python/python3/g' node_modules/@journeyapps/sqlcipher/deps/sqlite3.gyp
mkdir -p ${HOME}/.bin
ln -s %{__python3} ${HOME}/.bin/python
export PATH="${HOME}/.bin:${PATH}"
%endif

yarn install

%build

pwd

cd %{_builddir}/Signal-Desktop-%{version} 

# use dynamic linking
patch --no-backup-if-mismatch -Np1 << 'EOF'
--- a/node_modules/@journeyapps/sqlcipher/deps/sqlite3.gyp	2019-10-27 01:53:29.860275405 -0400
+++ b/node_modules/@journeyapps/sqlcipher/deps/sqlite3.gyp	2019-10-27 01:51:32.001730882 -0400
@@ -73,7 +73,7 @@
         'link_settings': {
           'libraries': [
             # This statically links libcrypto, whereas -lcrypto would dynamically link it
-            '<(SHARED_INTERMEDIATE_DIR)/sqlcipher-amalgamation-<@(sqlite_version)/OpenSSL-Linux/libcrypto.a'
+            '-lcrypto'
           ]
         }
       }]
@@ -141,7 +141,6 @@
         { # linux
           'include_dirs': [
             '<(SHARED_INTERMEDIATE_DIR)/sqlcipher-amalgamation-<@(sqlite_version)/',
-            '<(SHARED_INTERMEDIATE_DIR)/sqlcipher-amalgamation-<@(sqlite_version)/openssl-include/'
           ]
         }]
       ],
EOF


# We can't read the release date from git so we use SOURCE_DATE_EPOCH instead
patch --no-backup-if-mismatch -Np1 << 'EOF'
--- a/Gruntfile.js
+++ b/Gruntfile.js
@@ -203,9 +203,7 @@ module.exports = grunt => {
   });
 
   grunt.registerTask('getExpireTime', () => {
-    grunt.task.requires('gitinfo');
-    const gitinfo = grunt.config.get('gitinfo');
-    const committed = gitinfo.local.branch.current.lastCommitTime;
+    const committed = parseInt(process.env.SOURCE_DATE_EPOCH, 10) * 1000;
     const time = Date.parse(committed) + 1000 * 60 * 60 * 24 * 90;
     grunt.file.write(
       'config/local-production.json',
EOF

# Gruntfile expects Git commit information which we don't have in a tarball download
# See https://github.com/signalapp/Signal-Desktop/issues/2376
yarn generate exec:build-protobuf exec:transpile concat copy:deps sass

#env SIGNAL_ENV=production yarn --no-default-rc --verbose build-release --linux rpm
yarn build-release

%install

# Electron directory of the final build depends on the arch
%ifnarch x86_64
    %global PACKDIR linux-ia32-unpacked
%else
    %global PACKDIR linux-unpacked
%endif


# copy base files
install -dm755 %{buildroot}/%{_libdir}/%{name}
cp -a %{_builddir}/Signal-Desktop-%{version}/release/linux-unpacked/* %{buildroot}/%{_libdir}/%{name}

# delete uneeded build files
# this also would make signal-desktop package provide the wrong library .so files
#find %{buildroot}/%{_libdir}/%{name}/resources/ -iname '*.so*' -delete -print

# try to slim down install base. TODO: this breaks voice message player
#rm -rf %{buildroot}/%{_libdir}/%{name}/chrome_*.pak 
#rm -rf %{buildroot}/%{_libdir}/%{name}/chrome-sandbox
#rm -rf %{buildroot}/%{_libdir}/%{name}/swiftshader


install -dm755 %{buildroot}%{_bindir}
ln -s %{_libdir}/%{name}/signal-desktop %{buildroot}%{_bindir}/signal-desktop

install -dm755 %{buildroot}%{_datadir}/applications/
# Changes from upstream:
# 1. Run signal WITH sandbox since it looks like there's no problems with fedora and friends
# 2. Use tray icon by default
# 3. Small fix for tray for Plasma users
cat << EOF > %{buildroot}%{_datadir}/applications/signal-desktop.desktop
[Desktop Entry]
Name=Signal
Exec=/usr/bin/signal-desktop --use-tray-icon %U
Terminal=false
Type=Application
Icon=signal-desktop
StartupWMClass=Signal
Comment=Private messaging from your desktop
MimeType=x-scheme-handler/sgnl;
Categories=Network;InstantMessaging;Chat;
EOF

for i in 16 24 32 48 64 128 256 512 1024; do
    install -dm755 %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/
    install -Dm 644 %{_builddir}/Signal-Desktop-%{version}/build/icons/png/${i}x${i}.png %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/%{name}.png
done


%files
%defattr(-,root,root)
%{_bindir}/*
%{_libdir}/*
%{_datadir}/*
 

%changelog
* Thu Feb 18 2021 Guilherme Cardoso <gjc@ua.pt> 1.40.0-1
- BuildRequires git-lfs due to node-sqlcipher
- Update patches

* Fri Sep 25 2020 Guilherme Cardoso <gjc@ua.pt> 1.36.2-1
- Patch to remove fsevents from build, since it make build failing
in linux environments and is only needed for Apple MacOS users

* Mon Jul 27 2020 Guilherme Cardoso <gjc@ua.pt> 1.34.4-3
- Replaced 'requires' 'libappindicator' with 'libappindicator-gtk3'

* Sun Jun 21 2020 Guilherme Cardoso <gjc@ua.pt> 1.34.2-2
- Re-order %build and %prep steps
- Also manually build zkgroup nodemodule shared object on el7

* Tue Apr 28 2020 Guilherme Cardoso <gjc@ua.pt> 1.33.4-1
- Added workarounds for el8 copr build

* Tue Apr 7 2020 Guilherme Cardoso <gjc@ua.pt> 1.33.0-1
- Reordered patching and build flow
- Removed spellchecker directory patch for fedora 

* Sat Mar 14 2020 Guilherme Cardoso <gjc@ua.pt> 1.32.1-2
- Don't try to override XDG_CURRENT_DESKTOP anymore 

* Sat Feb 08 2020 Guilherme Cardoso <gjc@ua.pt> 1.30.1-3
- Fix spellchecker and audio player. Huge thank you to Christoph Schwille

* Fri Jan 24 2020 Guilherme Cardoso <gjc@ua.pt> 1.30.0-1
- Refactor spec file, since Signal no longer builds rpm file
- Fix package providing and requiring a lot of libraries
- Slimmed down instalation by deleting some build files present on release

* Mon Jan 20 2020 Guilherme Cardoso <gjc@ua.pt> 1.29.6-1
- Resync patches and build recipe from archlinux
- RPM spec build dependencies cleanup (ZaWertun)

* Thu Nov 14 2019 Guilherme Cardoso <gjc@ua.pt> 1.28.0-1
- Simplify changelog to include only major changes

* Fri Sep 6 2019 Guilherme Cardoso <gjc@ua.pt> 1.27.1-1
- Version bump
- Small adjustments to rpm spec file and its patches

* Sat Mar 30 2019 Guilherme Cardoso <gjc@ua.pt> 1.23.2-1
- Updated to dynamic eletron version, idea taken from
ArchLinux AUR Signal package (_installed_electron_version)

* Thu Jan 17 2019 Guilherme Cardoso <gjc@ua.pt> 1.20.0-2
- Version bump
- Updated patches from archlinux aur build
- Add depndencies for Fedora rawhide

* Wed Oct 31 2018 Guilherme Cardoso <gjc@ua.pt> 1.17.2-1
- Version bump
- Explicit nodejs dependency, which tries to solve the requirement of having nodejs LTS version 8
- Thanks clime for the help

* Mon Oct 22 2018 Guilherme Cardoso <gjc@ua.pt> 1.16.3-4
- Fix wrong this rpmspec version info

* Mon Oct 15 2018 Guilherme Cardoso <gjc@ua.pt> 1.16.2-3
- Workaround for KDE plasma Signal's tray icon
https://github.com/signalapp/Signal-Desktop/issues/1876

* Fri Oct 12 2018 Guilherme Cardoso <gjc@ua.pt> 1.16.2-2
- Patch to use tray icon

* Fri Aug 17 2018 Guilherme Cardoso <gjc@ua.pt> 1.15.5-2
- Try to patch to allow higher node versions for Fedora Rawhide
- Manual symlink

* Thu Aug 16 2018 Matthias Andree <mandree@FreeBSD.org> 1.15.5-1
- Shuffle things around a bit
- Add jq to build requisites
- tweak files section so it actually finds its inputs
- add node-gyp to developer dependencies only
- add -no-default-rc to yarn calls throughout

* Tue Aug 14 2018 Guilherme Cardoso <gjc@ua.pt> 1.15.4-1
- Version bump
- Build fixes arround embebed OpenSSL's from mandree and stemid
Link: https://github.com/signalapp/Signal-Desktop/issues/2634

* Wed May 02 2018 Guilherme Cardoso <gjc@ua.pt> 1.9.0-1
- Version bump
- Spec file cleanup

* Mon Apr 16 2018 Guilherme Cardoso <gjc@ua.pt> 1.7.1-4
- Added a few more yarn steps (check, lint)

* Mon Apr 16 2018 Guilherme Cardoso <gjc@ua.pt> 1.7.1-3
- Fix build. Requires 'yarn transpile'. Thanks spacekookie.
Ref: https://github.com/signalapp/Signal-Desktop/issues/2256

* Sat Apr 14 2018 Guilherme Cardoso <gjc@ua.pt> 1.7.1-2
- Remove patch lowering nodejs due to async problems
- Simplified BuildRequires

* Wed Apr 11 2018 Guilherme Cardoso <gjc@ua.pt> 1.6.1-2
- Fix desktop shortcut (thanks to bol for reporting)

* Tue Mar 13 2018 Guilherme Cardoso <gjc@ua.pt> 1.6.0-1
- Version bump
- Update project homepage url
- Patch to override nodejs version of Signal's sources

* Sun Feb 18 2018 Guilherme Cardoso <gjc@ua.pt> 1.3.0-2
- Build from sources instead of unpacking .deb release

* Mon Feb 05 2018 Guilherme Cardoso <gjc@ua.pt> 1.3.0-1
- Version bump
- Added missing dependencies from original deb package

* Thu Nov 02 2017 Richard Monk <richardmonk@gmail.com> 1.0.35-1
- Initial Packaging

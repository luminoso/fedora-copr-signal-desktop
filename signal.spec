Name:		signal-desktop
Version:	5.56.0
Release:	1%{?dist}
Summary:	Private messaging from your desktop
License:	GPLv3
URL:		https://github.com/signalapp/Signal-Desktop/

#			https://updates.signal.org/desktop/apt/pool/main/s/signal-desktop/signal-desktop_1.3.0_amd64.deb
Source0:	https://github.com/signalapp/Signal-Desktop/archive/v%{version}.tar.gz
Source1:	%{name}.desktop
#Patch0:    signal-desktop-better-sqlite3-openssl.patch
Patch1:     signal-desktop-expire-from-source-date-epoch.patch

#ExclusiveArch:	x86_64
BuildRequires: binutils, git, python2, gcc, gcc-c++, yarn, bsdtar, jq, zlib, xz
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
Requires: libnotify, libXtst, nss

%if 0%{?suse_version:1}
Requires: libvips42
%else
Requires: vips
%endif

%global __requires_exclude_from ^/%{_libdir}/%{name}/release/.*$
%define _build_id_links none

%if 0%{?fedora}
%global debug_package %{nil}
%endif

%description
Signal Desktop is an Electron application that links with your Signal Android
or Signal iOS app.

%prep
# https://bugzilla.redhat.com/show_bug.cgi?id=1793722
export SOURCE_DATE_EPOCH="$(date +"%s")"

# fix sqlcipher generic python invocation, incompatible with el8 
%if 0%{?el8}
#yarn install || true
#sed -i 's/python/python3/g' node_modules/@journeyapps/sqlcipher/deps/sqlite3.gyp
mkdir -p ${HOME}/.bin
ln -s %{__python3} ${HOME}/.bin/python
export PATH="${HOME}/.bin:${PATH}"
%endif

# git-lfs hook needs to be installed for one of the dependencies
git lfs install

node --version

rm -rf Signal-Desktop-%{version}
tar xfz %{S:0}
pwd

cd Signal-Desktop-%{version}

# Allow higher Node versions
sed 's#"node": "#&>=#' -i package.json

# Disable building deb package
patch -p0 << EOF
--- package.json	2022-08-24 21:15:13.597420398 +0100
+++ package.json	2022-08-25 09:01:22.424884862 +0100
@@ -385,7 +385,6 @@
         "StartupWMClass": "Signal"
       },
       "target": [
-        "deb"
       ],
       "icon": "build/icons/png"
     },
EOF

# Allow higher electron versions
#sed 's/"electron": "13.3.0"/"electron": "~14.1.1"/' -i package.json
#sed 's#"electron-builder": "#&~#' -i package.json
#sed 's#"electron-mocha": "#&~#' -i package.json
#sed 's#"electron-notarize": "#&~#' -i package.json
#sed 's#"@electron/fuses": "#&~#' -i package.json

# patch better-sqlite3 to encapsulate sqlcipher
# https://bugs.archlinux.org/task/69980
#grep -q 32828e03be0489572ab334239c5768c86697989 package.json
#sed 's|https://github\.com/signalapp/better-sqlite3#32828e03be0489572ab334239c5768c86697989|https://github.com/signalapp/better-sqlite3#917a6f5cf8b84d5ef4b8fe6dc0f4b8f59ca45bea|' -i package.json


# We can't read the release date from git so we use SOURCE_DATE_EPOCH instead
%patch1 -p1

npm config set python /usr/bin/python2
yarn install --ignore-engines

%build
# https://bugzilla.redhat.com/show_bug.cgi?id=1793722
export SOURCE_DATE_EPOCH="$(date +"%s")"
echo $SOURCE_DATE_EPOCH

pwd
date

cd %{_builddir}/Signal-Desktop-%{version} 
yarn generate
yarn build


%install

pwd
cd Signal-Desktop-%{version}
ls

install -d -m 0755 %{buildroot}%{_libdir}/%{name}

# Remove unneeded files
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/sharp/{docs,src,vendor}
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/sharp/node_modules/node-addon-api/
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/ringrtc/build/{darwin,win32}
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/ffi-napi/prebuilds/{darwin-x64,linux-arm64,win32-ia32,win32-x64}
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/ffi-napi/node_modules/ref-napi/prebuilds/{darwin-x64,linux-arm64,win32-ia32,win32-x64}
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/ref-napi/prebuilds/{darwin-x64,linux-arm64,win32-ia32,win32-x64}
rm -rf release/linux-unpacked/resources/app.asar.unpacked/node_modules/@signalapp/signal-client/prebuilds/{darwin-x64,win32-x64}

# correct mod
find release/linux-unpacked -type d | xargs chmod 755
find release/linux-unpacked -type f | xargs chmod 644
chmod +x release/linux-unpacked/signal-desktop

# Copy all required files
cp -r release/linux-unpacked/* %{buildroot}%{_libdir}/%{name}

install -d -m 0755 %{buildroot}%{_bindir}

cat << EOF > %{buildroot}%{_bindir}/signal-desktop
#!/bin/sh
exec %{_libdir}/%{name}/signal-desktop "\$@"
EOF
chmod +x %{buildroot}%{_bindir}/signal-desktop

# desktop file
# Changes from upstream:
# 1. Run signal WITH sandbox since it looks like there's no problems with fedora and friends
# 2. Use tray icon by default
# 3. Small fix for tray for Plasma users
install -d -m 0755 %{buildroot}%{_datadir}/applications/
install -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop

#%if 0%{?suse_version}
#%suse_update_desktop_file %{name}
#%endif

# icons
for i in 16 24 32 48 64 128 256 512; do
    install -d -m 0755 %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/
    install -m 0644 build/icons/png/${i}x${i}.png %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/%{name}.png
done

#%fdupes %{buildroot}%{_libdir}/%{name}

%files
%defattr(-,root,root)
#%doc ACKNOWLEDGMENTS.md CONTRIBUTING.md README.md
#%license LICENSE
%{_bindir}/%{name}

%dir %{_libdir}/%{name}

%{_libdir}/%{name}

%{_datadir}/icons/hicolor/

%dir %{_datadir}/applications/
%{_datadir}/applications/%{name}.desktop
 

%changelog
* Thu Aug 25 2022 Guilherme Cardoso <gjc@ua.pt> 5.56.0-1
- Avoid building .deb package

* Sun Feb 6 2022 Guilherme Cardoso <gjc@ua.pt> 5.30.0-1
- Remove libappindicator-gtk3, libXScrnSaver dependencies

* Sat Jan 29 2022 Guilherme Cardoso <gjc@ua.pt> 5.19.1-3
- Follow upstream and remove GConf2 dependency 

* Wed Jan 26 2022 Guilherme Cardoso <gjc@ua.pt> 5.29.1-2
- Add Workaround for SOURCE_DATE_EPOCH sourcing from date, due to rpm macros

* Thu Oct 28 2021 Guilherme Cardoso <gjc@ua.pt> 5.22.0-1
- Disabled better-sqlite patches

* Sun Oct 24 2021 Guilherme Cardoso <gjc@ua.pt> 5.20.0-2
- Added "--disable-seccomp-filter-sandbox" due to an older electron version crash on newer systems
https://github.com/luminoso/fedora-copr-signal-desktop/issues/12

* Sun Aug 29 2021 Guilherme Cardoso <gjc@ua.pt> 5.15.0-1
- Start to sync rpm spec file with https://build.opensuse.org/project/show/network:im:signal
- Sync patches with latest ArchLinux ones
- Move patches out of spec file

* Wed May 12 2021 Guilherme Cardoso <gjc@ua.pt> 5.1.0-1
- Remove openssl dynamic link patches
- Remove bundled binaries for other platforms

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

Name:		signal-desktop
Version:	99.0.0
Release:	1%{?dist}
Summary:	Private messaging from your desktop
License:	GPLv3
URL:		https://github.com/signalapp/Signal-Desktop/
Source0:	luminoso-copr-signal-deprecation-notice
Source1:	%{name}.desktop

AutoReqProv: no
Provides: signal-desktop

%if 0%{?fedora}
%global debug_package %{nil}
%endif


%description
Signal Desktop is an Electron application that links with your Signal Android
or Signal iOS app.

%prep


%build


%install

# install deprecation warning

install -d -m 0755 %{buildroot}%{_bindir}
install -m 0644 %{SOURCE0} %{buildroot}%{_bindir}/%{name}
chmod +x %{buildroot}%{_bindir}/signal-desktop

# keep desktop icon
install -d -m 0755 %{buildroot}%{_datadir}/applications/
install -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop


%files

%defattr(-,root,root)

%{_bindir}/%{name}
%dir %{_datadir}/applications/
%{_datadir}/applications/%{name}.desktop
 

%changelog
* Wed Nov 16 2022 Guilherme Cardoso <gjc@ua.pt> 99.0.0-1
- Update deprecation notice

* Fri Jun 10 2022 Guilherme Cardoso <gjc@ua.pt> 5.30.0-1
- Special mock release to deprecate Signal-desktop copr

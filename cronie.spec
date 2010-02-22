# TODO
# - update paths in manuals (create .in files and send upstream)
# - make /etc/pam.d independant of sysconfdir (configure-able option and send upstream)
#
# Conditional build:
%bcond_without	inotify		# without inotify support
%if "%{pld_release}" == "ac"
%bcond_with		selinux		# without SELinux support
%bcond_with		audit		# without audit support
%else
%bcond_without	selinux		# without SELinux support
%bcond_without	audit		# without audit support
%endif

Summary:	Cron daemon for executing programs at set times
Name:		cronie
Version:	1.4.4
Release:	1
License:	MIT and BSD and GPL v2
Group:		Daemons
Source0:	https://fedorahosted.org/releases/c/r/cronie/%{name}-%{version}.tar.gz
# Source0-md5:	eb9834c5f87cca9efeed68e6fed3fe3d
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
Patch0:		inotify-nosys.patch
Patch1:		%{name}-nosyscrontab.patch
Patch2:		sendmail-path.patch
URL:		https://fedorahosted.org/cronie/
%{?with_audit:BuildRequires:	audit-libs-devel}
BuildRequires:	autoconf
BuildRequires:	automake
%{?with_selinux:BuildRequires:	libselinux-devel}
BuildRequires:	pam-devel
BuildRequires:	rpm >= 4.4.9-56
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires:	/bin/run-parts
Requires:	/sbin/chkconfig
Requires:	psmisc >= 20.1
Requires:	rc-scripts >= 0.4.0.19
%{?with_inotify:Requires:	uname(release) >= 2.6.13}
Provides:	crondaemon
Provides:	crontabs = 1.7
Provides:	group(crontab)
%if "%{pld_release}" == "th"
Provides:	vixie-cron = 4:4.4
%endif
Obsoletes:	crondaemon
Obsoletes:	crontabs
%if "%{pld_release}" == "th"
Obsoletes:	vixie-cron <= 4:4.3
%endif
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Cronie contains the standard UNIX daemon crond that runs specified
programs at scheduled times and related tools. It is based on the
original cron and has security and configuration enhancements like the
ability to use pam and SELinux.

%package anacron
Summary:	Utility for running regular jobs
Group:		Base
Provides:	anacron = 2.4
Obsoletes:	anacron <= 2.3

%description anacron
Anacron becames part of cronie. Anacron is used only for running
regular jobs. The default settings execute regular jobs by anacron,
however this could be overloaded in settings.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1

%build
%{__aclocal}
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	SYSCRONTAB=/etc/crontab \
	SYS_CROND_DIR=/etc/cron.d \
	--sysconfdir=/etc/cron \
	--with-pam \
	--with%{!?with_selinux:out}-selinux \
	--with%{!?with_audit:out}-audit \
	--with%{!?with_inotify:out}-inotify \
	--enable-anacron

%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/{ana,}cron},%{_mandir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install \
	pamdir=/etc/pam.d \
	DESTDIR=$RPM_BUILD_ROOT

install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
cp -a contrib/0anacron $RPM_BUILD_ROOT/etc/cron.hourly/0anacron
cp -a %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
cp -a %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
cp -a %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
cp -a %{SOURCE5} $RPM_BUILD_ROOT/etc/pam.d/crond

touch $RPM_BUILD_ROOT/var/log/cron

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.allow << 'EOF'
# cron.allow	This file describes the names of the users which are
#		allowed to use the local cron daemon
root
EOF

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.deny << 'EOF'
# cron.deny	This file describes the names of the users which are
#		NOT allowed to use the local cron daemon
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 117 -r -f crontab

%post
if [ ! -f /var/log/cron ]; then
	umask 027
	touch /var/log/cron
	chgrp crontab /var/log/cron
	chmod 660 /var/log/cron
fi
/sbin/chkconfig --add crond
%service crond restart "Cron Daemon"

%preun
if [ "$1" = "0" ]; then
	%service crond stop
	/sbin/chkconfig --del crond
fi

%postun
if [ "$1" = "0" ]; then
	%groupremove crontab
fi

%triggerun -- hc-cron,fcron,vixie-cron
# Prevent preun from crond from working
chmod a-x /etc/rc.d/init.d/crond

%triggerpostun -- hc-cron,fcron,vixie-cron
# Restore what triggerun removed
chmod 754 /etc/rc.d/init.d/crond
# reinstall crond init.d links, which could be different
/sbin/chkconfig --del crond
/sbin/chkconfig --add crond

%files
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog README
%attr(750,root,crontab) %dir %{_sysconfdir}/cron*
%attr(640,root,crontab) %config(noreplace,missingok) /etc/cron.d/crontab
%attr(640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.allow
%attr(640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.deny
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/cron
%config(noreplace) %verify(not md5 mtime size) /etc/pam.d/crond
%attr(754,root,root) /etc/rc.d/init.d/crond
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/cron
%attr(755,root,root) %{_sbindir}/crond
%attr(2755,root,crontab) %{_bindir}/crontab

%{_mandir}/man8/crond.8*
%{_mandir}/man8/cron.8*
%{_mandir}/man5/crontab.5*
%{_mandir}/man1/crontab.1*

%attr(1730,root,crontab) /var/spool/cron
%attr(660,root,crontab) %ghost /var/log/cron

%files anacron
%defattr(644,root,root,755)
%attr(755,root,root) %{_sbindir}/anacron
%attr(755,root,root) %{_sysconfdir}/cron.hourly/0anacron
%{_mandir}/man5/anacrontab.5*
%{_mandir}/man8/anacron.8*

%attr(1730,root,crontab) /var/spool/anacron

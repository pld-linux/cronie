# TODO
# - update paths in manuals (create .in files and send upstream)
# - make /etc/pam.d independant of sysconfdir (configure-able option and send upstream)
# - syslog output (-s) writes two bytes of garbage to syslog instead of actual data:
#   Mar  3 09:30:01 ravenous CROND[2528]: 4ÿ
#
# Conditional build:
%bcond_without	inotify		# without inotify support
%if "%{pld_release}" == "ac"
%bcond_with		selinux		# with SELinux support
%bcond_with		audit		# with audit support
%else
%bcond_without	selinux		# without SELinux support
%bcond_without	audit		# without audit support
%endif

Summary:	Cron daemon for executing programs at set times
Name:		cronie
Version:	1.4.11
Release:	3
License:	MIT and BSD and GPL v2
Group:		Daemons
Source0:	https://fedorahosted.org/releases/c/r/cronie/%{name}-%{version}.tar.gz
# Source0-md5:	2ba645cf54de17f138ef70312843862f
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
Source6:	%{name}.upstart
Source7:	crond.service
Patch0:		inotify-nosys.patch
Patch1:		sendmail-path.patch
URL:		https://fedorahosted.org/cronie/
%{?with_audit:BuildRequires:	audit-libs-devel}
BuildRequires:	autoconf
BuildRequires:	automake
%{?with_selinux:BuildRequires:	libselinux-devel}
BuildRequires:	pam-devel
BuildRequires:	rpm >= 4.4.9-56
BuildRequires:	rpmbuild(macros) >= 1.647
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires:	/bin/run-parts
Requires:	psmisc >= 20.1
Requires:	rc-scripts >= 0.4.3.0
%if "%{pld_release}" != "ac"
Requires(post,preun,postun):	systemd-units >= 38
Requires:	systemd-units >= 38}
%endif
%{?with_inotify:Requires:	uname(release) >= 2.6.13}
Provides:	crondaemon
Provides:	crontabs = 1.7
Provides:	group(crontab)
%if "%{pld_release}" == "th"
Provides:	vixie-cron = 4.3-1
%endif
Obsoletes:	crondaemon
Obsoletes:	cronie-systemd
Obsoletes:	crontabs
%if "%{pld_release}" == "th"
Obsoletes:	vixie-cron < 4.3-1
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

%package upstart
Summary:	Upstart job description for Cronie
Summary(pl.UTF-8):	Opis zadania Upstart dla Cronie
Group:		Daemons
Requires:	%{name} = %{version}-%{release}
Requires:	upstart >= 0.6

%description upstart
Upstart job description for Cronie.

%description upstart -l pl.UTF-8
Opis zadania Upstart dla Cronie.

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
%{__aclocal}
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	SYSCRONTAB=/etc/crontab \
	SYS_CROND_DIR=/etc/cron.d \
	--sysconfdir=/etc/cron \
	--with-editor=/bin/vi \
	--with-pam \
	--with%{!?with_selinux:out}-selinux \
	--with%{!?with_audit:out}-audit \
	--with%{!?with_inotify:out}-inotify \
	--disable-syscrontab \
%if "%{cc_version}" >= "3.4"
	--enable-pie \
%endif
	--enable-relro \
	--enable-anacron

%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/{ana,}cron},%{_mandir},%{systemdunitdir}}\
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig,init} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install \
	pamdir=/etc/pam.d \
	DESTDIR=$RPM_BUILD_ROOT

cp -p %{SOURCE5} crond.pam

%if %{without audit}
# remove recording user's login uid to the process attribute
%{__sed} -i -e '/pam_loginuid.so/d' crond.pam
%endif

install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
cp -a contrib/0anacron $RPM_BUILD_ROOT/etc/cron.hourly/0anacron
cp -a %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
cp -a %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
cp -a %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
cp -a crond.pam  $RPM_BUILD_ROOT/etc/pam.d/crond
cp -a %{SOURCE6} $RPM_BUILD_ROOT/etc/init/crond.conf
cp -a %{SOURCE7} $RPM_BUILD_ROOT%{systemdunitdir}/crond.service

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
	install -m 660 -g crontab /dev/null /var/log/cron
fi
/sbin/chkconfig --add crond
%service crond restart "Cron Daemon"
%systemd_post crond.service

%preun
if [ "$1" = "0" ]; then
	%service crond stop
	/sbin/chkconfig --del crond
fi
%systemd_preun crond.service

%postun
if [ "$1" = "0" ]; then
	%groupremove crontab
fi
%systemd_reload

%triggerpostun -- cronie < 1.4.8-13
if [ -f /etc/sysconfig/cron ]; then
	. /etc/sysconfig/cron
	__CROND_ARGS=
	[ "$CROND_SYSLOG_RESULT" = "yes" ] && __CROND_ARGS="-s"
	[ -n "$CROND_MAIL_PROG" ] && __CROND_ARGS="$__CROND_ARGS -m $CROND_MAIL_PROG"
	if [ -n "$__CROND_ARGS" ]; then
		%{__cp} -f /etc/sysconfig/cron{,.rpmsave}
		echo >>/etc/sysconfig/cron
		echo "# Added by rpm trigger" >>/etc/sysconfig/cron
		echo "CROND_ARGS=\"$CROND_ARGS $__CROND_ARGS\"" >>/etc/sysconfig/cron
	fi
fi
%systemd_trigger crond.service

%triggerun -- hc-cron,fcron,vixie-cron < 4.3-1
# Prevent preun from crond from working
chmod a-x /etc/rc.d/init.d/crond

%triggerpostun -- hc-cron,fcron,vixie-cron < 4.3-1
# Restore what triggerun removed
chmod 754 /etc/rc.d/init.d/crond
# reinstall crond init.d links, which could be different
/sbin/chkconfig --del crond
/sbin/chkconfig --add crond

%post upstart
%upstart_post crond

%postun upstart
%upstart_postun crond

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
%{systemdunitdir}/crond.service
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

%if "%{pld_release}" == "th"
%files upstart
%defattr(644,root,root,755)
%config(noreplace) %verify(not md5 mtime size) /etc/init/crond.conf
%endif

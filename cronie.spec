#
# Conditional build:
%bcond_without	selinux		# without SELinux support
#
Summary:	Cron daemon for executing programs at set times
Name:		cronie
Version:	1.4.1
Release:	0.1
License:	MIT and BSD and GPLv2
Group:		Daemons
Source0:	https://fedorahosted.org/cronie/attachment/wiki/WikiStart/%{name}-%{version}.tar.gz?format=raw
# Source0-md5:	9c089d2035b9fa8263bc71da3eb31cdd
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
URL:		https://fedorahosted.org/cronie/
BuildRequires:	audit-libs-devel
%{?with_selinux:BuildRequires:	libselinux-devel}
BuildRequires:	pam-devel
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun):	rc-scripts
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires:	/bin/run-parts
Requires:	/sbin/chkconfig
Requires:	psmisc >= 20.1
Requires:	rc-scripts
Provides:	crondaemon
Provides:	crontabs = 1.7
Provides:	group(crontab)
Provides:	vixie-cron = 4:4.4
Obsoletes:	crondaemon
Obsoletes:	crontabs
Obsoletes:	vixie-cron <= 4:4.3
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

%build
%configure \
	SYSCRONTAB=/etc/cron.d/crontab \
	SYS_CROND_DIR=/etc/cron.d \
	--sysconfdir=/etc/cron.d \
	--with-pam \
	--with%{?!with_selinux:out}-selinux \
	--with-audit \
	--with-inotify \
	--enable-anacron

%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/cron},%{_mandir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

install contrib/0anacron $RPM_BUILD_ROOT/etc/cron.hourly/0anacron

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
install %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
install %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
install %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
install %{SOURCE5} $RPM_BUILD_ROOT/etc/pam.d/crond

for a in fi fr id ja ko pl; do
	if test -f $a/man1/crontab.1; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man1
		install $a/man1/crontab.1 $RPM_BUILD_ROOT%{_mandir}/$a/man1
	fi
	if test -f $a/man5/crontab.5; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man5
		install $a/man5/crontab.5 $RPM_BUILD_ROOT%{_mandir}/$a/man5
	fi
	if test -f $a/man8/cron.8; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man8
		install $a/man8/cron.8 $RPM_BUILD_ROOT%{_mandir}/$a/man8
	fi
done

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
/sbin/chkconfig --add crond
umask 027
touch /var/log/cron
chgrp crontab /var/log/cron
chmod 660 /var/log/cron
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

%triggerpostun -- hc-cron
# reinstall crond init.d links, which could be different
/sbin/chkconfig --del crond
/sbin/chkconfig --add crond

%triggerun -- vixie-cron
# Prevent preun from crond from working
chmod a-x /etc/rc.d/init.d/crond

%triggerpostun -- vixie-cron
# Restore what triggerun removed
chmod 754 /etc/rc.d/init.d/crond
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

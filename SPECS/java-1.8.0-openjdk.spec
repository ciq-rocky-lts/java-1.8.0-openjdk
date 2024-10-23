# To rebuild this RPM, you must first rebuild the portable
# RPM using the java-1.8.0-openjdk-portable.specfile, install
# it and then adjust portablerelease and portablesuffix
# to match the new portable.

# RPM conditionals so as to be able to dynamically produce
# slowdebug/release builds. See:
# http://rpm.org/user_doc/conditional_builds.html
#
# Examples:
#
# Produce release, fastdebug *and* slowdebug builds on x86_64 (default):
# $ rpmbuild -ba java-1.8.0-openjdk.spec
#
# Produce only release builds (no debug builds) on x86_64:
# $ rpmbuild -ba java-1.8.0-openjdk.spec --without slowdebug --without fastdebug
#
# Only produce a release build on x86_64:
# $ rhpkg mockbuild --without slowdebug --without fastdebug
#
# Enable fastdebug builds by default on relevant arches.
%bcond_without fastdebug
# Enable slowdebug builds by default on relevant arches.
%bcond_without slowdebug
# Enable release builds by default on relevant arches.
%bcond_without release
# Remove build artifacts by default
%bcond_with artifacts
# Build a fresh libjvm.so for use in a copy of the bootstrap JDK
%bcond_without fresh_libjvm
# Build with system libraries
%bcond_with system_libs

# Define whether to use the bootstrap JDK directly or with a fresh libjvm.so
%if %{with fresh_libjvm}
%global build_hotspot_first 1
%else
%global build_hotspot_first 0
%endif

%if %{with system_libs}
%global system_libs 1
%global link_type system
%global jpeg_lib |libjavajpeg[.]so.*
%else
%global system_libs 0
%global link_type bundled
%global jpeg_lib |libjpeg[.]so.*
%endif

# The -g flag says to use strip -g instead of full strip on DSOs or EXEs.
# This fixes detailed NMT and other tools which need minimal debug info.
# See: https://bugzilla.redhat.com/show_bug.cgi?id=1520879
%global _find_debuginfo_opts -g

# note: parametrized macros are order-sensitive (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter to other macros. If not macro, then it is considered a switch
# see the difference between global and define:
# See https://github.com/rpm-software-management/rpm/issues/127 to comments at  "pmatilai commented on Aug 18, 2017"
# (initiated in https://bugzilla.redhat.com/show_bug.cgi?id=1482192)
%global debug_suffix_unquoted -slowdebug
%global fastdebug_suffix_unquoted -fastdebug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global fastdebug_suffix "%{fastdebug_suffix_unquoted}"
%global normal_suffix ""

%global debug_warning This package is unoptimised with full debugging. Install only as needed and remove ASAP.
%global fastdebug_warning This package is optimised with full debugging. Install only as needed and remove ASAP.
%global debug_on unoptimised with full debugging on
%global fastdebug_on optimised with full debugging on
%global for_fastdebug for packages with debugging on and optimisation
%global for_debug for packages with debugging on and no optimisation

%if %{with release}
%global include_normal_build 1
%else
%global include_normal_build 0
%endif

%if %{include_normal_build}
%global normal_build %{normal_suffix}
%else
%global normal_build %{nil}
%endif

# We have hardcoded list of files, which  is appearing in alternatives, and in files
# in alternatives those are slaves and master, very often triplicated by man pages
# in files all masters and slaves are ghosted
# the ghosts are here to allow installation via query like `dnf install /usr/bin/java`
# you can list those files, with appropriate sections: cat *.spec | grep -e --install -e --slave -e post_ -e alternatives
# TODO - fix those hardcoded lists via single list
# Those files must *NOT* be ghosted for *slowdebug* packages
# FIXME - if you are moving jshell or jlink or similar, always modify all three sections
# you can check via headless and devels:
#    rpm -ql --noghost java-11-openjdk-headless-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# == rpm -ql           java-11-openjdk-headless-slowdebug-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# != rpm -ql           java-11-openjdk-headless-11.0.1.13-8.fc29.x86_64.rpm  | grep bin
# similarly for other %%{_jvmdir}/{jre,java} and %%{_javadocdir}/{java,java-zip}

# Indicates whether this is the default JDK on this version of RHEL
%global is_system_jdk 1

%global aarch64         aarch64 arm64 armv8
# we need to distinguish between big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
# Set of architectures which support multiple ABIs
%global multilib_arches %{power64} sparc64 x86_64
# Set of architectures for which we build slowdebug builds
%global debug_arches    %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64}
# Set of architectures for which we build fastdebug builds
%global fastdebug_arches x86_64 ppc64le aarch64
# Set of architectures with a Just-In-Time (JIT) compiler
%global jit_arches      %{aarch64} %{ix86} %{power64} sparcv9 sparc64 x86_64
# Set of architectures which use the Zero assembler port (!jit_arches)
%global zero_arches %{arm} ppc s390 s390x
# Set of architectures which run a full bootstrap cycle
%global bootstrap_arches %{jit_arches} %{zero_arches}
# Set of architectures which support SystemTap tapsets
%global systemtap_arches %{jit_arches}
# Set of architectures which support the serviceability agent
%global sa_arches       %{ix86} x86_64 sparcv9 sparc64 %{aarch64}
# Set of architectures which support class data sharing
# See https://bugzilla.redhat.com/show_bug.cgi?id=513605
# MetaspaceShared::generate_vtable_methods is not implemented for the PPC JIT
%global share_arches    %{ix86} x86_64 sparcv9 sparc64 %{aarch64}
# Set of architectures which support Java Flight Recorder (JFR)
%global jfr_arches      %{jit_arches}
# Set of architectures for which alt-java has SSB mitigation
%global ssbd_arches x86_64
# Set of architectures where we verify backtraces with gdb
%global gdb_arches %{jit_arches} %{zero_arches}
# Set of architectures for which we have a portable build
%global portable_build_arches %{aarch64} %{ix86} %{power64} s390x x86_64
# Architecture on which we run Java only tests
%global jdk_test_arch x86_64

# By default, we build a debug build during main build on JIT architectures
%if %{with slowdebug}
%ifarch %{debug_arches}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif
%else
%global include_debug_build 0
%endif

# By default, we build a fastdebug build during main build only on fastdebug architectures
%if %{with fastdebug}
%ifarch %{fastdebug_arches}
%global include_fastdebug_build 1
%else
%global include_fastdebug_build 0
%endif
%else
%global include_fastdebug_build 0
%endif

%if %{include_debug_build}
%global slowdebug_build %{debug_suffix}
%else
%global slowdebug_build %{nil}
%endif

%if %{include_fastdebug_build}
%global fastdebug_build %{fastdebug_suffix}
%else
%global fastdebug_build %{nil}
%endif

# If you disable all builds, then the build fails
# Build and test slowdebug first as it provides the best diagnostics
%global build_loop  %{slowdebug_build} %{fastdebug_build} %{normal_build}

%if 0%{?flatpak}
%global bootstrap_build false
%else
%ifarch %{bootstrap_arches}
%global bootstrap_build true
%else
%global bootstrap_build false
%endif
%endif

%global bootstrap_targets images
%global release_targets images docs-zip
# No docs nor bootcycle for debug builds
%global debug_targets images
# Target to use to just build HotSpot
%global hotspot_target hotspot

# JDK to use for bootstrapping
# Use OpenJDK 7 where available (on RHEL) to avoid
# having to use the rhel-7.x-java-unsafe-candidate hack
%if ! 0%{?fedora} && 0%{?rhel} <= 7
%global buildjdkver 1.7.0
%else
%global buildjdkver 1.8.0
%endif
%global bootjdk /usr/lib/jvm/java-%{buildjdkver}-openjdk

# debugedit tool for rewriting ELF file paths
%global debugedit %{_rpmconfigdir}/debugedit

# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimization of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security) and -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat -Wno-cpp|' | sed -r -e 's|-O[0-9]*||')
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||')
%global ourldflags %{__global_ldflags}

# With disabled nss is NSS deactivated, so NSS_LIBDIR can contain the wrong path
# the initialization must be here. Later the pkg-config have buggy behavior
# looks like openjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)
%global NSS_LIBS %(pkg-config --libs nss)
%global NSS_CFLAGS %(pkg-config --cflags nss-softokn)
# see https://bugzilla.redhat.com/show_bug.cgi?id=1332456
%global NSSSOFTOKN_BUILDTIME_NUMBER %(pkg-config --modversion nss-softokn || : )
%global NSS_BUILDTIME_NUMBER %(pkg-config --modversion nss || : )
# this is workaround for processing of requires during srpm creation
%global NSSSOFTOKN_BUILDTIME_VERSION %(if [ "x%{NSSSOFTOKN_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSSSOFTOKN_BUILDTIME_NUMBER}" ;fi)
%global NSS_BUILDTIME_VERSION %(if [ "x%{NSS_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSS_BUILDTIME_NUMBER}" ;fi)

# In some cases, the arch used by the JDK does
# not match _arch.
# Also, in some cases, the machine name used by SystemTap
# does not match that given by _target_cpu
%ifarch x86_64
%global archinstall amd64
%global stapinstall x86_64
%endif
%ifarch ppc
%global archinstall ppc
%global stapinstall powerpc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%global stapinstall powerpc
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%global stapinstall powerpc
%endif
%ifarch %{ix86}
%global archinstall i386
%global stapinstall i386
%endif
%ifarch ia64
%global archinstall ia64
%global stapinstall ia64
%endif
%ifarch s390
%global archinstall s390
%global stapinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%global stapinstall s390
%endif
%ifarch %{arm}
%global archinstall arm
%global stapinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%global stapinstall arm64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%global stapinstall %{_target_cpu}
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%global stapinstall %{_target_cpu}
%endif
# Need to support noarch for srpm build
%ifarch noarch
%global archinstall %{nil}
%global stapinstall %{nil}
%endif

%ifarch %{systemtap_arches}
%global with_systemtap 1
%else
%global with_systemtap 0
%endif

# New Version-String scheme-style defines
%global majorver 8

# Define version of OpenJDK 8 used
%global project openjdk
%global repo shenandoah-jdk8u
%global openjdk_revision 8u432-b06
%global shenandoah_revision shenandoah%{openjdk_revision}
# Define IcedTea version used for SystemTap tapsets and desktop files
%global icedteaver      3.15.0
# Define current Git revision for the FIPS support patches
%global fipsver 6d1aade0648
# Define current Git revision for the cacerts patch
%global cacertsver 8139f2361c2

# Standard JPackage naming and versioning defines
%global origin          openjdk
%global origin_nice     OpenJDK
%global top_level_dir_name   %{shenandoah_revision}

# Settings for local security configuration
%global security_file %{top_level_dir_name}/jdk/src/share/lib/security/java.security-%{_target_os}
%global cacerts_file /etc/pki/java/cacerts

# Define vendor information used by OpenJDK
%global oj_vendor Red Hat, Inc.
%global oj_vendor_url "https://www.redhat.com/"
# Define what url should JVM offer in case of a crash report
# order may be important, epel may have rhel declared
%if 0%{?epel}
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora%20EPEL&component=%{name}&version=epel%{epel}
%else
%if 0%{?fedora}
# Does not work for rawhide, keeps the version field empty
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=%{name}&version=%{fedora}
%else
%if 0%{?rhel}
%global oj_vendor_bug_url https://access.redhat.com/support/cases/
%else
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi
%endif
%endif
%endif

# e.g. aarch64-shenandoah-jdk8u212-b04-shenandoah-merge-2019-04-30 -> aarch64-shenandoah-jdk8u212-b04
%global version_tag     %(VERSION=%{shenandoah_revision}; echo ${VERSION%%-shenandoah-merge*})
# eg # jdk8u60-b27 -> jdk8u60 or # aarch64-jdk8u60-b27 -> aarch64-jdk8u60  (dont forget spec escape % by %%)
%global whole_update    %(VERSION=%{version_tag}; echo ${VERSION%%-*})
# eg  jdk8u60 -> 60 or aarch64-jdk8u60 -> 60
%global updatever       %(VERSION=%{whole_update}; echo ${VERSION##*u})
# eg jdk8u60-b27 -> b27
%global buildver        %(VERSION=%{version_tag}; echo ${VERSION##*-})
# rpmrelease numbering must start at 2 to be later than the 8.6 RPM
%global rpmrelease      2
# Settings used by the portable build
%global portablerelease 1
%global portablesuffix el8_8.88ciq_lts
%global portabledir 88ciq_lts
%global portablebuilddir /builddir/build/BUILD

# Define milestone (EA for pre-releases, GA ("fcs") for releases)
# Release will be (where N is usually a number starting at 1):
# - 0.N%%{?extraver}%%{?dist} for EA releases,
# - N%%{?extraver}{?dist} for GA releases
%global is_ga           1
%if %{is_ga}
%global milestone          fcs
%global milestone_version  %{nil}
%global extraver %{nil}
%global eaprefix %{nil}
%else
%global milestone          ea
%global milestone_version  "-ea"
%global extraver .%{milestone}
%global eaprefix 0.
%endif
# priority must be 7 digits in total. The expression is workarounding tip
%if %is_system_jdk
%global priority        %(TIP=1800%{updatever};  echo ${TIP/tip/999})
%else
# for non-default using 1, so slowdebugs can have 0
%global priority 00000%{interimver}1
%endif

%global javaver         1.%{majorver}.0

# parametrized macros are order-sensitive
%global compatiblename  %{name}
%global fullversion     %{compatiblename}-%{version}-%{release}
# output dir stub
%define installoutputdir() %{expand:install/jdk8.install%{?1}}
# we can copy the javadoc to not arched dir, or make it not noarch
%define uniquejavadocdir()    %{expand:%{fullversion}%{?1}}
# main id and dir of this jdk
%define uniquesuffix()        %{expand:%{fullversion}.%{_arch}%{?1}}

# Fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349.
# See also https://bugzilla.redhat.com/show_bug.cgi?id=1590796
# as to why some libraries *cannot* be excluded. In particular,
# these are:
# libjsig.so, libjava.so, libjawt.so, libjvm.so and libverify.so
%global _privatelibs libatk-wrapper[.]so.*|libattach[.]so.*|libawt_headless[.]so.*|libawt[.]so.*|libawt_xawt[.]so.*|libdt_socket[.]so.*|libfontmanager[.]so.*|libhprof[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas_unix[.]so.*|libjava_crw_demo[.]so.*%{jpeg_lib}|libjdwp[.]so.*|libjli[.]so.*|libjsdt[.]so.*|libjsoundalsa[.]so.*|libjsound[.]so.*|liblcms[.]so.*|libmanagement[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libnpt[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsplashscreen[.]so.*|libsunec[.]so.*|libsystemconf[.]so.*|libunpack[.]so.*|libzip[.]so.*|lib[.]so\\(SUNWprivate_.*
%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

%global etcjavasubdir     %{_sysconfdir}/java/java-%{javaver}-%{origin}
%define etcjavadir()      %{expand:%{etcjavasubdir}/%{uniquesuffix -- %{?1}}}
# Standard JPackage directories and symbolic links.
%define sdkdir()        %{expand:%{uniquesuffix -- %{?1}}}
%define jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%{?1}}

%define jredir()        %{expand:%{sdkdir -- %{?1}}/jre}
%define sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}
%define jrebindir()     %{expand:%{_jvmdir}/%{jredir -- %{?1}}/bin}
%global alt_java_name     alt-java

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

# For flatpack builds hard-code /usr/sbin/alternatives,
# otherwise use %%{_sbindir} relative path.
%if 0%{?flatpak}
%global alternatives_requires /usr/sbin/alternatives
%else
%global alternatives_requires %{_sbindir}/alternatives
%endif

%global family %{name}.%{_arch}
%global family_noarch  %{name}

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific sub-dir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinguish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka target_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdirttapset %{tapsetroot}/tapset/
%global tapsetdir %{tapsetdirttapset}/%{stapinstall}
%endif

# not-duplicated scriptlets for normal/debug packages
%global update_desktop_icons /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%define save_alternatives() %{expand:
  # warning! alternatives are localised!
  # LANG=cs_CZ.UTF-8  alternatives --display java | head
  # LANG=en_US.UTF-8  alternatives --display java | head
  function nonLocalisedAlternativesDisplayOfMaster() {
    LANG=en_US.UTF-8 alternatives --display "$MASTER"
  }
  function headOfAbove() {
    nonLocalisedAlternativesDisplayOfMaster | head -n $1
  }
  MASTER="%{?1}"
  LOCAL_LINK="%{?2}"
  FAMILY="%{?3}"
  rm -f %{_localstatedir}/lib/rpm-state/"$MASTER"_$FAMILY > /dev/null
  if nonLocalisedAlternativesDisplayOfMaster > /dev/null ; then
      if headOfAbove 1 | grep -q manual ; then
        if headOfAbove 2 | tail -n 1 | grep -q %{compatiblename} ; then
           headOfAbove 2  > %{_localstatedir}/lib/rpm-state/"$MASTER"_"$FAMILY"
        fi
      fi
  fi
}

%define save_and_remove_alternatives() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  upgrade1_uninstal0=%{?3}
  if [ "0$upgrade1_uninstal0" -gt 0 ] ; then # removal of this condition will cause persistence between uninstall
    %{save_alternatives %{?1} %{?2} %{?4}}
  fi
  alternatives --remove  "%{?1}" "%{?2}"
}

%define set_if_needed_alternatives() %{expand:
  MASTER="%{?1}"
  FAMILY="%{?2}"
  ALTERNATIVES_FILE="%{_localstatedir}/lib/rpm-state/$MASTER"_"$FAMILY"
  if [ -e  "$ALTERNATIVES_FILE" ] ; then
    rm "$ALTERNATIVES_FILE"
    alternatives --set $MASTER $FAMILY
  fi
}


%define post_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
exit 0
}

%define alternatives_java_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
key=java
alternatives \\
  --install %{_bindir}/java $key %{jrebindir -- %{?1}}/java $PRIORITY  --family %{family} \\
  --slave %{_jvmdir}/jre jre %{_jvmdir}/%{jredir -- %{?1}} \\
  --slave %{_bindir}/%{alt_java_name} %{alt_java_name} %{jrebindir -- %{?1}}/%{alt_java_name} \\
  --slave %{_bindir}/jjs jjs %{jrebindir -- %{?1}}/jjs \\
  --slave %{_bindir}/keytool keytool %{jrebindir -- %{?1}}/keytool \\
  --slave %{_bindir}/orbd orbd %{jrebindir -- %{?1}}/orbd \\
  --slave %{_bindir}/pack200 pack200 %{jrebindir -- %{?1}}/pack200 \\
  --slave %{_bindir}/rmid rmid %{jrebindir -- %{?1}}/rmid \\
  --slave %{_bindir}/rmiregistry rmiregistry %{jrebindir -- %{?1}}/rmiregistry \\
  --slave %{_bindir}/servertool servertool %{jrebindir -- %{?1}}/servertool \\
  --slave %{_bindir}/tnameserv tnameserv %{jrebindir -- %{?1}}/tnameserv \\
  --slave %{_bindir}/policytool policytool %{jrebindir -- %{?1}}/policytool \\
  --slave %{_bindir}/unpack200 unpack200 %{jrebindir -- %{?1}}/unpack200 \\
  --slave %{_mandir}/man1/java.1$ext java.1$ext \\
  %{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/%{alt_java_name}.1$ext %{alt_java_name}.1$ext \\
  %{_mandir}/man1/%{alt_java_name}-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jjs.1$ext jjs.1$ext \\
  %{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/keytool.1$ext keytool.1$ext \\
  %{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/orbd.1$ext orbd.1$ext \\
  %{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/pack200.1$ext pack200.1$ext \\
  %{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmid.1$ext rmid.1$ext \\
  %{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmiregistry.1$ext rmiregistry.1$ext \\
  %{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/servertool.1$ext servertool.1$ext \\
  %{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/tnameserv.1$ext tnameserv.1$ext \\
  %{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/policytool.1$ext policytool.1$ext \\
  %{_mandir}/man1/policytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/unpack200.1$ext unpack200.1$ext \\
  %{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1$ext

%{set_if_needed_alternatives $key %{family}}

for X in %{origin} %{javaver} ; do
  key=jre_"$X"
  alternatives --install %{_jvmdir}/jre-"$X" $key %{_jvmdir}/%{jredir -- %{?1}} $PRIORITY --family %{family}
  %{set_if_needed_alternatives $key %{family}}
done

key=jre_%{javaver}_%{origin}
alternatives --install %{_jvmdir}/jre-%{javaver}-%{origin} $key %{_jvmdir}/%{jrelnk -- %{?1}} $PRIORITY  --family %{family}
%{set_if_needed_alternatives $key %{family}}
}

%define post_headless() %{expand:
%ifarch %{share_arches}
%{jrebindir -- %{?1}}/java -Xshare:dump >/dev/null 2>/dev/null
%endif

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# see pretrans where this file is declared
# also see that pretrans is only for non-debug
if [ ! "%{?1}" == %{debug_suffix} ]; then
  if [ -f %{_libexecdir}/copy_jdk_configs_fixFiles.sh ] ; then
    sh  %{_libexecdir}/copy_jdk_configs_fixFiles.sh %{rpm_state_dir}/%{name}.%{_arch}  %{_jvmdir}/%{sdkdir -- %{?1}}
  fi
fi

exit 0
}

%define postun_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}


%define postun_headless() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  java  %{jrebindir -- %{?1}}/java $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{origin} %{_jvmdir}/%{jredir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{javaver} %{_jvmdir}/%{jredir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}} $post_state %{family}}
}

%define posttrans_script() %{expand:
%{update_desktop_icons}
}


%define alternatives_javac_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
key=javac
alternatives \\
  --install %{_bindir}/javac $key %{sdkbindir -- %{?1}}/javac $PRIORITY  --family %{family} \\
  --slave %{_jvmdir}/java java_sdk %{_jvmdir}/%{sdkdir -- %{?1}} \\
  --slave %{_bindir}/appletviewer appletviewer %{sdkbindir -- %{?1}}/appletviewer \\
  --slave %{_bindir}/clhsdb clhsdb %{sdkbindir -- %{?1}}/clhsdb \\
  --slave %{_bindir}/extcheck extcheck %{sdkbindir -- %{?1}}/extcheck \\
  --slave %{_bindir}/hsdb hsdb %{sdkbindir -- %{?1}}/hsdb \\
  --slave %{_bindir}/idlj idlj %{sdkbindir -- %{?1}}/idlj \\
  --slave %{_bindir}/jar jar %{sdkbindir -- %{?1}}/jar \\
  --slave %{_bindir}/jarsigner jarsigner %{sdkbindir -- %{?1}}/jarsigner \\
  --slave %{_bindir}/javadoc javadoc %{sdkbindir -- %{?1}}/javadoc \\
  --slave %{_bindir}/javah javah %{sdkbindir -- %{?1}}/javah \\
  --slave %{_bindir}/javap javap %{sdkbindir -- %{?1}}/javap \\
  --slave %{_bindir}/jcmd jcmd %{sdkbindir -- %{?1}}/jcmd \\
  --slave %{_bindir}/jconsole jconsole %{sdkbindir -- %{?1}}/jconsole \\
  --slave %{_bindir}/jdb jdb %{sdkbindir -- %{?1}}/jdb \\
  --slave %{_bindir}/jdeps jdeps %{sdkbindir -- %{?1}}/jdeps \\
%ifarch %{jfr_arches}
  --slave %{_bindir}/jfr jfr %{sdkbindir -- %{?1}}/jfr \\
%endif
  --slave %{_bindir}/jhat jhat %{sdkbindir -- %{?1}}/jhat \\
  --slave %{_bindir}/jinfo jinfo %{sdkbindir -- %{?1}}/jinfo \\
  --slave %{_bindir}/jmap jmap %{sdkbindir -- %{?1}}/jmap \\
  --slave %{_bindir}/jps jps %{sdkbindir -- %{?1}}/jps \\
  --slave %{_bindir}/jrunscript jrunscript %{sdkbindir -- %{?1}}/jrunscript \\
  --slave %{_bindir}/jsadebugd jsadebugd %{sdkbindir -- %{?1}}/jsadebugd \\
  --slave %{_bindir}/jstack jstack %{sdkbindir -- %{?1}}/jstack \\
  --slave %{_bindir}/jstat jstat %{sdkbindir -- %{?1}}/jstat \\
  --slave %{_bindir}/jstatd jstatd %{sdkbindir -- %{?1}}/jstatd \\
  --slave %{_bindir}/native2ascii native2ascii %{sdkbindir -- %{?1}}/native2ascii \\
  --slave %{_bindir}/rmic rmic %{sdkbindir -- %{?1}}/rmic \\
  --slave %{_bindir}/schemagen schemagen %{sdkbindir -- %{?1}}/schemagen \\
  --slave %{_bindir}/serialver serialver %{sdkbindir -- %{?1}}/serialver \\
  --slave %{_bindir}/wsgen wsgen %{sdkbindir -- %{?1}}/wsgen \\
  --slave %{_bindir}/wsimport wsimport %{sdkbindir -- %{?1}}/wsimport \\
  --slave %{_bindir}/xjc xjc %{sdkbindir -- %{?1}}/xjc \\
  --slave %{_mandir}/man1/appletviewer.1$ext appletviewer.1$ext \\
  %{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/extcheck.1$ext extcheck.1$ext \\
  %{_mandir}/man1/extcheck-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/idlj.1$ext idlj.1$ext \\
  %{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jar.1$ext jar.1$ext \\
  %{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jarsigner.1$ext jarsigner.1$ext \\
  %{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javac.1$ext javac.1$ext \\
  %{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javadoc.1$ext javadoc.1$ext \\
  %{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javah.1$ext javah.1$ext \\
  %{_mandir}/man1/javah-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javap.1$ext javap.1$ext \\
  %{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jcmd.1$ext jcmd.1$ext \\
  %{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jconsole.1$ext jconsole.1$ext \\
  %{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdb.1$ext jdb.1$ext \\
  %{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdeps.1$ext jdeps.1$ext \\
  %{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jhat.1$ext jhat.1$ext \\
  %{_mandir}/man1/jhat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jinfo.1$ext jinfo.1$ext \\
  %{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jmap.1$ext jmap.1$ext \\
  %{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jps.1$ext jps.1$ext \\
  %{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jrunscript.1$ext jrunscript.1$ext \\
  %{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jsadebugd.1$ext jsadebugd.1$ext \\
  %{_mandir}/man1/jsadebugd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstack.1$ext jstack.1$ext \\
  %{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstat.1$ext jstat.1$ext \\
  %{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstatd.1$ext jstatd.1$ext \\
  %{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/native2ascii.1$ext native2ascii.1$ext \\
  %{_mandir}/man1/native2ascii-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmic.1$ext rmic.1$ext \\
  %{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/schemagen.1$ext schemagen.1$ext \\
  %{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/serialver.1$ext serialver.1$ext \\
  %{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsgen.1$ext wsgen.1$ext \\
  %{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsimport.1$ext wsimport.1$ext \\
  %{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/xjc.1$ext xjc.1$ext \\
  %{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1$ext

%{set_if_needed_alternatives  $key %{family}}

for X in %{origin} %{javaver} ; do
  key=java_sdk_"$X"
  alternatives --install %{_jvmdir}/java-"$X" $key %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{family}
  %{set_if_needed_alternatives  $key %{family}}
done

key=java_sdk_%{javaver}_%{origin}
alternatives --install %{_jvmdir}/java-%{javaver}-%{origin} $key %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{family}
%{set_if_needed_alternatives  $key %{family}}
}

%define post_devel() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

exit 0
}

%define postun_devel() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javac %{sdkbindir -- %{?1}}/javac $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}
  %{save_and_remove_alternatives  java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $post_state %{family}}

update-desktop-database %{_datadir}/applications &> /dev/null || :

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}

%define posttrans_devel() %{expand:
%{alternatives_javac_install --  %{?1}}
%{update_desktop_icons}
}

%define alternatives_javadoc_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

key=javadocdir
alternatives --install %{_javadocdir}/java $key %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api $PRIORITY  --family %{family_noarch}
%{set_if_needed_alternatives  $key %{family_noarch}}
exit 0
}

%define postun_javadoc() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javadocdir  %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api $post_state %{family_noarch}}
exit 0
}

%define alternatives_javadoczip_install() %{expand:
if [ "x$debug"  == "xtrue" ] ; then
  set -x
fi
PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi
key=javadoczip
alternatives --install %{_javadocdir}/java-zip $key %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip $PRIORITY  --family %{family_noarch}
%{set_if_needed_alternatives  $key %{family_noarch}}
exit 0
}

%define postun_javadoc_zip() %{expand:
  if [ "x$debug"  == "xtrue" ] ; then
    set -x
  fi
  post_state=$1 # from postun, https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
  %{save_and_remove_alternatives  javadoczip  %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip $post_state %{family_noarch}}
exit 0
}

%define files_jre() %{expand:
%{_datadir}/icons/hicolor/*x*/apps/java-%{javaver}-%{origin}.png
%{_datadir}/applications/*policytool%{?1}.desktop
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libjsoundalsa.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libsplashscreen.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libawt_xawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libjawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/bin/policytool
}


%define files_jre_headless() %{expand:
%defattr(-,root,root,-)
%dir %{_sysconfdir}/.java/.systemPrefs
%dir %{_sysconfdir}/.java
%license %{_jvmdir}/%{jredir -- %{?1}}/ASSEMBLY_EXCEPTION
%license %{_jvmdir}/%{jredir -- %{?1}}/LICENSE
%license %{_jvmdir}/%{jredir -- %{?1}}/THIRD_PARTY_README
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/NEWS
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/README.md
%doc %{_defaultdocdir}/%{uniquejavadocdir -- %{?1}}/java-1.%{majorver}.0-openjdk-portable.specfile
%dir %{_jvmdir}/%{sdkdir -- %{?1}}
%{_jvmdir}/%{jrelnk -- %{?1}}
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/security
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/cacerts
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/cacerts.upstream
%dir %{_jvmdir}/%{jredir -- %{?1}}
%dir %{_jvmdir}/%{jredir -- %{?1}}/bin
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib
%{_jvmdir}/%{jredir -- %{?1}}/bin/java
%{_jvmdir}/%{jredir -- %{?1}}/bin/%{alt_java_name}
%{_jvmdir}/%{jredir -- %{?1}}/bin/jjs
%{_jvmdir}/%{jredir -- %{?1}}/bin/keytool
%{_jvmdir}/%{jredir -- %{?1}}/bin/orbd
%{_jvmdir}/%{jredir -- %{?1}}/bin/pack200
%{_jvmdir}/%{jredir -- %{?1}}/bin/rmid
%{_jvmdir}/%{jredir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{jredir -- %{?1}}/bin/servertool
%{_jvmdir}/%{jredir -- %{?1}}/bin/tnameserv
%{_jvmdir}/%{jredir -- %{?1}}/bin/unpack200
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/unlimited/
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/limited/
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/policy/unlimited/US_export_policy.jar
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/policy/unlimited/local_policy.jar
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/policy/limited/US_export_policy.jar
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/policy/limited/local_policy.jar
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/java.policy
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/java.security
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/blacklisted.certs
%config(noreplace) %{etcjavadir -- %{?1}}/lib/logging.properties
%config(noreplace) %{etcjavadir -- %{?1}}/lib/calendars.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/unlimited/US_export_policy.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/unlimited/local_policy.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/limited/US_export_policy.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/limited/local_policy.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/java.policy
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/java.security
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/blacklisted.certs
%{_jvmdir}/%{jredir -- %{?1}}/lib/logging.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/calendars.properties
%{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/%{alt_java_name}-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/policytool-%{uniquesuffix -- %{?1}}.1*
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/nss.cfg
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/nss.fips.cfg
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/nss.cfg
%config(noreplace) %{etcjavadir -- %{?1}}/lib/security/nss.fips.cfg
%ifarch %{share_arches}
%attr(444, root, root) %ghost %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/server/classes.jsa
%attr(444, root, root) %ghost %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/client/classes.jsa
%endif
%dir %{etcjavasubdir}
%dir %{etcjavadir -- %{?1}}
%dir %{etcjavadir -- %{?1}}/lib
%dir %{etcjavadir -- %{?1}}/lib/security
%{etcjavadir -- %{?1}}/lib/security/cacerts
%dir %{etcjavadir -- %{?1}}/lib/security/policy
%dir %{etcjavadir -- %{?1}}/lib/security/policy/limited
%dir %{etcjavadir -- %{?1}}/lib/security/policy/unlimited
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/server/
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/client/
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jli
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jli/libjli.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jvm.cfg
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libattach.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libawt.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libawt_headless.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libdt_socket.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libfontmanager.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libhprof.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libinstrument.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2gss.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2pcsc.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2pkcs11.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjaas_unix.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjava.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjava_crw_demo.so
%if %{system_libs}
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjavajpeg.so
%else
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjpeg.so
%endif
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjdwp.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsdt.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsig.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsound.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/liblcms.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libmanagement.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libmlib_image.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnet.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnio.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnpt.so
%ifarch %{sa_arches}
%ifnarch %{zero_arches}
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsaproc.so
%endif
%endif
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsctp.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsunec.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsystemconf.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libunpack.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libverify.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libzip.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/charsets.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/classlist
%{_jvmdir}/%{jredir -- %{?1}}/lib/content-types.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/currency.data
%{_jvmdir}/%{jredir -- %{?1}}/lib/flavormap.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/hijrah-config-umalqura.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/images/cursors/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/jce.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/jexec
%{_jvmdir}/%{jredir -- %{?1}}/lib/jsse.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/jvm.hprof.txt
%{_jvmdir}/%{jredir -- %{?1}}/lib/meta-index
%{_jvmdir}/%{jredir -- %{?1}}/lib/net.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/psfont.properties.ja
%{_jvmdir}/%{jredir -- %{?1}}/lib/psfontj2d.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/resources.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/rt.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/sound.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/tzdb.dat
%{_jvmdir}/%{jredir -- %{?1}}/lib/tzdb.dat.upstream
%{_jvmdir}/%{jredir -- %{?1}}/lib/management-agent.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/management/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/cmm/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/cldrdata.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/dnsns.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/jaccess.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/localedata.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/meta-index
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/nashorn.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/sunec.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/sunjce_provider.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/sunpkcs11.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/zipfs.jar
%ifarch %{jfr_arches}
%{_jvmdir}/%{jredir -- %{?1}}/lib/jfr.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/jfr/default.jfc
%{_jvmdir}/%{jredir -- %{?1}}/lib/jfr/profile.jfc
%endif

%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/images
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/images/cursors
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/management
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/cmm
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/ext
%ifarch %{jfr_arches}
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/jfr
%endif
}

%define files_devel() %{expand:
%defattr(-,root,root,-)
%license %{_jvmdir}/%{sdkdir -- %{?1}}/ASSEMBLY_EXCEPTION
%license %{_jvmdir}/%{sdkdir -- %{?1}}/LICENSE
%license %{_jvmdir}/%{sdkdir -- %{?1}}/THIRD_PARTY_README
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/include
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/appletviewer
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/clhsdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/extcheck
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/hsdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/idlj
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jar
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jarsigner
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/%{alt_java_name}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javac
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javadoc
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javah
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java-rmi.cgi
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jcmd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jconsole
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeps
%ifarch %{jfr_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jfr
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jhat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jinfo
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jjs
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jrunscript
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jsadebugd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstack
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstatd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/keytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/native2ascii
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/orbd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/pack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/policytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmic
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmid
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/schemagen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/serialver
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/servertool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/tnameserv
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/unpack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsgen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsimport
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/xjc
%{_jvmdir}/%{sdkdir -- %{?1}}/include/*
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/%{archinstall}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ct.sym
%if %{with_systemtap}
%{_jvmdir}/%{sdkdir -- %{?1}}/tapset
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ir.idl
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jconsole.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/orb.idl
%ifarch %{sa_arches}
%ifnarch %{zero_arches}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/sa-jdi.jar
%endif
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/dt.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jexec
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/tools.jar
%{_datadir}/applications/*jconsole%{?1}.desktop
%{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/extcheck-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javah-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jhat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jsadebugd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/native2ascii-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1*
%if %{with_systemtap}
%dir %{tapsetroot}
%dir %{tapsetdirttapset}
%dir %{tapsetdir}
%{tapsetdir}/*%{_arch}%{?1}.stp
%endif
}

%define files_demo() %{expand:
%defattr(-,root,root,-)
%license %{installoutputdir -- %{?1}}/jre/LICENSE
}

%define files_src() %{expand:
%defattr(-,root,root,-)
%{_jvmdir}/%{sdkdir -- %{?1}}/src.zip
}

%define files_javadoc() %{expand:
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}
%license %{installoutputdir -- %{?1}}/jre/LICENSE
}

%define files_javadoc_zip() %{expand:
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
%license %{installoutputdir -- %{?1}}/jre/LICENSE
}

%define files_accessibility() %{expand:
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libatk-wrapper.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/java-atk-wrapper.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/accessibility.properties
}

# not-duplicated requires/provides/obsoletes for normal/debug packages
%define java_rpo() %{expand:
Requires: fontconfig%{?_isa}
Requires: xorg-x11-fonts-Type1
# Require libXcomposite explicitly since it's only dynamically loaded
# at runtime. Fixes screenshot issues. See JDK-8150954.
Requires: libXcomposite%{?_isa}
# Requires rest of java
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# for java-X-openjdk package's desktop binding
%if 0%{?fedora} || 0%{?rhel} >= 8
Recommends: gtk2%{?_isa}
%endif

Provides: java-%{javaver}-%{origin} = %{epoch}:%{version}-%{release}

# Standard JPackage base provides
Provides: jre-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java%{?1} = %{epoch}:%{javaver}
Provides: jre%{?1} = %{epoch}:%{javaver}
%endif
}

%define java_headless_rpo() %{expand:
# Require /etc/pki/java/cacerts
Requires: ca-certificates
# Require javapackages-filesystem for ownership of /usr/lib/jvm/
Requires: javapackages-filesystem
# 2024a required as of JDK-8325150
Requires: tzdata-java >= 2024a
# for support of kernel stream control
# libsctp.so.1 is being `dlopen`ed on demand
Requires: lksctp-tools%{?_isa}
%if ! 0%{?flatpak}
# tool to copy jdk's configs - should be Recommends only, but then only dnf/yum enforce it,
# not rpm transaction and so no configs are persisted when pure rpm -u is run. It may be
# considered as regression
Requires: copy-jdk-configs >= 4.0
OrderWithRequires: copy-jdk-configs
%endif
# for printing support
Requires: cups-libs
# for system security properties
Requires: crypto-policies
# for FIPS PKCS11 provider
Requires: nss
# Post requires alternatives to install tool alternatives
Requires(post):   %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7
# for optional support of kernel stream control, card reader and printing bindings
%if 0%{?fedora} || 0%{?rhel} >= 8
Suggests: lksctp-tools%{?_isa}, pcsc-lite-devel%{?_isa}
%endif

# Standard JPackage base provides
Provides: jre-%{javaver}-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-headless%{?1} = %{epoch}:%{javaver}
Provides: java-headless%{?1} = %{epoch}:%{javaver}
%endif

# https://bugzilla.redhat.com/show_bug.cgi?id=1312019
Provides: /usr/bin/jjs

}

%define java_devel_rpo() %{expand:
# Requires base package
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install tool alternatives
Requires(post):   %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall tool alternatives
Requires(postun): %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage devel provides
Provides: java-sdk-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-sdk-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-devel%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-devel%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-devel-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-sdk-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-devel%{?1} = %{epoch}:%{javaver}
Provides: java-sdk%{?1} = %{epoch}:%{javaver}
%endif
}


%define java_demo_rpo() %{expand:
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

Provides: java-%{javaver}-demo%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-demo%{?1} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-demo%{?1} = %{epoch}:%{version}-%{release}
%endif
}

%define java_javadoc_rpo() %{expand:
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install javadoc alternative
Requires(post):   %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall javadoc alternative
Requires(postun): %{alternatives_requires}
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage javadoc provides
Provides: java-%{javaver}-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
%if %is_system_jdk
Provides: java-javadoc%{?1}%{?2} = %{epoch}:%{version}-%{release}
%endif
}

%define java_src_rpo() %{expand:
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

# Standard JPackage sources provides
Provides: java-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-src%{?1} = %{epoch}:%{version}-%{release}
}

%define java_accessibility_rpo() %{expand:
Requires: java-atk-wrapper%{?_isa}
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

Provides: java-accessibility = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-accessibility = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-accessibility = %{epoch}:%{version}-%{release}

}

# Prevent brp-java-repack-jars from being run
%global __jar_repack 0

Name: java-%{javaver}-%{origin}
Version: %{javaver}.%{updatever}.%{buildver}
Release: %{?eaprefix}%{rpmrelease}%{?extraver}%{?dist}
# Equivalent for the portable build
%global prelease %{?eaprefix}%{portablerelease}%{?extraver}
# java-1.5.0-ibm from jpackage.org set Epoch to 1 for unknown reasons
# and this change was brought into RHEL-4. java-1.5.0-ibm packages
# also included the epoch in their virtual provides. This created a
# situation where in-the-wild java-1.5.0-ibm packages provided "java =
# 1:1.5.0". In RPM terms, "1.6.0 < 1:1.5.0" since 1.6.0 is
# interpreted as 0:1.6.0. So the "java >= 1.6.0" requirement would be
# satisfied by the 1:1.5.0 packages. Thus we need to set the epoch in
# JDK package >= 1.6.0 to 1, and packages referring to JDK virtual
# provides >= 1.6.0 must specify the epoch, "java >= 1:1.6.0".

Epoch: 1
Summary: %{origin_nice} %{majorver} Runtime Environment
Group: Development/Languages

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily JAXP & JAXWS)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see THIRD_PARTY_README)
# The OpenJDK source tree includes the JPEG library (IJG), zlib & libpng (zlib), giflib and LCMS (MIT)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License: ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib
URL: http://openjdk.java.net/

# Shenandoah HotSpot
# openjdk/shenandoah-jdk8u contains an integration forest of
# OpenJDK 8u and the Shenandoah garbage collector
# To regenerate, use:
# VERSION=%%{shenandoah_revision}
# FILE_NAME_ROOT=${VERSION}
# REPO_ROOT=<path to checked-out repository> generate_source_tarball.sh
# where the source is obtained from http://github.com/%%{project}/%%{repo}
Source0: %{shenandoah_revision}.tar.xz

# Use 'icedtea_sync.sh' to update the following
# They are based on code contained in the IcedTea project (3.x).
# Systemtap tapsets. Zipped up to keep it small.
Source8: tapsets-icedtea-%{icedteaver}.tar.xz

# Desktop files. Adapted from IcedTea
Source9: jconsole.desktop.in
Source10: policytool.desktop.in

# nss configuration file
Source11: nss.cfg.in

# Removed libraries that we link instead
Source12: remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Ensure ECDSA is working
Source14: TestECDSA.java

# Verify system crypto (policy) can be disabled via a property
Source15: TestSecurityProperties.java

# Ensure vendor settings are correct
Source16: CheckVendor.java

# nss fips configuration file
Source17: nss.fips.cfg.in

# Ensure translations are available for new timezones
Source18: TestTranslations.java

# New versions of config files with aarch64 support. This is not upstream yet.
Source100: config.guess
Source101: config.sub

# Include portable spec and instructions on how to rebuild
Source19: README.md
Source20: java-1.%{majorver}.0-openjdk-portable.specfile
Source21: NEWS

# Repack export policy JARs with reproducible timestamps
Source22: repack_reproducible_policies.sh

# Setup variables to reference correct sources
%global releasezip %{_jvmdir}/%{name}-portable-%{version}-%{prelease}.portable.unstripped.jdk.%{portabledir}.%{_arch}.tar.xz
%global docszip %{_jvmdir}/%{name}-portable-%{version}-%{prelease}.portable.docs.%{portabledir}.%{_arch}.tar.xz
%global misczip %{_jvmdir}/%{name}-portable-%{version}-%{prelease}.portable.misc.%{portabledir}.%{_arch}.tar.xz
%global slowdebugzip %{_jvmdir}/%{name}-portable-%{version}-%{prelease}.portable.slowdebug.jdk.%{portabledir}.%{_arch}.tar.xz
%global fastdebugzip %{_jvmdir}/%{name}-portable-%{version}-%{prelease}.portable.fastdebug.jdk.%{portabledir}.%{_arch}.tar.xz

############################################
#
# RPM/distribution specific patches
#
# This section includes patches specific to
# Fedora/RHEL which can not be upstreamed
# either in their current form or at all.
############################################

# Accessibility patches
# Ignore AWTError when assistive technologies are loaded
Patch1: rh1648242-accessible_toolkit_crash_do_not_break_jvm.patch
# Turn on AssumeMP by default on RHEL systems
Patch534: rh1648246-always_instruct_vm_to_assume_multiple_processors_are_available.patch
# RH1648249: Add PKCS11 provider to java.security
Patch1000: rh1648249-add_commented_out_nss_cfg_provider_to_java_security.patch
# RH1582504: Use RSA as default for keytool, as DSA is disabled in all crypto policies except LEGACY
Patch1003: rh1582504-rsa_default_for_keytool.patch

# Crypto policy and FIPS support patches
# Patch is generated from the fips tree at https://github.com/rh-openjdk/jdk8u/tree/fips
# as follows: git diff %%{openjdk_revision} common jdk > fips-8u-$(git show -s --format=%h HEAD).patch
# Diff is limited to src and make subdirectories to exclude .github changes
# Fixes currently included:
# PR3183, RH1340845: Support Fedora/RHEL8 system crypto policy
# PR3655: Allow use of system crypto policy to be disabled by the user
# RH1655466: Support RHEL FIPS mode using SunPKCS11 provider
# RH1760838: No ciphersuites available for SSLSocket in FIPS mode
# RH1860986: Disable TLSv1.3 with the NSS-FIPS provider until PKCS#11 v3.0 support is available
# RH1906862: Always initialise JavaSecuritySystemConfiguratorAccess
# RH1929465: Improve system FIPS detection
# RH1996182: Login to the NSS software token in FIPS mode
# RH1991003: Allow plain key import unless com.redhat.fips.plainKeySupport is set to false
# RH2021263: Resolve outstanding FIPS issues
# RH2052819: Fix FIPS reliance on crypto policies
# RH2052829: Detect NSS at Runtime for FIPS detection
# RH2036462: sun.security.pkcs11.wrapper.PKCS11.getInstance breakage
# RH2090378: Revert to disabling system security properties and FIPS mode support together
Patch1001: fips-8u-%{fipsver}.patch

#############################################
#
# Upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed to the current development
# tree of OpenJDK.
#############################################
# PR2737: Allow multiple initialization of PKCS11 libraries
Patch5: pr2737-allow_multiple_pkcs11_library_initialisation_to_be_a_non_critical_error.patch
# Turn off strict overflow on IndicRearrangementProcessor{,2}.cpp following 8140543: Arrange font actions
Patch512: rh1649664-awt2dlibraries_compiled_with_no_strict_overflow.patch
# RH1337583, PR2974: PKCS#10 certificate requests now use CRLF line endings rather than system line endings
Patch523: pr2974-rh1337583-add_systemlineendings_option_to_keytool_and_use_line_separator_instead_of_crlf_in_pkcs10.patch
# PR3083, RH1346460: Regression in SSL debug output without an ECC provider
Patch528: pr3083-rh1346460-for_ssl_debug_return_null_instead_of_exception_when_theres_no_ecc_provider.patch
# PR2888: OpenJDK should check for system cacerts database (e.g. /etc/pki/java/cacerts)
# PR3575, RH1567204: System cacerts database handling should not affect jssecacerts
# RH2055274: Revert default keystore to JAVA_HOME/jre/lib/security/cacerts in portable builds
# Must be applied after the FIPS patch as it also changes java.security
# Patch is generated from the cacerts tree at https://github.com/rh-openjdk/jdk8u/tree/cacerts
# as follows: git diff fips > pr2888-rh2055274-support_system_cacerts-$(git show -s --format=%h HEAD).patch
Patch539: pr2888-rh2055274-support_system_cacerts-%{cacertsver}.patch
# RH1684077, JDK-8009550: Depend on pcsc-lite-libs instead of pcsc-lite-devel as this is only in optional repo
Patch541: rh1684077-openjdk_should_depend_on_pcsc-lite-libs_instead_of_pcsc-lite-devel.patch
# RH1750419: Enable build of speculative store bypass hardened alt-java (CVE-2018-3639)
Patch600: rh1750419-redhat_alt_java.patch

#############################################
#
# Arch-specific upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed upstream and are specific
# to certain architectures. This usually means the
# current OpenJDK development branch, but may also
# include other trees e.g. for the AArch64 port for
# OpenJDK 8u.
#############################################
# s390: PR3593: Use "%z" for size_t on s390 as size_t != intptr_t
Patch103: pr3593-s390_use_z_format_specifier_for_size_t_arguments_as_size_t_not_equals_to_int.patch
# x86: S8199936, PR3533: HotSpot generates code with unaligned stack, crashes on SSE operations (-mstackrealign workaround)
Patch105: jdk8199936-pr3533-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x.patch
# S390 ambiguous log2_intptr calls
Patch107: s390-8214206_fix.patch

#############################################
#
# Patches which need backporting to 8u
#
# This section includes patches which have
# been pushed upstream to the latest OpenJDK
# development tree, but need to be backported
# to OpenJDK 8u.
#############################################
# S8074839, PR2462: Resolve disabled warnings for libunpack and the unpack200 binary
# This fixes printf warnings that lead to build failure with -Werror=format-security from optflags
Patch502: pr2462-resolve_disabled_warnings_for_libunpack_and_the_unpack200_binary.patch
# PR3591: Fix for bug 3533 doesn't add -mstackrealign to JDK code
Patch571: jdk8199936-pr3591-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x_jdk.patch
# 8143245, PR3548: Zero build requires disabled warnings
Patch574: jdk8143245-pr3548-zero_build_requires_disabled_warnings.patch
# s390: JDK-8203030, Type fixing for s390
Patch102: jdk8203030-zero_s390_31_bit_size_t_type_conflicts_in_shared_code.patch
# 8035341: Allow using a system installed libpng
Patch202: jdk8035341-allow_using_system_installed_libpng.patch
# 8042159: Allow using a system-installed lcms2
Patch203: jdk8042159-allow_using_system_installed_lcms2-root.patch
Patch204: jdk8042159-allow_using_system_installed_lcms2-jdk.patch
# JDK-8257794: Zero: assert(istate->_stack_limit == istate->_thread->last_Java_sp() + 1) failed: wrong on Linux/x86_32
Patch581: jdk8257794-remove_broken_assert.patch
# JDK-8186464, RH1433262: ZipFile cannot read some InfoZip ZIP64 zip files
Patch12: jdk8186464-rh1433262-zip64_failure.patch
# JDK-8328999, RH2251025 - Update GIFlib to 5.2.2 (PR#571)
Patch13: jdk8328999-update_giflib_5.2.2.patch

#############################################
#
# Patches appearing in 8u382
#
# This section includes patches which are present
# in the listed OpenJDK 8u release and should be
# able to be removed once that release is out
# and used by this RPM.
#############################################


#############################################
#
# Patches ineligible for 8u
#
# This section includes patches which are present
# upstream, but ineligible for upstream 8u backport.
#############################################
# 8043805: Allow using a system-installed libjpeg
Patch201: jdk8043805-allow_using_system_installed_libjpeg.patch

#############################################
#
# Shenandoah fixes
#
# This section includes patches which are
# specific to the Shenandoah garbage collector
# and should be upstreamed to the appropriate
# trees.
#############################################

#############################################
#
# Non-OpenJDK fixes
#
# This section includes patches to code other
# that from OpenJDK.
#############################################

#############################################
#
# Dependencies
#
#############################################
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: alsa-lib-devel
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
# elfutils only are OK for build without AOT
BuildRequires: elfutils-devel
BuildRequires: fontconfig-devel
BuildRequires: freetype-devel
BuildRequires: gcc-c++
BuildRequires: gdb
BuildRequires: libxslt
BuildRequires: libX11-devel
BuildRequires: libXext-devel
BuildRequires: libXi-devel
BuildRequires: libXinerama-devel
BuildRequires: libXrender-devel
BuildRequires: libXt-devel
BuildRequires: libXtst-devel
# Requirement for setting up nss.cfg and nss.fips.cfg
BuildRequires: nss-devel
# Requirement for system security property test
BuildRequires: crypto-policies
BuildRequires: pkgconfig
BuildRequires: xorg-x11-proto-devel
BuildRequires: tar
BuildRequires: unzip
BuildRequires: zip
# For definitions and macros like jvmdir
BuildRequires: javapackages-filesystem
%if %{include_normal_build}
BuildRequires: java-1.%{majorver}.0-openjdk-portable-unstripped = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
%if %{include_fastdebug_build}
BuildRequires: java-1.%{majorver}.0-openjdk-portable-devel-fastdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
%if %{include_debug_build}
BuildRequires: java-1.%{majorver}.0-openjdk-portable-devel-slowdebug = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
%endif
BuildRequires: java-1.%{majorver}.0-openjdk-portable-docs = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
BuildRequires: java-1.%{majorver}.0-openjdk-portable-misc = %{epoch}:%{version}-%{prelease}.%{portablesuffix}
# Zero-assembler build requirement
%ifarch %{zero_arches}
BuildRequires: libffi-devel
%endif
# 2024a required as of JDK-8325150
BuildRequires: tzdata-java >= 2024a
# Earlier versions have a bug in tree vectorization on PPC
BuildRequires: gcc >= 4.8.3-8

%if %{with_systemtap}
BuildRequires: systemtap-sdt-devel
%endif

%if %{system_libs}
BuildRequires: giflib-devel
BuildRequires: lcms2-devel
BuildRequires: libjpeg-devel
BuildRequires: libpng-devel
BuildRequires: zlib-devel
%else
# Version in jdk/src/share/native/sun/awt/giflib/gif_lib.h
Provides: bundled(giflib) = 5.2.2
# Version in jdk/src/share/native/sun/java2d/cmm/lcms/lcms2.h
Provides: bundled(lcms2) = 2.11.0
# Version in jdk/src/share/native/sun/awt/image/jpeg/jpeglib.h
Provides: bundled(libjpeg) = 6b
# Version in jdk/src/share/native/sun/awt/libpng/png.h
Provides: bundled(libpng) = 1.6.39
# Version in jdk/src/share/native/java/util/zip/zlib/zlib.h
Provides: bundled(zlib) = 1.3.1
%endif

# this is always built, also during debug-only build
# when it is built in debug-only this package is just placeholder
%{java_rpo %{nil}}

%description
The %{origin_nice} %{majorver} runtime environment.

%if %{include_debug_build}
%package slowdebug
Summary: %{origin_nice} %{majorver} Runtime Environment %{debug_on}
Group: Development/Languages

%{java_rpo -- %{debug_suffix_unquoted}}
%description slowdebug
The %{origin_nice} %{majorver} runtime environment.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package fastdebug
Summary: %{origin_nice} %{majorver} Runtime Environment %{fastdebug_on}
Group: Development/Languages

%{java_rpo -- %{fastdebug_suffix_unquoted}}
%description fastdebug
The %{origin_nice} %{majorver} runtime environment.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package headless
Summary: %{origin_nice} %{majorver} Headless Runtime Environment
Group: Development/Languages

%{java_headless_rpo %{nil}}

%description headless
The %{origin_nice} %{majorver} runtime environment without audio and video support.
%endif

%if %{include_debug_build}
%package headless-slowdebug
Summary: %{origin_nice} %{majorver} Runtime Environment %{debug_on}
Group: Development/Languages

%{java_headless_rpo -- %{debug_suffix_unquoted}}

%description headless-slowdebug
The %{origin_nice} %{majorver} runtime environment without audio and video support.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package headless-fastdebug
Summary: %{origin_nice} %{majorver} Runtime Environment %{fastdebug_on}
Group: Development/Languages

%{java_headless_rpo -- %{fastdebug_suffix_unquoted}}

%description headless-fastdebug
The %{origin_nice} %{majorver} runtime environment without audio and video support.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package devel
Summary: %{origin_nice} %{majorver} Development Environment
Group: Development/Tools

%{java_devel_rpo %{nil}}

%description devel
The %{origin_nice} %{majorver} development tools.
%endif

%if %{include_debug_build}
%package devel-slowdebug
Summary: %{origin_nice} %{majorver} Development Environment %{debug_on}
Group: Development/Tools

%{java_devel_rpo -- %{debug_suffix_unquoted}}

%description devel-slowdebug
The %{origin_nice} %{majorver} development tools.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package devel-fastdebug
Summary: %{origin_nice} %{majorver} Development Environment %{fastdebug_on}
Group: Development/Tools

%{java_devel_rpo -- %{fastdebug_suffix_unquoted}}

%description devel-fastdebug
The %{origin_nice} %{majorver} development tools.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package demo
Summary: %{origin_nice} %{majorver} Demos
Group: Development/Languages

%{java_demo_rpo %{nil}}

%description demo
The %{origin_nice} %{majorver} demos.
%endif

%if %{include_debug_build}
%package demo-slowdebug
Summary: %{origin_nice} %{majorver} Demos %{debug_on}
Group: Development/Languages

%{java_demo_rpo -- %{debug_suffix_unquoted}}

%description demo-slowdebug
The %{origin_nice} %{majorver} demos.
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package demo-fastdebug
Summary: %{origin_nice} %{majorver} Demos %{fastdebug_on}
Group: Development/Languages

%{java_demo_rpo -- %{fastdebug_suffix_unquoted}}

%description demo-fastdebug
The %{origin_nice} %{majorver} demos.
%{fastdebug_warning}
%endif

%if %{include_normal_build}
%package src
Summary: %{origin_nice} %{majorver} Source Bundle
Group: Development/Languages

%{java_src_rpo %{nil}}

%description src
The %{compatiblename}-src sub-package contains the complete %{origin_nice} %{majorver}
class library source code for use by IDE indexers and debuggers.
%endif

%if %{include_debug_build}
%package src-slowdebug
Summary: %{origin_nice} %{majorver} Source Bundle %{for_debug}
Group: Development/Languages

%{java_src_rpo -- %{debug_suffix_unquoted}}

%description src-slowdebug
The %{compatiblename}-src-slowdebug sub-package contains the complete %{origin_nice} %{majorver}
 class library source code for use by IDE indexers and debuggers, %{for_debug}.
%endif

%if %{include_fastdebug_build}
%package src-fastdebug
Summary: %{origin_nice} %{majorver} Source Bundle %{for_fastdebug}
Group: Development/Languages

%{java_src_rpo -- %{fastdebug_suffix_unquoted}}

%description src-fastdebug
The %{compatiblename}-src-fastdebug sub-package contains the complete %{origin_nice} %{majorver}
 class library source code for use by IDE indexers and debuggers, %{for_fastdebug}.
%endif

%if %{include_normal_build}
%package javadoc
Summary: %{origin_nice} %{majorver} API documentation
Group: Documentation
Requires: javapackages-filesystem
Obsoletes: javadoc-slowdebug < 1:1.8.0.212.b04-4
BuildArch: noarch

%{java_javadoc_rpo -- %{nil} -zip}
%{java_javadoc_rpo -- %{nil} %{nil}}

%description javadoc
The %{origin_nice} %{majorver} API documentation.

%package javadoc-zip
Summary: %{origin_nice} %{majorver} API documentation compressed in a single archive
Group: Documentation
Requires: javapackages-filesystem
Obsoletes: javadoc-zip-slowdebug < 1:1.8.0.212.b04-4
BuildArch: noarch

%{java_javadoc_rpo -- %{nil} %{nil}}

%description javadoc-zip
The %{origin_nice} %{majorver} API documentation compressed in a single archive.

%package accessibility
Summary: %{origin_nice} %{majorver} accessibility connector

%{java_accessibility_rpo %{nil}}

%description accessibility
Enables accessibility support in %{origin_nice} %{majorver} by using java-atk-wrapper. This allows
compatible at-spi2 based accessibility programs to work for AWT and Swing-based
programs.

Please note, the java-atk-wrapper is still in beta, and %{origin_nice} %{majorver} itself is still
being tuned to be working with accessibility features. There are known issues
with accessibility on, so please do not install this package unless you really
need to.
%endif

%if %{include_debug_build}
%package accessibility-slowdebug
Summary: %{origin_nice} %{majorver} accessibility connector %{for_debug}

%{java_accessibility_rpo -- %{debug_suffix_unquoted}}

%description accessibility-slowdebug
See normal java-%{version}-openjdk-accessibility description.
%endif

%if %{include_fastdebug_build}
%package accessibility-fastdebug
Summary: %{origin_nice} %{majorver} accessibility connector %{for_fastdebug}

%{java_accessibility_rpo -- %{fastdebug_suffix_unquoted}}

%description accessibility-fastdebug
See normal java-%{version}-openjdk-accessibility description.
%endif

%prep

# Using the echo macro breaks rpmdev-bumpspec, as it parses the first line of stdout :-(
%if 0%{?stapinstall:1}
  echo "CPU: %{_target_cpu}, arch install directory: %{archinstall}, SystemTap install directory: %{stapinstall}"
%else
  %{error:Unrecognised architecture %{_target_cpu}}
%endif

if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_fastdebug_build} -eq 0 -o  %{include_fastdebug_build} -eq 1 ] ; then
  echo "include_fastdebug_build is %{include_fastdebug_build}"
else
  echo "include_fastdebug_build is %{include_fastdebug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 13
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 -a  %{include_fastdebug_build} -eq 0 ] ; then
  echo "You have disabled all builds (normal,fastdebug,slowdebug). That is a no go."
  exit 14
fi

echo "Update version: %{updatever}"
echo "Build number: %{buildver}"
echo "Milestone: %{milestone}"
%ifnarch %{ix86}
export XZ_OPT="-T0"
%endif
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 7 ] ; then
 echo "priority must be 7 digits in total, violated"
 exit 14
fi
# For old patches
ln -s %{top_level_dir_name} jdk8
ln -s %{top_level_dir_name} openjdk

# replace outdated configure guess script
#
# the configure macro will do this too, but it also passes a few flags not
# supported by openjdk configure script
cp %{SOURCE100} %{top_level_dir_name}/common/autoconf/build-aux/
cp %{SOURCE101} %{top_level_dir_name}/common/autoconf/build-aux/

# OpenJDK patches

# This syntax is deprecated:
#    %patchN [...]
# and should be replaced with:
#    %patch -PN [...]
# For example:
#    %patch1001 -p1
# becomes:
#    %patch -P1001 -p1
# The replacement format suggested by recent (circa Fedora 38) RPM
# deprecation messages:
#    %patch N [...]
# is not backward-compatible with prior (circa RHEL-8) versions of
# rpmbuild.

%if %{system_libs}
# Remove libraries that are linked
sh %{SOURCE12}
%endif

# System library fixes
%if %{system_libs}
%patch -P201
%patch -P202
%patch -P203
%patch -P204
%endif

%patch -P1
%patch -P5

# s390 build fixes
%patch -P102
%patch -P103
%patch -P107

# AArch64 fixes

# x86 fixes
pushd %{top_level_dir_name}
%patch -P105 -p1
popd

# Upstreamable fixes
%patch -P512
%patch -P523
%patch -P528
%patch -P571
%patch -P574
%patch -P581
%patch -P541
%patch -P12
pushd %{top_level_dir_name}
%patch -P502 -p1
%patch -P13 -p1
popd

pushd %{top_level_dir_name}
# Add crypto policy and FIPS support
%patch -P1001 -p1
# nss.cfg PKCS11 support; must come last as it also alters java.security
%patch -P1000 -p1
# system cacerts support
%patch -P539 -p1
popd

# RPM-only fixes
%patch -P600
%patch -P1003

# RHEL-only patches
%if ! 0%{?fedora} && 0%{?rhel} <= 7
%patch -P534
%endif

# Shenandoah patches

# Prepare desktop files
# The _X_ syntax indicates variables that are replaced by make upstream
# The @X@ syntax indicates variables that are replaced by configure upstream
for suffix in %{build_loop} ; do
for file in %{SOURCE9} %{SOURCE10} ; do
    FILE=`basename $file | sed -e s:\.in$::g`
    EXT="${FILE##*.}"
    NAME="${FILE%.*}"
    OUTPUT_FILE=$NAME$suffix.$EXT
    sed    -e  "s:_SDKBINDIR_:%{sdkbindir -- $suffix}:g" $file > $OUTPUT_FILE
    sed -i -e  "s:_JREBINDIR_:%{jrebindir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e  "s:@target_cpu@:%{_arch}:g" $OUTPUT_FILE
    sed -i -e  "s:@OPENJDK_VER@:%{version}-%{release}.%{_arch}$suffix:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_VER@:%{javaver}:g" $OUTPUT_FILE
    sed -i -e  "s:@JAVA_VENDOR@:%{origin}:g" $OUTPUT_FILE
done
done

# Setup nss.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE11} > nss.cfg

# Setup nss.fips.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE17} > nss.fips.cfg

# Setup security policy
sed -i -e "s:^security.systemCACerts=.*:security.systemCACerts=%{cacerts_file}:" %{security_file}

%build

function customisejdk() {
    local imagepath=${1}

     if [ -d ${imagepath} ] ; then
        # Turn on system security properties
        sed -i -e "s:^security.useSystemPropertiesFile=.*:security.useSystemPropertiesFile=true:" \
            ${imagepath}/jre/lib/security/java.security

        # Use system-wide tzdata
        mv ${imagepath}/jre/lib/tzdb.dat{,.upstream}
        ln -sv %{_datadir}/javazi-1.8/tzdb.dat ${imagepath}/jre/lib/tzdb.dat

        # Rename OpenJDK cacerts database
        mv ${imagepath}/jre/lib/security/cacerts{,.upstream}
        # Install cacerts symlink needed by some apps which hard-code the path
        ln -sv %{cacerts_file} ${imagepath}/jre/lib/security
    fi
}

mkdir -p $(dirname %{installoutputdir})

docdir=%{installoutputdir -- "-docs"}
tar -xJf %{docszip}
mv %{name}*.docs.* ${docdir}

miscdir=%{installoutputdir -- "-misc"}
tar -xJf %{misczip}
mv %{name}*.misc.* ${miscdir}

for suffix in %{build_loop} ; do

    if [ "x$suffix" = "x" ] ; then
        jdkzip=%{releasezip}
    elif [ "x$suffix" = "x%{fastdebug_suffix_unquoted}" ] ; then
        jdkzip=%{fastdebugzip}
    else # slowdebug
        jdkzip=%{slowdebugzip}
        debugbuild=release
    fi

    installdir=%{installoutputdir -- ${suffix}}

    # TODO: should verify checksums when using packages from buildroot
    tar -xJf ${jdkzip}
    mv %{name}* ${installdir}
    # Fix build paths in ELF files so it looks like we built them
    portablenvr="%{name}-portable-%{version}-%{prelease}.%{portablesuffix}.%{_arch}"
    for file in $(find ${installdir} -type f) ; do
        if file ${file} | grep -q 'ELF'; then
            %{debugedit} -b %{portablebuilddir}/${portablenvr} -d $(pwd) -n ${file}
        fi
    done

  # Set tapset variables to match this build
%if %{with_systemtap}
  for file in ${miscdir}/tapset${suffix}/*.in; do
    OUTPUT_FILE=`echo $file | sed -e "s:\.stp\.in$:-%{version}-%{release}.%{_arch}.stp:g"`
    sed -e "s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/server/libjvm.so:g" $file > ${OUTPUT_FILE}
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -i -e "s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/lib/client/libjvm.so:g" ${OUTPUT_FILE}
%else
    sed -i -e "/@ABS_CLIENT_LIBJVM_SO@/d" ${OUTPUT_FILE}
%endif
    sed -i -e "s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e "s:@prefix@:%{_jvmdir}/%{sdkdir -- $suffix}/:g" $OUTPUT_FILE
  done
%endif

    # Final setup on the main image
    customisejdk ${installdir}

    # Print release information
    cat ${installdir}/release

# build cycles
done

%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{build_loop} ; do

export JAVA_HOME=$(pwd)/%{installoutputdir -- $suffix}

# Only test on one architecture (the fastest) for Java only tests
%ifarch %{jdk_test_arch}

  # Check unlimited policy has been used
  $JAVA_HOME/bin/javac -d . %{SOURCE13}
  $JAVA_HOME/bin/java TestCryptoLevel

  # Check ECC is working
  $JAVA_HOME/bin/javac -d . %{SOURCE14}
  $JAVA_HOME/bin/java $(echo $(basename %{SOURCE14})|sed "s|\.java||")

  # Check system crypto (policy) is active and can be disabled
  # Test takes a single argument - true or false - to state whether system
  # security properties are enabled or not.
  $JAVA_HOME/bin/javac -d . %{SOURCE15}
  export PROG=$(echo $(basename %{SOURCE15})|sed "s|\.java||")
  export SEC_DEBUG="-Djava.security.debug=properties"
  $JAVA_HOME/bin/java ${SEC_DEBUG} ${PROG} true
  $JAVA_HOME/bin/java ${SEC_DEBUG} -Djava.security.disableSystemPropertiesFile=true ${PROG} false

  # Check correct vendor values have been set
  $JAVA_HOME/bin/javac -d . %{SOURCE16}
  $JAVA_HOME/bin/java $(echo $(basename %{SOURCE16})|sed "s|\.java||") "%{oj_vendor}" %{oj_vendor_url} %{oj_vendor_bug_url}

  # Check translations are available for new timezones
  $JAVA_HOME/bin/javac -d . %{SOURCE18}
  $JAVA_HOME/bin/java $(echo $(basename %{SOURCE18})|sed "s|\.java||") JRE

  # Check src.zip has all sources. See RHBZ#1130490
  unzip -l $JAVA_HOME/src.zip | grep 'sun.misc.Unsafe'

  # Check class files include useful debugging information
  $JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
  $JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
  $JAVA_HOME/bin/javap -l java.lang.Object | grep LocalVariableTable

  # Check generated class files include useful debugging information
  $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
  $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
  $JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LocalVariableTable

%else

  # Just run a basic java -version test on other architectures
  $JAVA_HOME/bin/java -version

%endif

# Check java launcher has no SSB mitigation
if ! nm $JAVA_HOME/bin/java | grep set_speculation ; then true ; else false; fi

# Check alt-java launcher has SSB mitigation on supported architectures
%ifarch %{ssbd_arches}
nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation
%else
if ! nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation ; then true ; else false; fi
%endif

# Check debug symbols are present and can identify code
find "$JAVA_HOME" -iname '*.so' -print0 | while read -d $'\0' lib
do
  if [ -f "$lib" ] ; then
    echo "Testing $lib for debug symbols"
    # All these tests rely on RPM failing the build if the exit code of any set
    # of piped commands is non-zero.

    # Test for .debug_* sections in the shared object. This is the main test
    # Stripped objects will not contain these
    eu-readelf -S "$lib" | grep "] .debug_"
    test $(eu-readelf -S "$lib" | grep -E "\]\ .debug_(info|abbrev)" | wc --lines) == 2

    # Test FILE symbols. These will most likely be removed by anything that
    # manipulates symbol tables because it's generally useless. So a nice test
    # that nothing has messed with symbols
    old_IFS="$IFS"
    IFS=$'\n'
    for line in $(eu-readelf -s "$lib" | grep "00000000      0 FILE    LOCAL  DEFAULT")
    do
     # We expect to see .cpp files, except for architectures like aarch64 and
     # s390 where we expect .o and .oS files
      echo "$line" | grep -E "ABS ((.*/)?[-_a-zA-Z0-9]+\.(c|cc|cpp|cxx|o|oS))?$"
    done
    IFS="$old_IFS"

    # If this is the JVM, look for javaCalls.(cpp|o) in FILEs, for extra sanity checking
    if [ "`basename $lib`" = "libjvm.so" ]; then
      eu-readelf -s "$lib" | \
        grep -E "00000000      0 FILE    LOCAL  DEFAULT      ABS javaCalls.(cpp|o)$"
    fi

    # Test that there are no .gnu_debuglink sections pointing to another
    # debuginfo file. There shouldn't be any debuginfo files, so the link makes
    # no sense either
    eu-readelf -S "$lib" | grep 'gnu'
    if eu-readelf -S "$lib" | grep '] .gnu_debuglink' | grep PROGBITS; then
      echo "bad .gnu_debuglink section."
      eu-readelf -x .gnu_debuglink "$lib"
      false
    fi
  fi
done

# Make sure gdb can do a backtrace based on line numbers on libjvm.so
# javaCalls.cpp:58 should map to:
# http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/ff3b27e6bcc2/src/share/vm/runtime/javaCalls.cpp#l58
# Using line number 1 might cause build problems. See:
# https://bugzilla.redhat.com/show_bug.cgi?id=1539664
# https://bugzilla.redhat.com/show_bug.cgi?id=1538767
gdb -q "$JAVA_HOME/bin/java" <<EOF | tee gdb.out
handle SIGSEGV pass nostop noprint
handle SIGILL pass nostop noprint
set breakpoint pending on
break javaCalls.cpp:58
commands 1
backtrace
quit
end
run -version
EOF

%ifarch %{gdb_arches}
grep 'JavaCallWrapper::JavaCallWrapper' gdb.out
%endif

# build cycles check
done

%install
STRIP_KEEP_SYMTAB=libjvm*

for suffix in %{build_loop} ; do

  # Should match same definitions in build section
  jdk_image=%{installoutputdir -- $suffix}
  docdir=$(pwd)/%{installoutputdir -- "-docs"}
  miscdir=$(pwd)/%{installoutputdir -- "-misc"}

  # Install release notes and rebuild instructions
  commondocdir=${RPM_BUILD_ROOT}%{_defaultdocdir}/%{uniquejavadocdir -- $suffix}
  install -d -m 755 ${commondocdir}
  mv ${jdk_image}/NEWS ${commondocdir}
  cp -a %{SOURCE19} %{SOURCE20} ${commondocdir}

  # Install the jdk

  # Install jsa directories so we can own them
  mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}/server/
  mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}/client/

%if %{with_systemtap}
  # Install systemtap support files
  install -dm 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset
  cp -a ${miscdir}/tapset$suffix/*.stp $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
  pushd  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
   tapsetFiles=`ls *.stp`
  popd
  install -d -m 755 $RPM_BUILD_ROOT%{tapsetdir}
  for name in $tapsetFiles ; do
    targetName=`echo $name | sed "s/.stp/$suffix.stp/"`
    ln -sf %{_jvmdir}/%{sdkdir -- $suffix}/tapset/$name $RPM_BUILD_ROOT%{tapsetdir}/$targetName
  done
%endif

  # Install versioned symlinks
  pushd $RPM_BUILD_ROOT%{_jvmdir}
    ln -sf %{jredir -- $suffix} %{jrelnk -- $suffix}
  popd

  pushd ${jdk_image}

  # Install main files.
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  cp -a bin include lib src.zip {ASSEMBLY_EXCEPTION,LICENSE,THIRD_PARTY_README} $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}
  cp -a jre/bin jre/lib jre/{ASSEMBLY_EXCEPTION,LICENSE,THIRD_PARTY_README} $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}

  # Remove javaws man page
  rm -f man/man1/javaws*

  # Install man pages
  install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
  for manpage in man/man1/*
  do
    # Convert man pages to UTF8 encoding
    iconv -f ISO_8859-1 -t UTF8 $manpage -o $manpage.tmp
    mv -f $manpage.tmp $manpage
    install -m 644 -p $manpage $RPM_BUILD_ROOT%{_mandir}/man1/$(basename \
      $manpage .1)-%{uniquesuffix -- $suffix}.1
  done

  # Install demos and samples.
  cp -a demo $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  mkdir -p sample/rmi
  if [ ! -e sample/rmi/java-rmi.cgi ] ; then
    # hack to allow --short-circuit on install
    mv bin/java-rmi.cgi sample/rmi
  fi
  cp -a sample $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}

  popd

if ! echo $suffix | grep -q "debug" ; then
  # Install Javadoc documentation
  install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}
  cp -a ${docdir}/docs $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}
  built_doc_archive=jdk-%{javaver}_%{updatever}%{milestone_version}$suffix-%{buildver}-docs.zip
  cp -a ${docdir}/$built_doc_archive  $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}.zip
fi

# Install icons and menu entries
for s in 16 24 32 48 ; do
  install -D -p -m 644 \
    ${miscdir}/java-icon${s}.png \
    $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x${s}/apps/java-%{javaver}-%{origin}.png
done

# Install desktop files
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/{applications,pixmaps}
for e in jconsole$suffix policytool$suffix ; do
    desktop-file-install --vendor=%{uniquesuffix -- $suffix} --mode=644 \
        --dir=$RPM_BUILD_ROOT%{_datadir}/applications $e.desktop
done

# Install /etc/.java/.systemPrefs/ directory
# See https://bugzilla.redhat.com/show_bug.cgi?id=741821
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/.java/.systemPrefs

# FIXME: remove SONAME entries from demo DSOs. See
# https://bugzilla.redhat.com/show_bug.cgi?id=436497

# Find non-documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/sample \
  -type f -o -type l | sort \
  | grep -v README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  >> %{name}-demo.files"$suffix"
# Find documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/sample \
  -type f -o -type l | sort \
  | grep README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  | sed 's|^|%doc |' \
  >> %{name}-demo.files"$suffix"
# Find demo directories.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/sample \
  -type d | sort \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  | sed 's|^|%dir |' \
  >> %{name}-demo.files"$suffix"

# Create links which leads to separately installed java-atk-bridge and allow configuration
# links points to java-atk-wrapper - an dependence
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}
    ln -s %{_libdir}/java-atk-wrapper/libatk-wrapper.so.0 libatk-wrapper.so
  popd
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/ext
     ln -s %{_libdir}/java-atk-wrapper/java-atk-wrapper.jar  java-atk-wrapper.jar
  popd
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/
    echo "#Config file to  enable java-atk-wrapper" > accessibility.properties
    echo "" >> accessibility.properties
    echo "assistive_technologies=org.GNOME.Accessibility.AtkWrapper" >> accessibility.properties
    echo "" >> accessibility.properties
  popd


bash %{SOURCE22} $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix} %{javaver}
# https://bugzilla.redhat.com/show_bug.cgi?id=1183793
touch -t 201401010000 $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/security/java.security

# moving config files to /etc
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib/security/policy/unlimited/
mkdir -p $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/lib/security/policy/limited/
for file in lib/security/cacerts lib/security/policy/unlimited/US_export_policy.jar lib/security/policy/unlimited/local_policy.jar lib/security/policy/limited/US_export_policy.jar lib/security/policy/limited/local_policy.jar lib/security/java.policy lib/security/java.security lib/security/blacklisted.certs lib/logging.properties lib/calendars.properties lib/security/nss.cfg lib/security/nss.fips.cfg ; do
  mv      $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/$file   $RPM_BUILD_ROOT/%{etcjavadir -- $suffix}/$file
  ln -sf  %{etcjavadir -- $suffix}/$file                          $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/$file
done

# stabilize permissions
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "*.so" -exec chmod 755 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -type d -exec chmod 755 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "ASSEMBLY_EXCEPTION" -exec chmod 644 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "LICENSE" -exec chmod 644 {} \; ;
find $RPM_BUILD_ROOT/%{_jvmdir}/%{sdkdir -- $suffix}/ -name "THIRD_PARTY_README" -exec chmod 644 {} \; ;

# end, dual install
done

%if %{include_normal_build}
# intentionally only for non-debug
%pretrans headless -p <lua>
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1290388 for pretrans over pre
-- if copy-jdk-configs is in transaction, it installs in pretrans to temp
-- if copy_jdk_configs is in temp, then it means that copy-jdk-configs is in transaction  and so is
-- preferred over one in %%{_libexecdir}. If it is not in transaction, then depends
-- whether copy-jdk-configs is installed or not. If so, then configs are copied
-- (copy_jdk_configs from %%{_libexecdir} used) or not copied at all
local posix = require "posix"

if (os.getenv("debug") == "true") then
  debug = true;
  print("cjc: in spec debug is on")
else
  debug = false;
end

SOURCE1 = "%{rpm_state_dir}/copy_jdk_configs.lua"
SOURCE2 = "%{_libexecdir}/copy_jdk_configs.lua"

local stat1 = posix.stat(SOURCE1, "type");
local stat2 = posix.stat(SOURCE2, "type");

  if (stat1 ~= nil) then
  if (debug) then
    print(SOURCE1 .." exists - copy-jdk-configs in transaction, using this one.")
  end;
  package.path = package.path .. ";" .. SOURCE1
else
  if (stat2 ~= nil) then
  if (debug) then
    print(SOURCE2 .." exists - copy-jdk-configs already installed and NOT in transaction. Using.")
  end;
  package.path = package.path .. ";" .. SOURCE2
  else
    if (debug) then
      print(SOURCE1 .." does NOT exists")
      print(SOURCE2 .." does NOT exists")
      print("No config files will be copied")
    end
  return
  end
end
arg = nil ;  -- it is better to null the arg up, no meter if they exists or not, and use cjc as module in unified way, instead of relaying on "main" method during require "copy_jdk_configs.lua"
cjc = require "copy_jdk_configs.lua"
args = {"--currentjvm", "%{uniquesuffix %{nil}}", "--jvmdir", "%{_jvmdir %{nil}}", "--origname", "%{name}", "--origjavaver", "%{javaver}", "--arch", "%{_arch}", "--temp", "%{rpm_state_dir}/%{name}.%{_arch}"}
cjc.mainProgram(args)

%post
%{post_script %{nil}}

%post headless
%{post_headless %{nil}}

%postun
%{postun_script %{nil}}

%postun headless
%{postun_headless %{nil}}

%posttrans
%{posttrans_script %{nil}}

%posttrans headless
%{alternatives_java_install %{nil}}

%post devel
%{post_devel %{nil}}

%postun devel
%{postun_devel %{nil}}

%posttrans  devel
%{posttrans_devel %{nil}}

%posttrans javadoc
%{alternatives_javadoc_install %{nil}}

%postun javadoc
%{postun_javadoc %{nil}}

%posttrans javadoc-zip
%{alternatives_javadoczip_install %{nil}}

%postun javadoc-zip
%{postun_javadoc_zip %{nil}}
%endif

%if %{include_debug_build}
%post slowdebug
%{post_script -- %{debug_suffix_unquoted}}

%post headless-slowdebug
%{post_headless -- %{debug_suffix_unquoted}}

%posttrans headless-slowdebug
%{alternatives_java_install -- %{debug_suffix_unquoted}}

%postun slowdebug
%{postun_script -- %{debug_suffix_unquoted}}

%postun headless-slowdebug
%{postun_headless -- %{debug_suffix_unquoted}}

%posttrans slowdebug
%{posttrans_script -- %{debug_suffix_unquoted}}

%post devel-slowdebug
%{post_devel -- %{debug_suffix_unquoted}}

%postun devel-slowdebug
%{postun_devel -- %{debug_suffix_unquoted}}

%posttrans  devel-slowdebug
%{posttrans_devel -- %{debug_suffix_unquoted}}

%endif

%if %{include_fastdebug_build}
%post fastdebug
%{post_script -- %{fastdebug_suffix_unquoted}}

%post headless-fastdebug
%{post_headless -- %{fastdebug_suffix_unquoted}}

%postun fastdebug
%{postun_script -- %{fastdebug_suffix_unquoted}}

%postun headless-fastdebug
%{postun_headless -- %{fastdebug_suffix_unquoted}}

%posttrans fastdebug
%{posttrans_script -- %{fastdebug_suffix_unquoted}}

%posttrans headless-fastdebug
%{alternatives_java_install -- %{fastdebug_suffix_unquoted}}

%post devel-fastdebug
%{post_devel -- %{fastdebug_suffix_unquoted}}

%postun devel-fastdebug
%{postun_devel -- %{fastdebug_suffix_unquoted}}

%posttrans  devel-fastdebug
%{posttrans_devel -- %{fastdebug_suffix_unquoted}}

%endif

%if %{include_normal_build}
%files
# main package builds always
%{files_jre %{nil}}
%if %is_system_jdk
%ghost %{_bindir}/policytool
%endif
%else
%files
# placeholder
%endif


%if %{include_normal_build}
%files headless
# important note, see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
# all config/noreplace files (and more) have to be declared in pretrans. See pretrans
%{files_jre_headless %{nil}}
# RHEL-11313; alternatives not owned by packages
%if %is_system_jdk
%ghost %{_bindir}/java
%ghost %{_jvmdir}/jre
%ghost %{_bindir}/%{alt_java_name}
%ghost %{_bindir}/jjs
%ghost %{_bindir}/keytool
%ghost %{_bindir}/orbd
%ghost %{_bindir}/pack200
%ghost %{_bindir}/rmid
%ghost %{_bindir}/rmiregistry
%ghost %{_bindir}/servertool
%ghost %{_bindir}/tnameserv
%ghost %{_bindir}/unpack200
%ghost %{_jvmdir}/jre-%{origin}
%ghost %{_jvmdir}/jre-%{javaver}
%ghost %{_jvmdir}/jre-%{javaver}-%{origin}
%endif

%files devel
%{files_devel %{nil}}
# RHEL-11313; alternatives not owned by packages
%if %is_system_jdk
%ghost %{_bindir}/javac
%ghost %{_jvmdir}/java
%ghost %{_bindir}/appletviewer
%ghost %{_bindir}/clhsdb
%ghost %{_bindir}/extcheck
%ghost %{_bindir}/hsdb
%ghost %{_bindir}/idlj
%ghost %{_bindir}/jar
%ghost %{_bindir}/jarsigner
%ghost %{_bindir}/javadoc
%ghost %{_bindir}/javah
%ghost %{_bindir}/javap
%ghost %{_bindir}/jcmd
%ghost %{_bindir}/jconsole
%ghost %{_bindir}/jdb
%ghost %{_bindir}/jdeps
%ghost %{_bindir}/jfr
%ghost %{_bindir}/jhat
%ghost %{_bindir}/jinfo
%ghost %{_bindir}/jmap
%ghost %{_bindir}/jps
%ghost %{_bindir}/jrunscript
%ghost %{_bindir}/jsadebugd
%ghost %{_bindir}/jstack
%ghost %{_bindir}/jstat
%ghost %{_bindir}/jstatd
%ghost %{_bindir}/native2ascii
%ghost %{_bindir}/rmic
%ghost %{_bindir}/schemagen
%ghost %{_bindir}/serialver
%ghost %{_bindir}/wsgen
%ghost %{_bindir}/wsimport
%ghost %{_bindir}/xjc
%ghost %{_jvmdir}/java-%{origin}
%ghost %{_jvmdir}/java-%{javaver}
%ghost %{_jvmdir}/java-%{javaver}-%{origin}
%endif

%files demo -f %{name}-demo.files
%{files_demo %{nil}}

%files src
%{files_src %{nil}}

%files javadoc
%{files_javadoc %{nil}}
# RHEL-11313; alternatives not owned by packages
%if %is_system_jdk
%ghost %{_javadocdir}/java
%endif

# This puts a huge documentation file in /usr/share
# It is now architecture-dependent, as eg. AOT and Graal are now x86_64 only
# same for debug variant
%files javadoc-zip
%{files_javadoc_zip %{nil}}
# RHEL-11313; alternatives not owned by packages
%if %is_system_jdk
%ghost %{_javadocdir}/java-zip
%endif

%files accessibility
%{files_accessibility %{nil}}
%endif

%if %{include_debug_build}
%files slowdebug
%{files_jre -- %{debug_suffix_unquoted}}

%files headless-slowdebug
%{files_jre_headless -- %{debug_suffix_unquoted}}

%files devel-slowdebug
%{files_devel -- %{debug_suffix_unquoted}}

%files demo-slowdebug -f %{name}-demo.files-slowdebug
%{files_demo -- %{debug_suffix_unquoted}}

%files src-slowdebug
%{files_src -- %{debug_suffix_unquoted}}

%files accessibility-slowdebug
%{files_accessibility -- %{debug_suffix_unquoted}}
%endif

%if %{include_fastdebug_build}
%files fastdebug
%{files_jre -- %{fastdebug_suffix_unquoted}}

%files headless-fastdebug
%{files_jre_headless -- %{fastdebug_suffix_unquoted}}

%files devel-fastdebug
%{files_devel -- %{fastdebug_suffix_unquoted}}

%files demo-fastdebug -f %{name}-demo.files-fastdebug
%{files_demo -- %{fastdebug_suffix_unquoted}}

%files src-fastdebug
%{files_src -- %{fastdebug_suffix_unquoted}}

%files accessibility-fastdebug
%{files_accessibility -- %{fastdebug_suffix_unquoted}}
%endif

%changelog
* Mon Oct 21 2024 Jonathan Dieter <jdieter@ciq.com> - 1.8.0.432.b06-2.el8_8
- Fix build for 8.8 LTS

* Wed Oct 16 2024 Release Engineering <releng@rockylinux.org> - 1.8.0.432.b06-2
- Build for Rocky Linux %{rocky} using our own portable

* Fri Oct 11 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.432.b06-1
- Update to shenandoah-jdk8u432-b06 (GA)
- Update release notes for shenandoah-8u432-b06.
- Drop JDK-828109{6,7,8}/PR3836 patch following integration of upstream version
- Regenerate JDK-8199936/PR3533 patch following JDK-828109{6,7,8} integration
- Bump version of bundled zlib to 1.3.1 following JDK-8324632
- Include backport of JDK-8328999 to update giflib to 5.2.2
- Bump version of bundled giflib to 5.2.2 following JDK-8328999
- Add build scripts to repository to ease remembering all CentOS & RHEL targets and options
- Sync the copy of the portable specfile with the latest update
- Resolves: RHEL-58791
- Resolves: RHEL-62278
- Resolves: RHEL-61285
- ** This tarball is embargoed until 2024-10-15 @ 1pm PT. **

* Wed Jul 10 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.422.b05-1
- Update to shenandoah-jdk8u422-b05 (GA)
- Update release notes for shenandoah-8u422-b05.
- Rebase PR2462 patch following patched hunk being removed by JDK-8322106
- Switch to GA mode.
- Sync the copy of the portable specfile with the latest update
- Actually require tzdata 2024a now it is available in the buildroot
- Add missing build dependencies on zlib-devel and tar
- Update LCMS version to match JDK-8245400
- ** This tarball is embargoed until 2024-07-16 @ 1pm PT. **
- Resolves: RHEL-46866
- Resolves: RHEL-47001

* Tue Jul 09 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.422.b01-0.1.ea
- Update to shenandoah-jdk8u422-b01 (EA)
- Update release notes for shenandoah-8u422-b01.
- Switch to EA mode.
- Sync the copy of the portable specfile with the latest update
- Restore NEWS file and rename remove-intree-libraries.sh so portable can be rebuilt
- Document policy repacking script and rename to correct spelling and style
- Limit Java only tests to one architecture using jdk_test_arch
- Related: RHEL-46866
- Resolves: RHEL-47067
- Resolves: RHEL-47087

* Mon Apr 08 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.412.b08-2
- Update to shenandoah-jdk8u412-b08 (GA)
- Update release notes for shenandoah-8u412-b08.
- Complete release note for Certainly roots
- Switch to GA mode.
- Sync the copy of the portable specfile with the latest update
- ** This tarball is embargoed until 2024-04-16 @ 1pm PT. **
- Resolves: RHEL-32396

* Fri Apr 05 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.412.b07-0.2.ea
- Update to shenandoah-jdk8u412-b07 (EA)
- Require tzdata 2024a due to upstream inclusion of JDK-8322725
- Only require tzdata 2023d for now as 2024a is unavailable in buildroot
- Sync the copy of the portable specfile with the latest update
- Related: RHEL-30931

* Fri Mar 22 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.412.b01-0.2.ea
- Turn off xz multi-threading on i686 as it fails with an out of memory error
- Move to upstream tag style (shenandoah8ux-by) in preparation for eventually moving back to official sources
- generate_source_tarball.sh: Rename JCONSOLE_JS_PATCH{,_DEFAULT} to JCONSOLE_PATCH{,_DEFAULT} for brevity
- generate_source_tarball.sh: Adapt OPENJDK_LATEST logic to work with 8u Shenandoah fork
- generate_source_tarball.sh: Adapt version logic to work with 8u
- generate_source_tarball.sh: Add quoting for SCRIPT_DIR and JCONSOLE_PATCH (SC2086)
- generate_source_tarball.sh: Update examples in header for clarity
- generate_source_tarball.sh: Create directory in TMPDIR when using WITH_TEMP
- generate_source_tarball.sh: Only add --depth=1 on non-local repositories
- Move maintenance scripts to a scripts subdirectory
- icedtea_sync.sh: Update with a VCS mode that retrieves sources from a Mercurial repository
- discover_trees.sh: Set compile-command and indentation instructions for Emacs
- discover_trees.sh: shellcheck: Do not use -o (SC2166)
- discover_trees.sh: shellcheck: Remove x-prefixes since we use Bash (SC2268)
- discover_trees.sh: shellcheck: Double-quote variable references (SC2086)
- generate_source_tarball.sh: Add authorship
- icedtea_sync.sh: Set compile-command and indentation instructions for Emacs
- icedtea_sync.sh: shellcheck: Double-quote variable references (SC2086)
- icedtea_sync.sh: shellcheck: Remove x-prefixes since we use Bash (SC2268)
- openjdk_news.sh: Set compile-command and indentation instructions for Emacs
- openjdk_news.sh: shellcheck: Double-quote variable references (SC2086)
- openjdk_news.sh: shellcheck: Remove x-prefixes since we use Bash (SC2268)
- openjdk_news.sh: shellcheck: Remove deprecated egrep usage (SC2196)
- Remove obsolete file generate_singlerepo_source_tarball.sh
- Remove obsolete file get_sources.sh
- Remove obsolete file update_main_sources.sh
- generate_source_tarball.sh: Handle an existing checkout
- generate_source_tarball.sh: Sync indentation with java-21-openjdk version
- generate_source_tarball.sh: Support using a subdirectory via TO_COMPRESS
- Sync patch set with portable build
- Related: RHEL-30931

* Fri Mar 22 2024 Thomas Fitzsimmons <fitzsim@redhat.com> - 1:1.8.0.412.b01-0.2.ea
- Invoke xz in multi-threaded mode
- generate_source_tarball.sh: Add WITH_TEMP environment variable
- generate_source_tarball.sh: Multithread xz on all available cores
- generate_source_tarball.sh: Add OPENJDK_LATEST environment variable
- generate_source_tarball.sh: Update comment about tarball naming
- generate_source_tarball.sh: Reformat comment header
- generate_source_tarball.sh: Reformat and update help output
- generate_source_tarball.sh: Do a shallow clone, for speed
- generate_source_tarball.sh: Eliminate some removal prompting
- generate_source_tarball.sh: Make tarball reproducible
- generate_source_tarball.sh: Prefix temporary directory with temp-
- generate_source_tarball.sh: Remove temporary directory exit conditions
- generate_source_tarball.sh: Set compile-command in Emacs
- generate_source_tarball.sh: Remove REPO_NAME from FILE_NAME_ROOT
- generate_source_tarball.sh: Move PROJECT_NAME and REPO_NAME checks
- generate_source_tarball.sh: shellcheck: Remove x-prefixes since we use Bash (SC2268)
- generate_source_tarball.sh: shellcheck: Double-quote variable references (SC2086)
- generate_source_tarball.sh: shellcheck: Do not use -a (SC2166)
- generate_source_tarball.sh: shellcheck: Do not use $ on arithmetic variables (SC2004)
- Use backward-compatible patch syntax
- generate_source_tarball.sh: Ignore -ga tags with OPENJDK_LATEST
- generate_source_tarball.sh: Remove trailing period in echo
- generate_source_tarball.sh: Use long-style argument to grep
- generate_source_tarball.sh: Add license
- generate_source_tarball.sh: Add indentation instructions for Emacs
- Related: RHEL-30931

* Thu Mar 21 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.412.b01-0.2.ea
- Update to shenandoah-jdk8u412-b01 (EA)
- Switch to EA mode.
- Related: RHEL-30931

* Thu Jan 11 2024 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.402.b06-0.2.ea
- Update to shenandoah-jdk8u402-b06 (GA)
- Sync the copy of the portable specfile with the latest update
- Drop local copy of JDK-8312489 which is now included upstream
- ** This tarball is embargoed until 2024-01-16 @ 1pm PT. **
- Resolves: RHEL-21477
- Resolves: RHEL-20975

* Sat Dec 16 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.392.b08-5
- Restore %%{epoch}:%%{javaver} versioning to jre, java, jre-headless, java-headless, java-devel & java-sdk
- Resolves: RHEL-19636

* Mon Oct 16 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.392.b08-4
- Revert jcmd move as jcmd will not operate without tools.jar
- Related: RHEL-13612

* Mon Oct 16 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.392.b08-3
- Add a compatibility symlink from bin/jcmd to jre/bin/jcmd
- Related: RHEL-13612

* Tue Oct 10 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.392.b08-2
- Update to shenandoah-jdk8u392-b08 (GA)
- Sync the copy of the portable specfile with the latest update
- Update generate_tarball.sh to be closer to upstream vanilla script inc. no more ECC removal
- Update bug URL for RHEL to point to the Red Hat customer portal
- Change top_level_dir_name to use the VCS tag, matching new upstream release style tarball
- Regenerate PR2462 patch following JDK-8315135
- Bump version of bundled libpng to 1.6.39
- Add backport of JDK-8312489 heading upstream for 8u402 (see OPENJDK-2095)
- Add missing JFR, alt-java, jre-* and java-* alternative ghosts
- Move jcmd to the headless package
- ** This tarball is embargoed until 2023-10-17 @ 1pm PT. **
- Resolves: RHEL-12309
- Resolves: RHEL-13600
- Resolves: RHEL-13628
- Resolves: RHEL-13635
- Resolves: RHEL-13641
- Resolves: RHEL-13612
- Resolves: RHEL-13621

* Tue Oct 10 2023 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.392.b08-1
- For non debug subpackages, ghosted all alternatives (rhbz1649776)
- For non system JDKs, if-outed versionless provides.
- Aligned versions to be %%{epoch}:%%{version}-%%{release} instead of chaotic
- Related: RHEL-13641

* Wed Jul 19 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.382.b05-2
- Bump release number so we are newer than 8.6
- Related: rhbz#2221106

* Fri Jul 14 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.382.b05-1
- Update to shenandoah-jdk8u372-b05 (GA)
- Sync the copy of the portable specfile with the latest update
- Add note at top of spec file about rebuilding
- Use tapsets from the misc tarball
- Make sure root installation directory is created first
- Use in-place substitution for all but the first of the tapset changes
- The 'prelease' variable should refer to 'portablerelease', not 'rpmrelease'
- ** This tarball is embargoed until 2023-07-18 @ 1pm PT. **
- Resolves: rhbz#2221106

* Fri Jul 07 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.382.b04-0.1.ea
- Update to shenandoah-jdk8u382-b04 (EA)
- Sync the copy of the portable specfile with the latest update
- Resolves: rhbz#2217710

* Wed Jul 05 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.382.b01-0.1.ea
- Update to shenandoah-jdk8u382-b01 (EA)
- Switch to EA mode.
- Remove JDK-8271199 patch which is now upstream.
- Add version of bundled zlib (bumped from 1.2.11 to 1.2.13 with this update)
- Introduce 'prelease' for the portable release versioning, to handle EA builds
- Sync the copy of the portable specfile with the latest update
- Related: rhbz#2217710

* Thu Apr 27 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.372.b07-4
- Include the java-1.8.0-openjdk-portable.spec file with instructions on how to rebuild.
- Remove duplicate use of README.md inside the *-src package (it is no longer about sources)
- Related: rhbz#2189328

* Thu Apr 27 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.372.b07-3
- Revert "Restore native build for x86 as there is no portable build"
- Retain portable_build-arches with x86-32 added for reference
- Remove NEWS.
- Related: rhbz#2189328

* Tue Apr 18 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.372.b07-2
- Update to shenandoah-jdk8u372-b07 (GA)
- Update release notes for shenandoah-8u372-b07.
- Require tzdata 2023c due to inclusion of JDK-8305113 in 8u372-b07
- Update generate_tarball.sh to add support for passing a boot JDK to the configure run
- Add POSIX-friendly error codes to generate_tarball.sh and fix whitespace
- Remove .jcheck and GitHub support when generating tarballs, as done in upstream release tarballs
- Drop JDK-8275535/RH2053256 patch which is now upstream
- Include JDK-8271199 backport early ahead of 8u382 (RH2175317)
- Drop hack for difference in local and portable build version
- Replace local copies of JDK portable binaries with build dependencies
- ** This tarball is embargoed until 2023-04-18 @ 1pm PT. **
- Resolves: rhbz#2185182
- Resolves: rhbz#2189328

* Tue Feb 28 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.362.b09-4
- On portable architectures, replace build section with extraction of existing builds from portables
- Rewrite ELF files so the source file path is correct and debugsources can be assembled
- Resolves: rhbz#2150203

* Tue Jan 24 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.362.b09-3
- Update cacerts patch to fix OPENJDK-1433 SecurityManager issue
- Update to shenandoah-jdk8u352-b09 (GA)
- Update release notes for shenandoah-8u352-b09.
- Resolves: rhbz#2162715

* Fri Jan 13 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.362.b08-3
- Update to shenandoah-jdk8u352-b08 (GA)
- Update release notes for shenandoah-8u352-b08.
- Fix broken links and missing release notes in older releases.
- Drop RH1163501 patch which is not upstream or in 11, 17 & 19 packages and seems obsolete
  - Patch was broken by inclusion of "JDK-8293554: Enhanced DH Key Exchanges"
  - Patch was added for a specific corner case of a 4096-bit DH key on a Fedora host that no longer exists
  - Fedora now appears to be using RSA and the JDK now supports ECC in preference to large DH keys
- Resolves: rhbz#2160111

* Wed Jan 11 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.362.b07-0.3.ea
- Update to shenandoah-jdk8u362-b07 (EA)
- Update release notes for shenandoah-8u362-b07.
- Require tzdata 2022g due to inclusion of JDK-8296108, JDK-8296715 & JDK-8297804
- Drop tzdata patches for 2022d & 2022e (JDK-8294357 & JDK-8295173) which are now upstream
- Update TestTranslations.java to test the new America/Ciudad_Juarez zone
- Drop JDK-8255559/RH2124390 patch which is now upstream
- Resolves: rhbz#2150193

* Tue Jan 10 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.362.b01-0.3.ea
- Update to shenandoah-jdk8u362-b01 (EA)
- Update release notes for shenandoah-8u362-b01.
- Switch to EA mode for 8u362 pre-release builds.
- Drop JDK-8195607/PR3776/RH1760437 now this is upstream
- Related: rhbz#2150193

* Thu Nov 10 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.352.b08-3
- Add backport of JDK-8255559 to fix file descriptor leak in XML code
- Resolves: rhbz#2124390

* Wed Oct 19 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.352.b08-2
- Update to shenandoah-jdk8u352-b08 (GA)
- Update release notes for shenandoah-8u352-b08.
- Switch to GA mode for final release.
- Update in-tree tzdata to 2022e with JDK-8294357 & JDK-8295173
- Add test to ensure timezones can be translated
- Resolves: rhbz#2133695

* Wed Oct 12 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.352.b07-0.2.ea
- Update to shenandoah-jdk8u352-b07 (EA)
- Update release notes for shenandoah-8u352-b07.
- Switch to EA mode for 8u352 pre-release builds.
- Rebase FIPS patch against 8u352-b07
- Resolves: rhbz#2130612

* Tue Aug 30 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.345.b01-5
- Switch to static builds, reducing system dependencies and making build more portable
- Resolves: rhbz#2048542

* Tue Aug 30 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.345.b01-4
- Sync system cacerts support with RHEL 9, disabling using -Dsecurity.systemCACerts=
- Move cacerts replacement to install section and retain original of this and tzdb.dat
- Related: rhbz#2055274

* Mon Aug 29 2022 Stephan Bergmann <sbergman@redhat.com> - 1:1.8.0.345.b01-3
- Disable copy-jdk-configs for Flatpak builds
- Fix flatpak builds by exempting them from bootstrap
- Resolves: rhbz#2102733

* Wed Aug 03 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.345.b01-2
- Update to shenandoah-jdk8u345-b01 (GA)
- Update release notes for 8u345-b01.
- Resolves: rhbz#2112403

* Sun Jul 24 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.342.b07-2
- Update to shenandoah-jdk8u342-b07 (GA)
- Update release notes for 8u342-b07.
- Switch to GA mode for final release.
- Resolves: rhbz#2106507

* Sun Jul 17 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.342.b06-0.1.ea
- Update to shenandoah-jdk8u342-b06 (EA)
- Update release notes for shenandoah-8u342-b06.
- Switch to EA mode for 8u342 pre-release builds.
- Print release file during build, which should now include a correct SOURCE value from .src-rev
- Update tarball script with IcedTea GitHub URL and .src-rev generation
- Use "git apply" with patches in the tarball script to allow binary diffs
- Remove redundant "REPOS" variable from tarball script
- Include script to generate bug list for release notes
- Update tzdata requirement to 2022a to match JDK-8283350
- Resolves: rhbz#2083265

* Sun Jul 17 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.332.b09-5
- Rebase FIPS patches from fips branch and simplify by using a single patch from that repository
- * RH2036462: sun.security.pkcs11.wrapper.PKCS11.getInstance breakage
- * RH2090378: Revert to disabling system security properties and FIPS mode support together
- Rebase RH1648249 nss.cfg patch so it applies after the FIPS patch
- Rebase PR2888/RH2055274 cacerts patch so it applies after the current FIPS patch
- Perform configuration changes (e.g. nss.cfg, nss.fips.cfg, tzdb.dat) in installjdk
- Enable system security properties in the RPM (now disabled by default in the FIPS repo)
- Improve security properties test to check both enabled and disabled behaviour
- Run security properties test with property debugging on
- Explicitly require crypto-policies during build and runtime for system security properties
- Resolves: rhbz#2097152
- Resolves: rhbz#2100675

* Thu Jun 30 2022 Francisco Ferrari Bihurriet <fferrari@redhat.com> - 1:1.8.0.332.b09-4
- RH2007331: SecretKey generate/import operations don't add the CKA_SIGN attribute in FIPS mode
- Resolves: rhbz#2102431

* Mon Apr 18 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.332.b09-3
- Update to shenandoah-jdk8u332-b09 (GA)
- Update release notes for 8u332-b09.
- Switch to GA mode for final release.
- Resolves: rhbz#2074646

* Mon Apr 18 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.332.b06-0.2.ea
- Allow the default keystore to be configured using security.systemCACerts
- Use of the property can now be disabled using -Djava.security.disableSystemCACerts=true
- Resolves: rhbz#2055274

* Mon Apr 18 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.332.b06-0.1.ea
- Update to shenandoah-jdk8u332-b06 (EA)
- Update release notes for shenandoah-8u332-b06.
- Resolves: rhbz#2047536

* Sun Apr 17 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.332.b01-0.1.ea
- Update to shenandoah-jdk8u332-b01 (EA)
- Update release notes for shenandoah-8u332-b01.
- Switch to EA mode.
- Remove JDK-8279077 patch now upstream.
- Related: rhbz#2047536

* Mon Feb 28 2022 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.322.b06-11
- Storing and restoring alterntives during update manually
- Fixing Bug 2001567 - update of JDK/JRE is removing its manually selected alterantives and select (as auto) system JDK/JRE
-- The move of alternatives creation to posttrans to fix:
-- Bug 1200302 - dnf reinstall breaks alternatives
-- Had caused the alternatives to be removed, and then created again,
-- instead of being added, and then removing the old, and thus persisting
-- the selection in family
-- Thus this fix, is storing the family of manually selected master, and if
-- stored, then it is restoring the family of the master
- Resolves: rhbz#2008192

* Mon Feb 28 2022 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.322.b06-10
- Family extracted to globals
- Resolves: rhbz#2008192

* Mon Feb 28 2022 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.322.b06-9
- javadoc-zip got its own provides next to plain javadoc ones
- Resolves: rhbz#2008192

* Mon Feb 28 2022 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.322.b06-8
- alternatives creation moved to posttrans
- Thus fixing the old reisntall issue:
- https://bugzilla.redhat.com/show_bug.cgi?id=1200302
- https://bugzilla.redhat.com/show_bug.cgi?id=1976053
- Resolves: rhbz#2008192

* Mon Feb 28 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-7
- Add JDK-8275535 patch to fix LDAP authentication issue.
- Resolves: rhbz#2053285

* Mon Feb 28 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-6
- Detect NSS at runtime for FIPS detection
- Turn off build-time NSS linking and go back to an explicit Requires on NSS
- Resolves: rhbz#2052828

* Wed Feb 23 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-5
- Separate crypto policy initialisation from FIPS initialisation, now they are no longer interdependent
- Resolves: rhbz#2052817

* Mon Feb 21 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-4
- Refactor build functions so we can build just HotSpot without any attempt at installation.
- Introduce architecture restriction logic for the gdb test. (RH2041970)
- Pass compiler flags to the ADLC build (JDK-8281098)
- Adjust JDK8199936/PR3533 -mstackrealign patch to instead pass -mincoming-stack-boundary=2 -mpreferred-stack-boundary=4
- Explicitly list JIT architectures rather than relying on those with slowdebug builds
- Disable the serviceability agent on Zero architectures even when the architecture itself is supported
- Add backport of JDK-8257794 to fix bogus assert on slowdebug x86-32 Zero builds
- Sync minor placement differences with Fedora & RHEL 9
- Resolves: rhbz#2022815

* Mon Jan 24 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-3
- Fix FIPS issues in native code and with initialisation of java.security.Security
- Resolves: rhbz#2021263

* Fri Jan 21 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b06-2
- Update to aarch64-shenandoah-jdk8u322-b06 (EA)
- Update release notes for 8u322-b06.
- Switch to GA mode for final release.
- Resolves: rhbz#2039366

* Thu Jan 20 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u322-b05 (EA)
- Update release notes for 8u322-b05.
- Require tzdata 2021e as of JDK-8275766.
- Update tarball generation script to use git following shenandoah-jdk8u's move to github
- Resolves: rhbz#2022815

* Tue Jan 18 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b04-0.2.ea
- Add backport of JDK-8279077 to fix crash on ppc64
- Resolves: rhbz#2030399

* Mon Jan 10 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u322-b04 (EA)
- Update release notes for 8u322-b04.
- Require tzdata 2021c as of JDK-8274407.
- Related: rhbz#2022815

* Fri Jan 07 2022 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u322-b03 (EA)
- Update release notes for 8u322-b03.
- Related: rhbz#2022815

* Fri Dec 17 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u322-b02 (EA)
- Update release notes for 8u322-b02.
- Related: rhbz#2022815

* Tue Dec 14 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.322.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u322-b01 (EA)
- Update release notes for 8u322-b01.
- Switch to EA mode.
- Related: rhbz#2022815

* Mon Dec 06 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b07-5
- Turn off bootstrapping for slow debug builds, which are particularly slow on ppc64le.
- Related: rhbz#2022815

* Mon Dec 06 2021 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.312.b07-4
- Use 'sql:' prefix in nss.fips.cfg as F35+ no longer ship the legacy
  secmod.db file as part of nss
- Resolves: rhbz#2023532

* Fri Oct 15 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b07-3
- Update to aarch64-shenandoah-jdk8u312-b07 (EA)
- Update release notes for 8u312-b07.
- Switch to GA mode for final release.
- Resolves: rhbz#2012339

* Tue Oct 12 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b05-0.3.ea
- Update to aarch64-shenandoah-jdk8u312-b05-shenandoah-merge-2021-10-07
- Update release notes for 8u312-b05-shenandoah-merge-2021-10-07.
- Related: rhbz#1999937

* Thu Oct 07 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b05-0.2.ea
- Allow plain key import to be disabled with -Dcom.redhat.fips.plainKeySupport=false
- Resolves: rhbz#1994659

* Thu Oct 07 2021 Martin Balao <mbalao@redhat.com> - 1:1.8.0.312.b05-0.2.ea
- Add patch to allow plain key import.
- Resolves: rhbz#1994659

* Thu Sep 30 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u312-b05 (EA)
- Update release notes for 8u312-b05.
- Resolves: rhbz#1999937

* Mon Sep 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b04-0.2.ea
- Reduce disk footprint by removing build artifacts by default.
- Related: rhbz#1999937

* Sun Sep 26 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u312-b04 (EA)
- Update release notes for 8u312-b04.
- Related: rhbz#1999937

* Fri Sep 24 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u312-b03 (EA)
- Update release notes for 8u312-b03.
- Related: rhbz#1999937

* Sun Sep 19 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u312-b02 (EA)
- Update release notes for 8u312-b02.
- Related: rhbz#1999937

* Mon Sep 13 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.312.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u312-b01 (EA)
- Update release notes for 8u312-b01.
- Switch to EA mode.
- Remove "-clean" suffix as no 8u312 builds are unclean.
- Related: rhbz#1999937

* Fri Sep 10 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b08-4
- Remove non-Free test and demo files from source tarball.
- Related: rhbz#1999937

* Fri Aug 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b08-3
- Add patch to login to the NSS software token when in FIPS mode.
- Resolves: rhbz#1997358

* Fri Aug 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b08-2
- Fix path to libsystemconf.so on 8u.
- Resolves: rhbz#1971679

* Fri Aug 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b08-2
- Port FIPS system detection support to OpenJDK 8u
- Minor code cleanups on FIPS detection patch and check for SECMOD_GetSystemFIPSEnabled in configure.
- Remove unneeded Requires on NSS as it will now be dynamically linked and detected by RPM.
- Resolves: rhbz#1971679

* Fri Aug 27 2021 Martin Balao <mbalao@redhat.com> - 1:1.8.0.302.b08-2
- Detect FIPS using SECMOD_GetSystemFIPSEnabled in the new libsystemconf JDK library.
- Resolves: rhbz#1971679

* Fri Jul 16 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b08-1
- Update to aarch64-shenandoah-jdk8u302-b08 (EA)
- Update release notes for 8u302-b08.
- Switch to GA mode for final release.
- This tarball is embargoed until 2021-07-20 @ 1pm PT.
- Resolves: rhbz#1972395

* Thu Jul 08 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b07-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b07 (EA)
- Update release notes for 8u302-b07.
- Resolves: rhbz#1967812

* Tue Jul 06 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b06-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b06 (EA)
- Update release notes for 8u302-b06.
- Resolves: rhbz#1967812

* Tue Jul 06 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b05-0.2.ea
- Remove restriction on disabling product build, as debug packages no longer have javadoc packages.
- Fix name of javadoc debug packages in Obsoletes declarations and add version where it was removed.
- Resolves: rhbz#1966233

* Mon Jul 05 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b05-0.1.ea
- Use the "reverse" build loop (debug first) as the main and only build loop to get more diagnostics.
- Resolves: rhbz#1966233

* Fri Jul 02 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b05-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b05 (EA)
- Update release notes for 8u302-b05.
- Resolves: rhbz#1967812

* Wed Jun 30 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b04-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b04 (EA)
- Update release notes for 8u302-b04.
- Resolves: rhbz#1967812

* Tue Jun 29 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b03-0.3.ea
- Introduced nm based check to verify alt-java on x86_64 is patched, and no other alt-java or java is patched
- Patch600, rh1750419-redhat_alt_java.patch, amended to die, if it is used wrongly
- Introduced ssbd_arches with currently only valid arch of x86_64 to separate real alt-java architectures
- Resolves: rhbz#1966233

* Mon Jun 28 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b03-0.2.ea
- Re-order source files to sync with Fedora.
- Resolves: rhbz#1966233

* Mon Jun 28 2021 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.302.b03-0.2.ea
- Add a test verifying system crypto policies can be disabled
- Resolves: rhbz#1966233

* Mon Jun 28 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u302-b03-shenandoah-merge-2021-06-23 (EA)
- Update release notes for 8u302-b03-shenandoah-merge-2021-06-23.
- Resolves: rhbz#1967812

* Sun Jun 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b03-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b03 (EA)
- Update release notes for 8u302-b03.
- Resolves: rhbz#1967812

* Sat Jun 26 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b02-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b02 (EA)
- Update release notes for 8u302-b02.
- Resolves: rhbz#1967812

* Mon Jun 21 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b01-0.3.ea
- Add ppc64le and aarch64 to fastdebug_arches
- Resolves: rhbz#1969254

* Fri Jun 18 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b01-0.2.ea
- Cleanup architecture handling in preparation for extending set of fastdebug architectures
- Fixed not-including fastdebug build in case of --without fastdebug
- Resolves: rhbz#1969254

* Wed Jun 16 2021 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.302.b01-0.1.ea
- adapted to newst cjc to fix issue with rpm 4.17
- Disable copy-jdk-configs for Flatpak builds
- removed cjc backward comaptiblity, to fix when both rpm 4.16 and 4.17 are in transaction
- Resolves: rhbz#1953923

* Sat May 22 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.302.b01-0.0.ea
- Update to aarch64-shenandoah-jdk8u302-b01 (EA)
- Update release notes for 8u302-b01.
- Switch to EA mode.
- Resolves: rhbz#1967812

* Tue Apr 13 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b10-2
- Update to aarch64-shenandoah-jdk8u292-b10 (GA)
- Update release notes for 8u292-b10.
- This tarball is embargoed until 2021-04-20 @ 1pm PT.
- Resolves: rhbz#1938201

* Tue Apr 13 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b09-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b09 (EA)
- Update release notes for 8u292-b09.
- Resolves: rhbz#1942306

* Mon Apr 12 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b08-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b08 (EA)
- Update release notes for 8u292-b08.
- Require tzdata 2021a due to JDK-8260356
- Resolves: rhbz#1942306

* Mon Apr 12 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b07-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b07 (EA)
- Update release notes for 8u292-b07.
- Resolves: rhbz#1942306

* Sun Apr 11 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b06-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b06 (EA)
- Update release notes for 8u292-b06.
- Require tzdata 2020f due to JDK-8259048
- Resolves: rhbz#1942306

* Sat Apr 10 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b05-0.3.ea
- Update to aarch64-shenandoah-jdk8u292-b05-shenandoah-merge-2021-03-11 (EA)
- Update release notes for 8u292-b05-shenandoah-merge-2021-03-11.
- Re-organise S/390 patches for upstream submission, separating 8u upstream from Shenandoah fixes.
- Add new formatting case found in memprofiler.cpp on debug builds to PR3593 patch.
- Extend s390 patch to fix issue caused by JDK-8252660 backport and lack of JDK-8188813 in 8u.
- Revise JDK-8252660 s390 failure to make _soft_max_size a jlong so pointer types are accurate.
- Resolves: rhbz#1942306

* Fri Apr 09 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b05-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b05 (EA)
- Update release notes for 8u292-b05.
- Resolves: rhbz#1942306

* Fri Apr 09 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b04-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b04 (EA)
- Update release notes for 8u292-b04.
- Resolves: rhbz#1942306

* Fri Apr 09 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b03-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b03 (EA)
- Update release notes for 8u292-b03.
- Resolves: rhbz#1942306

* Sat Mar 27 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b02-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b02 (EA)
- Update release notes for 8u292-b02.
- Remove RH1868759 patch as this is now resolved upstream by JDK-8258833.
- Resolves: rhbz#1942306

* Thu Mar 25 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.292.b01-0.2.ea
- Update to aarch64-shenandoah-jdk8u292-b01 (EA)
- Update release notes for 8u292-b01.
- Switch to EA mode.
- Update tarball generation script to use PR3822 which handles
    JDK-8233228 & JDK-8035166 changes
- Resolves: rhbz#1942306

* Wed Feb 17 2021 Stephan Bergmann <sbergman@redhat.com> - 1:1.8.0.282.b08-4
- Resolves: rhbz#1896014 Hardcode /usr/sbin/alternatives for Flatpak builds

* Sun Jan 17 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b08-3
- Cleanup package descriptions and version number placement.
- Resolves: rhbz#1908967

* Sun Jan 17 2021 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.282.b08-3
- Fix typo in variable
- Resolves: rhbz#1908967

* Sun Jan 17 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b08-2
- Add explicit runtime dependency on NSS for the PKCS11 provider in FIPS mode
- Resolves: rhbz#1913868

* Fri Jan 15 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b08-1
- Update to aarch64-shenandoah-jdk8u282-b08 (GA)
- Update release notes for 8u282-b08.
- Resolves: rhbz#1908967

* Fri Jan 15 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b07-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b07 (EA)
- Update release notes for 8u282-b07.
- Fix placement issue in release notes, caught by comparing with vanilla version.
- Resolves: rhbz#1903904

* Wed Jan 13 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b06-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b06 (EA)
- Update release notes for 8u282-b06.
- Resolves: rhbz#1903904

* Mon Jan 11 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b05 (EA)
- Update release notes for 8u282-b05 and make some minor corrections.
- Resolves: rhbz#1903904

* Wed Jan 06 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b04 (EA)
- Update release notes for 8u282-b04.
- Remove upstreamed patch PR3519
- Resolves: rhbz#1903904

* Sat Jan 02 2021 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b03 (EA)
- Update release notes for 8u282-b03.
- Resolves: rhbz#1903904

* Fri Dec 18 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b02-0.2.ea
- Move setup of JavaSecuritySystemConfiguratorAccess to Security class so it always occurs.
- Resolves: rhbz#1906862

* Wed Dec 16 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b02 (EA)
- Update release notes for 8u282-b02.
- Resolves: rhbz#1903904

* Mon Dec 07 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.282.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u282-b01 (EA)
- Update release notes for 8u282-b01.
- Switch to EA mode.
- Require tzdata 2020b due to resource changes in JDK-8254177
- Remove PR3601, covered upstream by JDK-8062808.
- Remove upstreamed JDK-8197981/PR3548, JDK-8062808/PR3548, JDK-8254177 & JDK-8215727.
- Extend RH1750419 alt-java fix to include external debuginfo, following JDK-8252395
- Resolves: rhbz#1903904

* Fri Nov 27 2020 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.275.b01-3
- added patch600, rh1750419-redhat_alt_java.patch
- Replaced alt-java palceholder by real pathced alt-java
- remove patch529 rh1566890-CVE_2018_3639-speculative_store_bypass.patch
- remove patch531 rh1566890-CVE_2018_3639-speculative_store_bypass_toggle.patch
- both suprassed by new patch
- Resolves: rhbz#1750419

* Fri Nov 06 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.275.b01-2
- Update to aarch64-shenandoah-jdk8u275-b01 (GA)
- Update release notes for 8u275.
- Remove JDK-8223940/RH1892216 backport now included in upstream 8u275.
- Remove JDK-8236512/RH1889414 backport now included in upstream 8u275.
- Resolves: rhbz#1895060

* Fri Oct 30 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b10-6
- Add backport of JDK-8223940: "Private key not supported by chosen signature algorithm" to handle lack of provider RSAPSS support
- Resolves: rhbz#1892216

* Fri Oct 30 2020 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.272.b10-5
- Added gating test for ipa server
- Resolves: rhbz#1892216

* Thu Oct 29 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b10-4
- Bump release number to build on RHEL 8.4.0 branch.
- Resolves: rhbz#1876665
- Resolves: rhbz#1889414

* Wed Oct 21 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b10-3
- Add backport of JDK-8236512 to correct use of killSession
- Resolves: rhbz#1889414

* Tue Oct 20 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b10-2
- Add backport of JDK-8215727: "Restore JFR thread sampler loop to old / previous behaviour"
- Resolves: rhbz#1876665

* Sat Oct 17 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b10-1
- Update to aarch64-shenandoah-jdk8u272-b10.
- Switch to GA mode for final release.
- Update release notes for 8u272 release.
- Add backport of JDK-8254177 to update to tzdata 2020b
- Require tzdata 2020b due to resource changes in JDK-8254177
- Delay tzdata 2020b dependency until tzdata update has shipped.
- Adjust JDK-8062808/PR3548 following constantPool.hpp context change in JDK-8243302
- Adjust PR3593 following g1StringDedupTable.cpp context change in JDK-8240124 & JDK-8244955
- This tarball is embargoed until 2020-10-20 @ 1pm PT.
- Resolves: rhbz#1876665

* Thu Oct 15 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b09-0.2.ea
- Include a test in the RPM to check the build has the correct vendor information.
- Use 'oj_' prefix on new vendor globals to avoid a conflict with RPM's vendor value.
- Improve quoting of vendor name
- Resolves: rhbz#1876665

* Thu Oct 15 2020 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.272.b09-0.2.ea
- Set vendor property and vendor URLs
- Made URLs to be preconfigured by OS
- Resolves: rhbz#1876665

* Wed Oct 14 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b09-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b09 (EA).
- Resolves: rhbz#1876665

* Tue Oct 13 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b08-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b08 (EA).
- Resolves: rhbz#1876665

* Tue Oct 13 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b07-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b07 (EA).
- Resolves: rhbz#1876665

* Mon Oct 12 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b06-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b06.
- Update tarball generation script to use PR3799, following inclusion of JDK-8245468 (TLSv1.3)
- Remove JDK-8165996/PR3506/RH1760437 & JDK-8251117/RH1860990 as now applied upstream.
- Replace JDK-8223482/RH1860965 with RH1860986 (disable TLSv1.3 when using the NSS-FIPS provider)
- Resolves: rhbz#1876665

* Mon Oct 12 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b05-0.3.ea
- Enable JFR on x86, now we have JDK-8252096: Shenandoah: adjust SerialPageShiftCount for x86_32 and JFR
- Resolves: rhbz#1876665

* Thu Oct 08 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b05-0.2.ea
- Update to aarch64-shenandoah-jdk8u272-b05-shenandoah-merge-2020-08-28.
- Add additional s390 log2_intptr case in shenandoahUtils.cpp introduced by JDK-8245464
- Resolves: rhbz#1876665

* Thu Oct 08 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b05.
- Add additional s390 size_t case in g1ConcurrentMarkObjArrayProcessor.cpp introduced by JDK-8057003
- Resolves: rhbz#1876665

* Wed Oct 07 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b04.
- Update tarball generation script to use PR3795, following inclusion of JDK-8177334
- Resolves: rhbz#1876665

* Mon Oct 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b03.
- Resolves: rhbz#1876665

* Mon Oct 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b02.
- Remove JDK-8154313 backport now applied upstream.
- Change target from 'zip-docs' to 'docs-zip', which is the naming used upstream.
- Resolves: rhbz#1876665

* Mon Oct 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.272.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u272-b01.
- Switch to EA mode.
- Add debugging output for build.
- JFR must now be explicitly disabled when unwanted (e.g. x86), following switch of upstream default.
- Resolves: rhbz#1876665

* Thu Sep 17 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.265.b01-4
- Add patch to cancel PKCS#11 operations on failure (RH1868759)
- Resolves: rhbz#1868759

* Tue Aug 25 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.265.b01-3
- Add backport of JDK-8251117 to allow key length to be retrieved from PKCS#11 FIPS keys
- Resolves: rhbz#1860993

* Tue Aug 25 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.265.b01-2
- Add backport of JDK-8223482 so PKCS#11 FIPS provider does not offer unsupported ciphers.
- Resolves: rhbz#1860965

* Mon Jul 27 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.265.b01-1
- Update to aarch64-shenandoah-jdk8u265-b01.
- Update release notes for 8u265 release.
- Resolves: rhbz#1860453

* Mon Jul 27 2020 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.262.b10-3
- ASSEMBLY_EXCEPTION LICENSE THIRD_PARTY_README moved to fully versioned dirs
- Resolves: rhbz#1831665

* Thu Jul 16 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b10-2
- Remove issues in NEWS file duplicated between 8u252 & 8u262 releases.
- Resolves: rhbz#1838811

* Sun Jul 12 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b10-1
- Update to aarch64-shenandoah-jdk8u262-b10.
- Switch to GA mode for final release.
- Update release notes for 8u262 release.
- Fix typo in jfr_arches which leads to ppc64 being wrongly excluded.
- Split JDK-8042159 patch into per-repo patches as upstream.
- Update JDK-8042159 JDK patch to apply after JDK-8238002 changes to Awt2dLibraries.gmk
- Resolves: rhbz#1838811

* Sat Jul 11 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b09-0.3.ea
- Restructure the build so a minimal initial build is then used for the final build (with docs)
- This reduces pressure on the system JDK and ensures the JDK being built can do a full build
- Resolves: rhbz#1838811

* Fri Jul 10 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b09-0.2.ea
- Update to aarch64-shenandoah-jdk8u262-b09-shenandoah-merge-2020-07-03
- Resolves: rhbz#1838811

* Fri Jul 10 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b09-0.1.ea
- With JDK-8248399 fixed, a broken jfr binary is no longer installed on architectures without JFR.
- Resolves: rhbz#1838811

* Thu Jul 09 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b09-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b09.
- Resolves: rhbz#1838811

* Wed Jul 08 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b08-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b08.
- Resolves: rhbz#1838811

* Tue Jul 07 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b07-0.3.ea
- Update to aarch64-shenandoah-jdk8u262-b07-shenandoah-merge-2020-06-18.
- Resolves: rhbz#1838811

* Sun Jul 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b07-0.2.ea
- Sync alt-java support with java-11-openjdk version.
- Resolves: rhbz#1838811

* Sat Jul 04 2020 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.262.b07-0.2.ea
- Created copy of java as alt-java and adapted alternatives and man pages
- Resolves: rhbz#1838811

* Fri Jul 03 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b07-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b07.
- Require tzdata 2020a so system tzdata matches resource updates in b07
- Resolves: rhbz#1838811

* Tue Jun 30 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b06-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b06.
- Resolves: rhbz#1838811

* Mon Jun 29 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b05-0.4.ea
- Update to aarch64-shenandoah-jdk8u262-b05-shenandoah-merge-2020-06-04.
- Resolves: rhbz#1838811

* Mon Jun 29 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b05-0.3.ea
- Add directories to files directive for demo package.
- Resolves: rhbz#1649801

* Sun Jun 28 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b05-0.2.ea
- Use RSA as default for keytool, as DSA is disabled in all crypto policies except LEGACY
- Resolves: rhbz#1582504

* Sat Jun 27 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b05.
- Resolves: rhbz#1838811

* Fri Jun 26 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b04.
- Resolves: rhbz#1838811

* Wed Jun 24 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b03-0.2.ea
- Update to aarch64-shenandoah-jdk8u262-b03-shenandoah-merge-2020-05-20.
- Resolves: rhbz#1838811

* Tue Jun 23 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b03.
- Resolves: rhbz#1838811

* Mon Jun 22 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b02-0.2.ea
- Introduce jfr_arches for architectures which support JFR.
- Fix path to jfr.jar.
- Use sa_arches for libsaproc.so inclusion.
- Resolves: rhbz#1838811

* Mon Jun 22 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b02-0.2.ea
- Explicitly list jfr.jar, default.jfc & profile.jfc in the spec file.
- Resolves: rhbz#1838811

* Sun Jun 21 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b02-0.2.ea
- Enable JFR in our builds, ahead of upstream default.
- Only enable JFR for JIT builds, as it is not supported with Zero.
- Turn off JFR on x86 for now due to assert(SerializePageShiftCount == count) crash.
- Resolves: rhbz#1838811

* Sun Jun 21 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b02.
- Resolves: rhbz#1838811

* Sat Jun 20 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.262.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u262-b01.
- Switch to EA mode.
- Adjust JDK-8143245/PR3548 patch following context changes due to JDK-8203287 for JFR
- Adjust RH1648644 following context changes due to introduction of JFR packages
- Add jfr binary to devel package and alternatives set
- Resolves: rhbz#1838811

* Tue Jun 02 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-7
- Enable alignment with FIPS crypto policy by default (-Dcom.redhat.fips=false to disable).
- Resolves: rhbz#1655466

* Mon Jun 01 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-6
- Use appropriate keystore types when in FIPS mode.
- Resolves: rhbz#1760838

* Fri May 22 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-5
- Add support for fastdebug builds on x86_64 only.
- Drop redundant slowdebug/debug sed invocation on the docs zip filename as it is only now built for non-debug.
- Resolves: rhbz#1836067

* Wed Apr 22 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-4
- Bump release number for RHEL 8.3.0.
- Resolves: rhbz#1810557

* Sun Apr 19 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-3
- Add release notes.
- Resolves: rhbz#1810557

* Sun Apr 19 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-2
- Make use of --with-extra-asflags introduced in jdk8u252-b01.
- Resolves: rhbz#1810557

* Mon Apr 06 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b09-1
- Update to aarch64-shenandoah-jdk8u252-b09.
- Switch to GA mode for final release.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b08-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b08.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b07-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b07.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b06-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b06.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b05.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b04.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b03.
- Adjust PR2974/RH1337583 & PR3083/RH1346460 following context changes in JDK-8230978
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b02.
- Resolves: rhbz#1810557

* Wed Apr 01 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.252.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u252-b01.
- Switch to EA mode.
- Adjust JDK-8199936/PR3533 patch following JDK-8227397 configure change
- Resolves: rhbz#1810557

* Fri Mar 27 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-4
- Need to support noarch for creating source RPMs for non-scratch builds.
- Resolves: rhbz#1737112

* Tue Mar 24 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-4
- Introduce stapinstall variable to set SystemTap arch directory correctly (e.g. arm64 on aarch64)
- Resolves: rhbz#1737112

* Mon Feb 24 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-3
- Add JDK-8165996/PR3506 & JDK-8195607/PR3776 to support NSS SQLite databases.
- Resolves: rhbz#1760437

* Sun Feb 23 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-2
- Sync SystemTap & desktop files with upstream IcedTea release 3.15.0, removing previous workarounds
- Resolves: rhbz#1737112

* Sun Feb 23 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-2
- Sync SystemTap & desktop files with upstream IcedTea release 3.11.0 using new script
- Resolves: rhbz#1737112

* Wed Jan 15 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b08-1
- Update to aarch64-shenandoah-jdk8u242-b08.
- Remove local copies of JDK-8031111 & JDK-8132111 as replaced by upstream versions.
- Resolves: rhbz#1785753

* Wed Jan 15 2020 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b07-2
- Add backports of JDK-8031111 & JDK-8132111 to fix TCK issue.
- Resolves: rhbz#1785753

* Mon Jan 13 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b07-1
- Update to aarch64-shenandoah-jdk8u242-b07.
- Switch to GA mode for final release.
- Remove Shenandoah S390 patch which is now included upstream as JDK-8236829.
- Resolves: rhbz#1785753

* Sun Jan 05 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u242-b05.
- Attempt to fix Shenandoah formatting failures on S390, introduced by JDK-8232102.
- Revise b05 snapshot to include JDK-8236178.
- Add additional Shenandoah formatting fixes revealed by successful -Wno-error=format run
- Resolves: rhbz#1785753

* Sat Jan 04 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.242.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u242-b01.
- Switch to EA mode.
- Resolves: rhbz#1785753

* Sat Jan 04 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-6
- Update generate_source_tarball.sh script to use the PR3756 patch and retain the secp256k1 curve.
- Regenerate source tarball using the updated script and add the -'4curve' suffix.
- Resolves: rhbz#1746879

* Thu Jan 02 2020 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-5
- Revert SSBD removal for now, until appropriate messaging has been decided.
- Resolves: rhbz#1750419

* Tue Dec 24 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-4
- Remove CVE-2018-3639 mitigation due to performance regression and
    OpenJDK position on speculative execution vulnerabilities.
    https://mail.openjdk.java.net/pipermail/vuln-announce/2019-July/000002.html
- Resolves: rhbz#1750419

* Thu Nov 14 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-3
- Bump release number for RHEL 8.2.0.
- Resolves: rhbz#1753423

* Fri Oct 25 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-2
- Disable FIPS mode support unless com.redhat.fips is set to "true".
- Resolves: rhbz#1655466

* Fri Oct 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b09-1
- Update to aarch64-shenandoah-jdk8u232-b09.
- Switch to GA mode for final release.
- Remove PR1834/RH1022017 which is now handled by JDK-8228825 upstream.
- Resolves: rhbz#1753423

* Fri Oct 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b08-0.1.ea
- Update to aarch64-shenandoah-jdk8u232-b08.
- Resolves: rhbz#1753423

* Fri Oct 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b05-0.2.ea
- Update to aarch64-shenandoah-jdk8u232-b05-shenandoah-merge-2019-09-09.
- Resolves: rhbz#1753423

* Thu Oct 10 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u232-b05.
- Drop upstreamed patch JDK-8141570/PR3548.
- Adjust context of JDK-8143245/PR3548 to apply against upstream JDK-8141570.
- Resolves: rhbz#1753423

* Mon Oct 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.232.b01-0.1.ea
- Update to aarch64-shenandoah-jdk8u232-b01.
- Switch to EA mode.
- Drop JDK-8210761/RH1632174 as now upstream.
- Drop JDK-8223219 as now upstream.
- JDK-8226870 removed clhsdb and hdsdb from the JRE bin directory, so we should do likewise.
- Add alternatives support for these two new SDK binaries.
- Resolves: rhbz#1753423

* Fri Sep 27 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b10-3
- SunPKCS11 runtime provider name is a concatenation of "SunPKCS11-" and the name in the config file.
- Change nss.fips.cfg config name to "NSS-FIPS" to avoid confusion with nss.cfg.
- Resolves: rhbz#1750752

* Wed Aug 21 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b10-2
- nss.fips.cfg needs to be moved to %%{etcjavadir} and symlinked into the JDK, like nss.cfg
- Resolves: rhbz#1655466

* Thu Aug 15 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b10-2
- Backport FIPS mode patch to java-1.8.0-openjdk, simplifying provider removal.
- Resolves: rhbz#1655466

* Thu Aug 15 2019 Martin Balao <mbalao@redhat.com> - 1:1.8.0.222.b10-2
- Support the FIPS mode crypto policy on RHEL 8.
- Resolves: rhbz#1655466

* Thu Jul 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b10-1
- Update to aarch64-shenandoah-jdk8u222-b10.
- Resolves: rhbz#1724452

* Tue Jul 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b09-2
- Drop NSS runtime dependencies and patches to link against it.
- Resolves: rhbz#1678557

* Tue Jul 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b09-1
- Update to aarch64-shenandoah-jdk8u222-b09.
- Switch to GA mode for final release.
- Resolves: rhbz#1724452

* Tue Jul 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b08-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b08.
- Adjust PR3083/RH134640 to apply after JDK-8182999
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b07-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b07 and Shenandoah merge 2019-06-13.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b06-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b06.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b05-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b05.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b04-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b04.
- Drop remaining JDK-8210425/RH1632174 patch now AArch64 part is upstream.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b03-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b03.
- Drop 8210425 patches applied upstream. Still need to add AArch64 version in aarch64/shenandoah-jdk8u.
- Re-generate JDK-8141570 & JDK-8143245 patches due to 8210425 zeroshark.make changes.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b02-0.1.ea
- Update to aarch64-shenandoah-jdk8u222-b02.
- Drop 8064786/PR3599 & 8210416/RH1632174 as applied upstream (8064786 silently in 8176100).
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-2
- Switch to EA mode
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- fontconfig build requirement should be fontconfig-devel, previously masked by Gtk2+ dependency
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Allow Recommends and Suggests on Fedora platforms too.
- Resolves: rhbz#1724452

* Mon Jul 08 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Add missing build requirements for libXext-devel and libXrender-devel, previously masked by Gtk2+ dependency.
- Resolves: rhbz#1724452

* Sun Jul 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Add new tarball to new format sources file.
- Resolves: rhbz#1724452

* Sun Jul 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Drop unnecessary build requirement on gtk2-devel, as OpenJDK searches for Gtk+ at runtime.
- Resolves: rhbz#1724452

* Sun Jul 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Make use of Recommends and Suggests dependent on RHEL 8+ environment.
- Resolves: rhbz#1724452

* Sun Jul 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.222.b01-1
- Update to aarch64-shenandoah-jdk8u222-b01.
- Refactor PR2888 after inclusion of 8129988 upstream. Now includes PR3575.
- Drop 8171000 & 8197546 as applied upstream.
- Resolves: rhbz#1724452

* Wed Jul 03 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-5
- Obsolete javadoc-debug and javadoc-debug-zip packages via javadoc and javadoc-zip respectively.
- Resolves: rhbz#1724452

* Wed Jul 03 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.212.b04-5
- Include 'ea' designator in Release when appropriate.
- Resolves: rhbz#1724452

* Wed Jul 03 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.212.b04-5
- Don't produce javadoc/javadoc-zip sub packages for the debug variant build.
- Don't perform a bootcycle build for the debug variant build.
- Resolves: rhbz#1724452

* Wed Jul 03 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-5
- Handle milestone as variables so we can alter it easily and set the docs zip filename appropriately.
- Drop unused use_shenandoah_hotspot variable.
- Resolves: rhbz#1724452

* Fri Jun 14 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-4
- Update to aarch64-shenandoah-jdk8u212-b04-shenandoah-merge-2019-04-30.
- Update version logic to handle -shenandoah* tag suffix.
- Drop PR3634 as applied upstream.
- Adjust 8214206 fix for S390 as BinaryMagnitudeSeq moved to shenandoahNumberSeq.cpp
- Update 8214206 to use log2_long rather than casting to intptr_t, which may be smaller than size_t.
- Resolves: rhbz#1688365
- Resolves: rhbz#1688382

* Thu May 02 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-3
- Remove additions to EXTRA_CFLAGS and EXTRA_CPP_FLAGS which are now made by upstream.
- Resolves: rhbz#1693468

* Thu May 02 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-2
- Add JDK-8223219 to avoid -fstack-protector overriding -fstack-protector-strong
- Resolves: rhbz#1693468

* Thu Apr 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-1
- Update to aarch64-shenandoah-jdk8u212-b04.
- Resolves: rhbz#1693468

* Thu Apr 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b03-1
- Update to aarch64-shenandoah-jdk8u212-b03.
- Resolves: rhbz#1693468

* Thu Apr 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b02-1
- Add new clhsdb and hsdb binaries.
- Resolves: rhbz#1693468

* Tue Apr 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b02-1
- Update to aarch64-shenandoah-jdk8u212-b02.
- Remove patches included upstream
  - JDK-8197429/PR3546/RH153662{2,3}
  - JDK-8184309/PR3596
  - JDK-8210647/RH1632174
  - JDK-8029661/PR3642/RH1477159
  - JDK-8145096/PR3693
- Re-generate patches
  - JDK-8203030
- Add casts to resolve s390 ambiguity in calls to log2_intptr
- Resolves: rhbz#1693468

* Sun Apr 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.202.b08-1
- Update to aarch64-shenandoah-jdk8u202-b08.
- Remove patches included upstream
  - JDK-8211387/PR3559
  - JDK-8207057/PR3613
  - JDK-8165852/PR3468
  - JDK-8073139/PR1758/RH1191652
  - JDK-8044235
  - JDK-8172850/RH1640127
  - JDK-8209639/RH1640127
  - JDK-8131048/PR3574/RH1498936
  - JDK-8164920/PR3574/RH1498936
- Re-generate patches
  - JDK-8210647/RH1632174
- Resolves: rhbz#1693468

* Thu Apr 04 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b13-1
- Update to aarch64-shenandoah-jdk8u201-b13.
- Drop JDK-8160748 & JDK-8189170 AArch64 patches now applied upstream.
- Resolves: rhbz#1693468

* Tue Apr 02 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.201.b09-5
- Update patch for RH1566890.
  - Renamed rh1566890_speculative_store_bypass_so_added_more_per_task_speculation_control_CVE_2018_3639 to
    rh1566890-CVE_2018_3639-speculative_store_bypass.patch
  - Added dependent patch,
    rh1566890-CVE_2018_3639-speculative_store_bypass_toggle.patch
- Resolves: rhbz#1693468

* Tue Mar 26 2019 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.201.b09-4
- added gating

* Mon Feb 11 2019 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.201.b09-3
- removed config declaration from links to config files
- Resolves: rhbz#1661577

* Thu Feb 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b09-2
- Fix invalid dates earlier in the ChangeLog.
- Resolves: rhbz#1661577

* Thu Feb 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b09-2
- Add PR3655 to allow the system crypto policy to be turned off.
- Resolves: rhbz#1661577

* Wed Feb 06 2019 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b09-1
- Add backport of JDK-8145096 (PR3693) to fix undefined behaviour issues on newer GCCs
- Resolves: rhbz#1661577

* Tue Feb 05 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b09-0
- Update to aarch64-shenandoah-jdk8u201-b09.
- Resolves: rhbz#1661577

* Wed Jan 30 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.192.b12-0
- Update to aarch64-shenandoah-jdk8u192-b12.
- Remove patches included upstream
  - JDK-8031668/PR2842
  - JDK-8148351/PR2842
  - JDK-6260348/PR3066
  - JDK-8061305/PR3335/RH1423421
  - JDK-8188030/PR3459/RH1484079
  - JDK-8205104/PR3539/RH1548475
  - JDK-8185723/PR3553
  - JDK-8186461/PR3557
  - JDK-8201509/PR3579
  - JDK-8075942/PR3602
  - JDK-8203182/PR3603
  - JDK-8206406/PR3610/RH1597825
  - JDK-8206425
  - JDK-8036003
  - JDK-8201495/PR2415
  - JDK-8150954/PR2866/RH1176206
- Re-generate patches (mostly due to upstream build changes)
  - JDK-8073139/PR1758/RH1191652
  - JDK-8143245/PR3548 (due to JDK-8202600)
  - JDK-8197429/PR3546/RH1536622 (due to JDK-8189170)
  - JDK-8199936/PR3533
  - JDK-8199936/PR3591
  - JDK-8207057/PR3613
  - JDK-8210761/RH1632174 (due to JDK-8207402)
  - PR3559 (due to JDK-8185723/JDK-8186461/JDK-8201509)
  - PR3593 (due to JDK-8081202)
  - RH1566890/CVE-2018-3639 (due to JDK-8189170)
  - RH1649664 (due to JDK-8196516)
- Add 8160748 for AArch64 which is missing from upstream 8u version.
- Add port of 8189170 to AArch64 which is missing from upstream 8u version.
- Resolves: rhbz#1661577

* Mon Jan 28 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b14-1
- Add 8131048 & 8164920 (PR3574/RH1498936) to provide a CRC32 intrinsic for PPC64.
- Resolves: rhbz#1661577

* Thu Jan 24 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b14-0
- Introduce sa_arches for architectures with sa-jdi.jar and include aarch64
- Resolves: rhbz#1661577

* Thu Jan 10 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b14-0
- Update to aarch64-shenandoah-jdk8u191-b14.
- Adjust JDK-8073139/PR1758/RH1191652 to apply following 8155627 backport.
- Resolves: rhbz#1661577

* Wed Jan 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b13-0
- Update to aarch64-shenandoah-jdk8u191-b13.
- Update tarball generation script in preparation for PR3667/RH1656676 SunEC changes.
- Use remove-intree-libraries.sh to remove the remaining SunEC code for now.
- Resolves: rhbz#1661577

* Sat Dec 22 2018 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-12
- Add backport of JDK-8029661 which adds TLSv1.2 support to the PKCS11 provider.
- Resolves: rhbz#1661577

* Sat Dec 22 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-11
- Revise Shenandoah PR3634 patch following upstream discussion.
- Resolves: rhbz#1661577

* Wed Dec 19 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.191.b12-11
- Refactor _find_debuginfo_opts -g (global over define)
- Resolves: rhbz#1661577

* Wed Nov 07 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.191.b12-9
- headfull suggests of cups, replaced by Requires of cups-libs in headless
- Resolves: rhbz#1661577

* Wed Nov 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-9
- Note why PR1834/RH1022017 is not suitable to go upstream in its current form.
- Resolves: rhbz#1661577

* Mon Nov 05 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-9
- Document patch sections.
- Resolves: rhbz#1661577

* Mon Nov 05 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-9
- Fix patch organisation in the spec file:
-   * Move ECC patches back to upstreamable section
-   * Move system cacerts & crypto policy patches to upstreamable section
-   * Merge "Local fixes" and "RPM fixes" which amount to the same thing
-   * Move system libpng & lcms patches back to 8u upstreamable section
- Resolves: rhbz#1661577

* Fri Oct 26 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.191.b12-8
- added Patch583 jdk8172850-rh1640127-01-register_allocator_crash.patch
- added Patch584 jdk8209639-rh1640127-02-coalesce_attempted_spill_non_spillable.patch
- Resolves: rhbz#1661577

* Tue Oct 23 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.191.b12-2
- cups moved to headful package
- Resolves: rhbz#1633817

* Tue Oct 23 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.191.b12-1
- updated to aarch64-shenandoah-jdk8u191-b12
- deleted 8146115-pr3508-rh1463098.patch, pr3619.patch, pr3620.patch - should be upstreamed
- create pr3634-fix_shenandoah_for_size_t_on_s390.patch to fix build failure on s390
- Resolves: rhbz#1633817

* Fri Oct 12 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-7
- Add patch jdk8210425-rh1632174-03-compile_with_o2_and_ffp_contract_off_as_for_fdlibm_zero.patch:
  - Annother fix for optimization gaps (annocheck issues)
  - Zero 8u version fix was missing. Hence, only shows up on Zero arches.
- Resolves: rhbz#1633817

* Tue Oct 09 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Update to aarch64-shenandoah-jdk8u191-b12.
- Resolves: rhbz#1633817

* Mon Oct 08 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-6
- Refreshed upstreamed patches (from 8u202):
  - jdk8044235-src_zip_should_include_all_sources.patch: src.zip should include all sources.
  - jdk8073139-pr2236-rh1191652--use_ppc64le_as_the_arch_directory_on_that_platform_and_report_it_in_os_arch_aarch64_forest.patch,
    jdk8073139-pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_jdk.patch,
    jdk8073139-pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_root.patch: PPC64LE JVM reporting issues.
- Moved both patch series to 8u202 sections.
- Resolves: rhbz#1633817

* Tue Oct 02 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b10-0
- Update to aarch64-shenandoah-jdk8u191-b10.
- Drop 8146115/PR3508/RH1463098 applied upstream.
- Resolves: rhbz#1633817

* Mon Oct 01 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b16-0
- Add new Shenandoah patch PR3634 as upstream still fails on s390.
- Resolves: rhbz#1633817

* Mon Oct 01 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b16-0
- Update to aarch64-shenandoah-jdk8u181-b16.
- Drop PR3619 & PR3620 Shenandoah patches which should now be fixed upstream.
- Resolves: rhbz#1633817

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b15-0
- Move to single OpenJDK tarball build, based on aarch64/shenandoah-jdk8u.
- Update to aarch64-shenandoah-jdk8u181-b15.
- Drop 8165489-pr3589.patch which was only applied to aarch64/jdk8u builds.
- Split ppc64 Shenandoah fix into separate patch file with its own bug ID (PR3620).
- Update pr3539-rh1548475.patch to apply after 8187045.
- Resolves: rhbz#1633817

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Remove unneeded functions from ppc shenandoahBarrierSet.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Add missing shenandoahBarrierSet implementation for ppc64{be,le}.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Fix wrong format specifiers in Shenandoah code.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Avoid changing variable types to fix size_t, at least for now.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- More size_t fixes for Shenandoah.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Add additional s390 size_t case for Shenandoah.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Attempt to fix Shenandoah build issues on s390.
- Resolves: rhbz#1640188

* Mon Oct 1 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b13-10
- Use the Shenandoah HotSpot on all architectures.
- Resolves: rhbz#1640188

* Mon Oct 01 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-5
- Add explicit requirement for libXcomposite which is used when performing
  screenshots from Java.
- Add explicit BR unzip required for building OpenJDK.
- Resolves: rhbz#1633817

* Thu Sep 27 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-4
- Add fixes for optimization gaps (annocheck issues):
  - 8210761: libjsig is being compiled without optimization
  - 8210647: libsaproc is being compiled without optimization
  - 8210416: [linux] Poor StrictMath performance due to non-optimized compilation
  - 8210425: [x86] sharedRuntimeTrig/sharedRuntimeTrans compiled without optimization
             8u upstream and aarch64/jdk8u upstream versions.
- Resolves: rhbz#1633817

* Wed Sep 26 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-3
- Renamed more patches for clarity:
  include-all-srcs.patch => jdk8044235-src_zip_should_include_all_sources.patch
  java-1.8.0-openjdk-rh1191652-hotspot-aarch64.patch => jdk8073139-pr2236-rh1191652--use_ppc64le_as_the_arch_directory_on_that_platform_and_report_it_in_os_arch_aarch64_forest.patch
  java-1.8.0-openjdk-rh1191652-jdk.patch => jdk8073139-pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_jdk.patch
  java-1.8.0-openjdk-rh1191652-root.patch => jdk8073139-pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_root.patch
- Resolves: rhbz#1633817

* Tue Sep 18 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b15-2
- Update(s) from upstreamed patches:
  - 8036003-dont-add-unnecessary-debug-links.patch =>
    jdk8036003-add_with_native_debug_symbols_configure_flag.patch
  - rh1176206-jdk.patch =>
    jdk8150954-pr2866-rh1176206-screenshot_xcomposite_jdk.patch =>
    Deleted rh1176206-root.patch as thats no longer needed with
    upstream 8150954.
  - Refreshed jdk8165852-pr3468-mount_point_not_found_for_a_file_which_is_present_in_overlayfs.patch from upstream.
  - Refreshed jdk8201495-zero_reduce_limits_of_max_heap_size_for_boot_JDK_on_s390.patch from upstream.
  - 8207057-pr3613-hotspot-assembler-debuginfo.patch =>
    jdk8207057-pr3613-no_debug_info_for_assembler_files_hotspot.patch and
    jdk8207057-pr3613-no_debug_info_for_assembler_files_root.patch. From JDK 8u
    review.
- Renamed pr2842-02.patch => jdk8148351-pr2842-02-only_display_resolved_symlink_for_compiler_do_not_change_path.patch.
- Renamed spec-only patch:
  pr3183.patch => pr3183-rh1340845-support_fedora_rhel_system_crypto_policy.patch
- Renamed java-1.8.0-openjdk-size_t.patch =>
  jdk8201495-zero_reduce_limits_of_max_heap_size_for_boot_JDK_on_s390.patch
- Moved SunEC provider via system NSS to RPM specific patches section.
- Moved upstream 8u patches to appropriate sections (8u192/8u202).
- Removed rh1214835.patch since it's invalid. See:
  https://icedtea.classpath.org/bugzilla/show_bug.cgi?id=2304#c3
- Use --with-native-debug-symbols=internal which JDK-8036003 adds.
- Resolves: rhbz#1633817

* Tue Sep 11 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.181.b15-1
- fixed unexpanded arch in policy tool desktop file
- fixed versions (8->1.8.0) of images used in desktop files
- Resolves: rhbz#1633817

* Mon Aug 27 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b13-9
- Adjust system jpeg patch, jdk8043805-allow_using_system_installed_libjpeg.patch, so as to filter
  -Wl,--as-needed. Resolves RHBZ#1622186.
- Resolves: rhbz#1633817

* Mon Aug 27 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181.b13-8
- Adjust system NSS patch, pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk8.patch, so as to filter
  -Wl,--as-needed. Resolves RHBZ#1622186.
- Resolves: rhbz#1633817

* Wed Aug 01 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.181.b13-7
- build number moved from release to version

* Mon Jul 23 2018 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-7.b13
- Remove duplicate -mstackrealign workaround.

* Mon Jul 23 2018 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-6.b13
- Bump release for previous changeset.

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-6.b13
- Update to aarch64-jdk8u181-b13 and aarch64-shenandoah-jdk8u181-b13.
- Remove 8187577/PR3578 now applied upstream.

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-5.b04
- Update bug status and add missing bug IDs

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-5.b04
- Add "8146115, PR3508, RH1463098: Improve docker container detection and resource configuration usage"

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b04
- Add "8206406, PR3610, RH1597825: StubCodeDesc constructor publishes partially-constructed objects on StubCodeDesc::_list"

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b04
- Mark bugs now backported to OpenJDK 8u upstream

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-3.b04
- Backport "8203182, PR3603: Release session if initialization of SunPKCS11 Signature fails"

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-2.b04
- Backport "8075942, PR3602: ArrayIndexOutOfBoundsException in sun.java2d.pisces.Dasher.goTo"

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-1.b04
- Add missing bug identifiers for patches unique to RHEL 8 and move to correct sections.

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-1.b04
- Mark bugs that have been pushed to 8u upstream and are scheduled for a release.

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-1.b04
- Update to aarch64-jdk8u181-b04 and aarch64-shenandoah-jdk8u181-b04.

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-0.b03
- Update to aarch64-jdk8u181-b03 and aarch64-shenandoah-jdk8u181-b03.
- Remove AArch64 patch for PR3458/RH1540242 as applied upstream.

* Sun Jul 22 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-17.b11
- Fix bad output file name substitution for SystemTap files.

* Wed Jul 18 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-17.b11
- Update Shenandoah tarball to fix TCK overflow failure.

* Tue Jul 17 2018 Jiri Vanek <jvanek@redhat.com> - 11:1.8.0.172-16.b11
- added Recommends gtk2 for main package
- added Suggests lksctp-tools, pcsc-lite-devel, cups for headless package
- see RHBZ1598152

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.172-15.b11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jul 10 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-14.b11
- Fix hook to show hs_err*.log files on failures.

* Mon Jul 02 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-13.b11
- Fix requires/provides filters for internal libs. See
  RHBZ#1590796

* Mon Jun 25 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-12.b11
- Add hook to show hs_err*.log files on failures.

* Wed Jun 20 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-11.b11
- Expose release/slowdebug builds being produced via conditionals.

* Wed Jun 20 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-11.b11
- Add additional fix (PR3601) to fix -Wreturn-type failures introduced by 8061651
- Backport 8064786 (PR3601) to fix -Wreturn-type failure on debug builds.
- Bring in PR3519 from IcedTea 3.7.0 to fix remaining -Wreturn-type failure on AArch64.
- Sync with IcedTea 3.8.0 patches to use -Wreturn-type.
- Add backports of 8141570, 8143245, 8197981 & 8062808.
- Drop pr3458-rh1540242-zero.patch which is covered by 8143245.

* Wed Jun 20 2018 Jiri Vanek <jvanek@redhat.com> - 11:1.8.0.172-10.b11
- jsa files changed to 444 to pass rpm verification

* Mon Jun 18 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-9.b11
- Filter private provides/requires: 'lib.so(SUNWprivate_.*'

* Thu Jun 14 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-8.b11
- Add provides/requires for libjvm.so back. See RHBZ#1591215.

* Wed Jun 13 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.172-7.b11
- Fix reg-ex for filtering private libraries' provides/requires.

* Wed Jun 13 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-6.b11
- Remove build flags exemption for aarch64 now the platform is more mature and can bootstrap OpenJDK with these flags.
- Remove duplicate -fstack-protector-strong; it is provided by the RHEL cflags.
- Add missing changelog credits

* Mon Jun 11 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.172-5.b11
- Merge changes from RHEL 7

* Mon Jun 11 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-5.b11
- Read jssecacerts file prior to trying either cacerts file (system or local) (PR3575)

* Mon Jun 11 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-5.b11
- Fix a number of bad bug identifiers (PR3546 should be PR3578, PR3456 should be PR3546)

* Thu Jun 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-5.b11
- Update Shenandoah tarball to include 2018-05-15 merge.
- Split PR3458/RH1540242 fix into AArch64 & Zero sections, so former can be skipped on Shenandoah builds.
- Drop PR3573 patch applied upstream.
- Restrict 8187577 fix to non-Shenandoah builds, as it's included in the new tarball.

* Thu Jun 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-5.b11
- Sync with IcedTea 3.8.0.
- Label architecture-specific fixes with architecture concerned
- x86: S8199936, PR3533: HotSpot generates code with unaligned stack, crashes on SSE operations (-mstackrealign workaround)
- PR3539, RH1548475: Pass EXTRA_LDFLAGS to HotSpot build
- 8171000, PR3542, RH1402819: Robot.createScreenCapture() crashes in wayland mode
- 8197546, PR3542, RH1402819: Fix for 8171000 breaks Solaris + Linux builds
- 8185723, PR3553: Zero: segfaults on Power PC 32-bit
- 8186461, PR3557: Zero's atomic_copy64() should use SPE instructions on linux-powerpcspe
- PR3559: Use ldrexd for atomic reads on ARMv7.
- 8187577, PR3578: JVM crash during gc doing concurrent marking
- 8201509, PR3579: Zero: S390 31bit atomic_copy64 inline assembler is wrong
- 8165489, PR3589: Missing G1 barrier in Unsafe_GetObjectVolatile
- PR3591: Fix for bug 3533 doesn't add -mstackrealign to JDK code
- 8184309, PR3596: Build warnings from GCC 7.1 on Fedora 26

* Wed Jun 06 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.172-1.b11
- updated to u172-b11
- removed patches:
- patch207 8200556-pr3566.patch
- patch104 pr3458-rh1540242.patch
- patch209 8035496-hotspot.patch
- patch700 pr3573-fix_TCK_crash_with_shenandoah_in_shenandoahsupport_cpp_in_case_of_dead_brnach_in_is_independent.patch
- fixed issue with atkwrapper wrongly palced broken symlink
- fixed libjvm path for system tap
- returned patch104 pr3458-rh1540242.patch

* Mon Jun 04 2018 Jiri Vanek <jvanek@redhat.com> - 1:10.0.1.10-7
- quoted sed expressions, changed possibly confussing # by @
- added vendor(origin) into icons
- removed last trace of relative symlinks
- added BuildRequires of javapackages-tools to fix build failure after Requires change to javapackages-filesystem

* Fri Jun 01 2018 Jiri Vanek <jvanek@redhat.com>  - 1:1.8.0.171-6.b10
- aligning with java-openjdk in fedora:
- removed fx binding
- config files to etc
- slowdebug instead simply debug subpackage
- purged provides
- many macros renamed
- typos correction
- bumped jstack (may be wrong)

* Wed May 09 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.171-5.b10
- Compile i686 JDK with -mstackrealign.

* Wed Apr 25 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.171-4.b10
- Enable hardened build unconditionally (also for Zero).
  Resolves RHBZ#1290936.

* Tue Apr 24 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.171-3.b10
- Enable hardened build for Aarch64.

* Tue Apr 24 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.171-2.b10
- Update rhbz1548475-LDFLAGSusage.patch to also set linker
  flags for libsaproc.so and libjsig.so.

* Wed Apr 18 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.171-1.b10
- Update to aarch64-jdk8u171-b10 and aarch64-shenandoah-jdk8u171-b10.
- Fix jconsole.desktop.in subcategory, replacing "Monitor" with "Profiling" (PR3550) (gnu_andrew)
- Fix invalid license 'LGPL+' (should be LGPLv2+ for ECC code) and add misisng ones (gnu_andrew)

* Wed Apr 18 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.162-7.b12
- added ownership of policy dir and subdirs
- removed ignored attributes for classes.jsa

* Tue Apr 10 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.162-6.b12
- Use correct patch for RHBZ#1538767 (JDK-8196516)

* Mon Apr 02 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.162-5.b12
- Cleanup from previous commit.
- Remove unused upstream patch 8167200.hotspotAarch64.patch.

* Thu Mar 29 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.162-3.b12
- returned patch562 rhbz_1540242.patch
- added Patch563 rhbz_1536622-JDK8197429-jdk8.patch

* Mon Mar 26 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.162-2.b12
- Added  patch 540 rhbz1548475-LDFLAGSusage.patch to honor build flags fully

* Wed Mar 21 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.162-1.b12
- Update to aarch64-jdk8u162-b12 and aarch64-shenandoah-jdk8u162-b12.
- Remove upstreamed patches for 8181055/PR3394/RH1448880,
-  8181419/PR3413/RH1463144, 8145913/PR3466/RH1498309,
-  8168318/PR3466/RH1498320, 8170328/PR3466/RR1498321 and
-  8181810/PR3466/RH1498319.

* Wed Mar 07 2018 Adam Williamson <awilliam@redhat.com> - 1:1.8.0.161-9.b14
- Rebuild to fix GCC 8 mis-compilation
  See https://da.gd/YJVwk ("GCC 8 ABI change on x86_64")

* Sun Feb 11 2018 Sandro Mani <manisandro@gmail.com> - 1:1.8.0.161-8.b14
- Rebuild (giflib)

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1:1.8.0.161-7.b14
- Escape macros in %%changelog

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.161-6.b14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 31 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.161-5.b14
- Additional fix needed for FTBFS bug on aarch64.
  Resolves RHBZ#1540242.

* Wed Jan 31 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.161-4.b14
- Add fix for FTBFS on aarch64 and armv7hl.
  Resolves RHBZ#1540242.

* Tue Jan 30 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.161-3.b14
- Include Aarch64 build fixes post January 2018 CPU.

* Mon Jan 29 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.161-2.b14
- Work around ppc64le gdb backtrace problem in %%check.
  See RHBZ#1539664

* Wed Jan 24 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.161-1.b14
- Fix FTBFS due to link failure in libfontmanager.so
- See RHBZ#1538767

* Wed Jan 24 2018 jvanek <jvanek@redhat.com> - 1:1.8.0.161-0.b14
- updated to u161, rmeoved upstreamed patches
- removed patch555 8164293-pr3412-rh1459641.patch
- removed patch550 8175813-pr3394-rh1448880.patch
- removed patch547 8173941-pr3326.patch
- removed patch532 8162384-pr3122-rh1358661.patch
- removed patch535 8153711-pr3313-rh1284948.patch
- removed patch561 8075484-pr3473-rh1490713.patch
- removed patch554 8175887-pr3415.patch

* Mon Nov 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.151-1.b12
- added ownership of etc dirs
- sysconfdir/.java/.systemPrefs
- sysconfdir/.java

* Wed Oct 25 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.151-1.b12
- updated to aarch64-jdk8u151-b12 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u151-b12 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u151-b12.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u151-b12.tar.xz as new sources for hotspot
- tapset updated to 3.6pre02
- policies adapted to new limited/unlimited schmea
- above acomapnied by c-j-c 3.3
- alligned patches and added PPC ones (thanx to gnu_andrew)
- added patch209: 8035496-hotspot.patch
- added patch210: suse_linuxfilestore.patch

* Wed Oct 04 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.144-7.b01
- updated to aarch64-shenandoah-jdk8u144-b02-shenandoah-merge-2017-10-02 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u144-b02-shenandoah-merge-2017-10-02.tar.xz as new sources for hotspot

* Fri Sep 15 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-6.b01
- added patch540, bug1484079.patch

* Fri Sep 08 2017 Troy Dawson <tdawson@redhat.com> - 1:1.8.0.144-6.b01
- Cleanup spec file conditionals

* Fri Aug 25 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-4.b01
- added ownership of diretories which were oonly listing files

* Fri Aug 25 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-3.b01
- added (experiment) "--" delimiter also to $suffix in expanding macros

* Wed Aug 23 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-1.b01
- Update to aarch64-jdk8u144-b01 and aarch64-shenandoah-jdk8u144-b01.
- Exclude 8175887 from Shenandoah builds as it has been included in that repo.
- Added 8164293-pr3412-rh1459641.patch backport from 8u development tree
- get rid of bin/* and lib/*, fixed rhbz1480777
- adapted to rpm 4.14: all expanding macros changed to define, all %1 and %%1 replaced by %%{?1}, all expandable macros parameter preffixed by --
- get rid of generated filelists all except javafx and demos

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.141-5.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Florian Weimer <fweimer@redhat.com> - 1:1.8.0.141-4.b16
- Rebuild with binutils fix for ppc64le (#1475636)

* Wed Jul 26 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.141-3.b16
- added patch208, aarch64BuildFailure.patch to fix condition found during jdk9 build

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.141-2.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.141-1.b16
- updated to security u141.b16
- sync patches with rhel7
- removed no longer defined jvmjardir

* Sat Jun 17 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-7.b12
- adapted to no longer noarch openjfx-devel

* Wed Jun 07 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-6.b12
- added virtualprovides for javafx

* Wed Jun 07 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-5.b12
- fixed target of to fxrt.jar link
- fixedname of libglass

* Tue Jun 06 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-3.b12
- source999 moved to source1
- added two pathces 8181055-pr3394-rh1448880.patch and 8175813/PR3394/RH1448880
- enabled (commented out) system NSS via patch1000, rh1648249-add_commented_out_nss_cfg_provider_to_java_security.patch

* Tue May 09 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-1.b12
- added javafx binding subpackages

* Thu Apr 20 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-1.b12
- updated to aarch64-jdk8u131-b12 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u131-b12-shenandoah-merge-2017-04-20 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u131-b12.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u131-b12-shenandoah-merge-2017-04-20.tar.xz as new sources for hotspot

* Sun Mar 19 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-12.b14
- minor tweaks, egrep replaced by grep -E, added provides for some subpackages

* Mon Mar 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-11.b14
- sync from rhel, reordered patches, enabled shenanoah on aarch64
- Patch OpenJDK to check the system cacerts database directly
- Remove unneeded symlink to the system cacerts database
- Drop outdated openssl dependency from when the RPM built the cacerts database
- udpated to latest stable shenandoah hotspot

* Mon Mar 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-10.b14
- rhbz#1423751 - removed -fno-split-loops worakround as building against newer GCC7

* Tue Feb 28 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-9.b14
- updated to latest stable shenandoah hotspot
- updated to properly tagged upstream forest (no update, just rename)
- fixed update package to verify PR2126 patch and work with sha512

* Tue Feb 28 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-8.b14
- rebuild because of NSS

* Tue Feb 21 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-7.b14
- fixed the config(noreplace) issue with various left files lke java.security (rhbz#1183793)
- by calling new c-j-c hooks
- removed self-tail-bitting check check_sum_presented_in_spec
- release 6+7 to verify update path

* Mon Feb 20 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-5.b14
- patch 536 reordered to 537
- added patch 536 - Backport "8170888: [linux] Experimental support for cgroup memory limits in container (ie Docker) environments"
- added patch 538 - 1423421: Javadoc crashes when method name ends with "Property"
- rhbz#1423751 - added -fno-split-loops worakround sigsew when building with GCC7 (probably bug in jdk's JIT )

* Fri Feb 17 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-4.b14
- added Patch535 and 526
- tweeked debugsymbols check for sigill

* Wed Jan 25 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-2.b14
- revertrd patch535, excludeECDHE-1415137.patch and related changes
- issue casued by nss, see rhbz#1415137 c#35

* Tue Jan 24 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-2.b14
- added patch535, excludeECDHE-1415137.patch to tmp-worakround crash with nss

* Tue Jan 24 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-1.b14
- updated to aarch64-jdk8u121-b14 (from openjdk8-forests/latest-aarch64)
- updated to aarch64-shenandoah-jdk8u121-b14 (from openjdk8-forests/latest-shenandoah) of hotspot
- used openjdk8-forests-latest-aarch64-aarch64-jdk8u121-b14.tar.xz as new sources
- used openjdk8-forests-latest-shenandoah-aarch64-shenandoah-jdk8u121-b14.tar.xz as new sources for hotspot
- deleted:    8044762-pr2960.patch 8049226-pr2960.patch 8154210.patch 8158260-pr2991-rh1341258.patch 8159244-pr3074.patch
- adapted java-1.8.0-openjdk-size_t.patch pr1834-rh1022017-reduce_ellipticcurvesextension_to_provide_only_three_nss_supported_nist_curves_23_24_25.patch rh1163501-increase_2048_bit_dh_upper_bound_fedora_infrastructure_in_dhparametergenerator.patch
- updated from internal (rhel) repo  OPENJDK_URL_DEFAULT=ssh://t...redhat.com//...ty/
- with custom PR2126=/.../pr2126.patch (removed newly added brainpool curves)
- withspecial values of PROJECT_NAME="openjdk8-forests", REPO_NAME="latest-aarch64"
- with correct tag VERSION="aarch64-jdk8u121-b14"
- and for shenandoah hotspot used custom repo REPO_NAME=latest-shenandoah
- with correct tag VERSION="aarch64-shenandoah-jdk8u121-b14"
- complete changes to  generate_source_tarball.sh  update_package.sh NOT commited (willbe regenerated from official repos soon)

* Mon Jan 09 2017 jvanek <jvanek@redhat.com - 1:1.8.0.111-5.b16
- Added arched dependencies to headless/main package

* Thu Nov 03 2016 jvanek <jvanek@redhat.com - 1:1.8.0.111-3.b16
- added patch207 - PR3183.patch
- java SSL/TLS implementation: should follow the policies of system-wide crypto policy

* Fri Oct 21 2016 Omair Majid <omajid@redhat.com> - 1:1.8.0.111-2.b16
- added dont-add-unnecessary-debug-links.patch
- added hotspot-assembler-debuginfo.patch
- returned accidentally removed  hotspot-remove-debuglink.patch
- eu-readelfs on libraries improved, added gdb call

* Wed Oct 19 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.111-1.b16
- updated to aarch64-jdk8u111-b16 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u111-b16 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u111-b16.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u111-b16.tar.xz as new sources for hotspot
- adapted patches

* Wed Oct 5 2016  Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.102-3.b14
- debug subpackages allowed on aarch64 and ppc64le
- fontconfig and nss restricted by isa

* Wed Aug 31 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.102-2.b14
- declared check_sum_presented_in_spec and used in prep and check
- it is checking that latest packed java.security is mentioned in listing
- @prefix@ in tapsetfiles substitued by prefix as necessary to work with systemtap3 (rhbz1371005)

* Thu Aug 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.102-1.b14
- updated to aarch64-jdk8u102-b14 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u102-b14 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u102-b14.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u102-b14.tar.xz as new sources for hotspot
- removed upstreamed patches 519, 520 and 605
- updated to systemtap 3, removed related patches 300 and 301
- jjs provides moved to headless

* Mon Aug 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-3.b14
- Replace patch for S8162384 with upstream version. Document correctly along with SystemTap RH1204159 patch.
- Resolves: rhbz#1358661
- Replace patch for S8157306 with upstream version, documented & applied on all archs with conditional in patch
- Resolves: rhbz#1360863

* Mon Jul 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.101-2.b14
- added patch532 hotspot-1358661.patch - to fix performance of bimorphic inlining may be bypassed by type speculation
- added patch301 bz1204159_java8.patch - to fix systemtap on multiple jdks

* Mon Jul 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.101-1.b14
- updated to aarch64-jdk8u101-b14 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u101-b14-shenandoah-merge-2016-07-25 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u101-b14.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u101-b14-shenandoah-merge-2016-07-25.tar.xz as new sources for hotspot
- priority lowered for ine zero digit, tip moved to 999
- added jdk6260348-pr3066-gtk_laf_jtextcomponent_not_respecting_desktop_caret_blink_rate.patch, pr3083-rh1346460-for_ssl_debug_return_null_instead_of_exception_when_theres_no_ecc_provider.patch, 8159244-pr3074.patch, corba_typo_fix.patch
renamed: jdk8-archivedJavadoc.patch -> jdk8154313-generated_javadoc_scattered_all_over_the_place.patch, pr2991-rh1341258.patch -> 8158260-pr2991-rh1341258.patch
- not added 8147771-additional_hunk.patch, already in b14

* Tue Jul 12 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-5.b14
- added Provides: /usr/bin/jjs

* Tue Jun 21 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-2.b14
- family restricted by arch

* Tue Jun 07 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-1.b14
- updated to u92
- removed upstreamed patches 8132051-aarch64.patch, 8143855.patch, criticalShenandoahFix.patch, rhbz1206656_fix_current_stack_pointer.patch
- 8132051-zero.patch, remove_aarch64_template_for_gcc6.patch
- jdwpCrash.abrt.patch renamed to 8044762-pr2960.patch
- httpsFix1329342.patch renamed to pr2934-sunec_provider_throwing_keyexception_withine.separator_current_nss_thus_initialise_the_random_number_generator_and_feed_the_seed_to_it.patch
- added known regresisonos fixes for u92 scheduled for next u (519-525)

* Thu May 19 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-7.b14
- added patch519, jdwpCrash.abrt.patch to fix trasnportation error

* Fri May 13 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-6.b14
- Enable weak reference discovery in ShenandoahMarkCompact. Otherwise we never process any weak references in full-gc.

* Tue May 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-5.b14
- Restricted to depend on exactly same version of nss as used for build
- Resolves: rhbz#1332456

* Tue May 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-4.b14
- updated to aarch64-shenandoah-jdk8u71-b15-beta02 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u71-b15-beta02.tar.xz as new sources for hotspot
- reverted  nss version fix

* Mon Apr 25 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-4.b14
- Restricted to depend on exactly same version of nss as use dfor build
- Resolves: rhbz#1332456

* Mon Apr 25 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-3.b14
- included shenandoah support in 64b intel

* Sun Apr 24 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-2.b14
- added patch518 httpsFix1329342.patch
- test based on SOURCE14 enabled
- Resolves: rhbz#1329342

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Roll back release number as release 1 never succeeded, even with tests disabled.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add additional fix to Zero patch to properly handle result on 64-bit big-endian
- Revert debugging options (aarch64 back to JIT, product build, no -Wno-error)
- Enable full bootstrap on all architectures to check we are good to go.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn tests back on or build will not fail.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Temporarily remove power64 from JIT arches to see if endian issue appears on Zero.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn off Java-based checks in a vain attempt to get a complete build.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn off -Werror so s390 can build in slowdebug mode.
- Add fix for formatting issue found by previous s390 build.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Revert settings to production defaults so we can at least get a build.
- Switch to a slowdebug build to try and unearth remaining issue on s390x.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Disable ECDSA test for now until failure on RHEL 7 is fixed.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add 8132051 port to Zero.
- Turn on bootstrap build for all to ensure we are now good to go.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add 8132051 port to AArch64.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Enable a full bootstrap on JIT archs. Full build held back by Zero archs anyway.
- Resolves: rhbz#1325423

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Use basename of test file to avoid misinterpretation of full path as a package
- Resolves: rhbz#1325423

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Update to u91b14.
- Resolves: rhbz#1325423

* Mon Apr 04 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.77-2.b03
- added patch400  jdk8-archivedJavadoc.patch
- added javadoc-zip(-debug) subpackage with compressed javadoc

* Thu Mar 31 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-3.b03
- Fix typo in test invocation.
- Resolves: rhbz#1245810

* Thu Mar 31 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-3.b03
- Add ECDSA test to ensure ECC is working.
- Resolves: rhbz#1245810

* Wed Mar 30 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-2.b03
- Avoid WithSeed versions of NSS functions as they do not fully process the seed
- List current java.security md5sum so that java.security is replaced and ECC gets enabled.
- Resolves: rhbz#1245810

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Update to u77b03.

* Thu Mar 03 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-13.b16
- When using a compositing WM, the overlay window should be used, not the root window.

* Mon Feb 29 2016 Omair Majid <omajid@redhat.com> - 1:1.8.0.72-12.b15
- Use a simple backport for PR2462/8074839.
- Don't backport the crc check for pack.gz. It's not tested well upstream.

* Mon Feb 29 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-5.b16
- Fix regression introduced on s390 by large code cache change.
- Update to u72b16.
- Drop 8147805 and jvm.cfg fix which are applied upstream.

* Wed Feb 24 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-11.b15
- Add patches to allow the SunEC provider to be built with the system NSS install.
- Re-generate source tarball so it includes ecc_impl.h.
- Adjust tarball generation script to allow ecc_impl.h to be included.
- Bring over NSS changes from java-1.7.0-openjdk spec file (NSS_CFLAGS/NSS_LIBS)
- Remove patch which disables the SunEC provider as it is now usable.
- Correct spelling mistakes in tarball generation script.
- Move completely unrelated AArch64 gcc 6 patch into separate file.
- Resolves: rhbz#1019554 (fedora bug)

* Tue Feb 23 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-10.b15
- returning accidentlay removed hunk from renamed and so wrongly merged remove_aarch64_jvm.cfg_divergence.patch

* Mon Feb 22 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-9.b15
- sync from rhel

* Tue Feb 16 2016 Dan Horák <dan[at]danny.cz> - 1:1.8.0.72-8.b15
- Refresh s390-java-opts patch

* Tue Feb 16 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-7.b15
- Use -fno-lifetime-dse over -fno-guess-branch-probability.
  See RHBZ#1306558.

* Mon Feb 15 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-6.b15
- Add aarch64_FTBFS_rhbz_1307224.patch so as to resolve RHBZ#1307224.

* Fri Feb 12 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-5.b15
- Add -fno-delete-null-pointer-checks -fno-guess-branch-probability flags to resolve x86/x86_64 crash.

* Mon Feb 08 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-5.b15
- Explicitly set the C++ standard to use, as the default has changed to C++ 2014 in GCC 6.
- Turn off -Werror due to format warnings in HotSpot and -std usage warnings in SCTP.
- Run tests under the check stage and use the debug build first.

* Fri Feb 05 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-4.b15
- Backport S8148351: Only display resolved symlink for compiler, do not change path

* Wed Feb 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-3.b15
* touch -t 201401010000 java.security to try to worakround md5sums

* Wed Jan 27 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-1.b15
- updated to aarch64-jdk8u72-b15 (from aarch64-port/jdk8u)
- used aarch64-port-jdk8u-aarch64-jdk8u72-b15.tar.xz as new sources
- removed already upstreamed patch501 8146566.patch

* Wed Jan 20 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.71-1.b15
- sync with rhel7
- security update to CPU 19.1.2016 to u71b15

* Tue Dec 15 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-14.b17
- pretrans moved back to lua nd now includes file from copy-jdk-configs instead of call it

* Tue Dec 15 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.65-13.b17
- Disable hardened build on non-JIT arches.
  Workaround for RHBZ#1290936.

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-12.b17
-removed patch4 java-1.8.0-openjdk-PStack-808293.patch
-removed patch13 libjpeg-turbo-1.4-compat.patch

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-11.b17
- Define our own optimisation flags based on the optflags macro and pass to OpenJDK build cflags/cxxflags.
- Remove -fno-devirtualize as we are now on GCC 5 where the GCC bug it worked around is fixed.
- Pass __global_ldflags to --with-extra-ldflags so Fedora linker flags are used in the build.
- Also Pass ourcppflags to the OpenJDK build cflags as it wrongly uses them for the HotSpot C++ build.
- Add PR2428, PR2462 & S8143855 patches to fix build issues that arise.
- Resolves: rhbz#1283949
- Resolves: rhbz#1120792

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-10.b17
- Add patch to honour %%{_smp_ncpus_max} from Tuomo Soini
- Resolves: rhbz#1152896

* Wed Dec 09 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-9.b17
- extracted lua scripts moved from pre where they don't work to pretrans
- requirement on copy-jdk-configs made Week.

* Tue Dec 08 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-8.b17
- used extracted lua scripts.
- now depnding on copy-jdk-configs
- config files persisting in pre instead of %%pretrans

* Tue Dec 08 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-7.b17
- changed way of generating the sources. As result:
- "updated" to aarch64-jdk8u65-b17 (from aarch64-port/jdk8u60)
- used aarch64-port-jdk8u60-aarch64-jdk8u65-b17.tar.xz as new sources

* Fri Nov 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-5.b17
- added missing md5sums
- moved to bundeld lcms

* Wed Nov 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-4.b17
- debug packages priority lowered by 1

* Wed Nov 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-3.b17
- depends on chkconfig >1.7 - added --family support

* Fri Nov 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-2.b17
- added and applied patch605 soundFontPatch.patch as repalcement for removed sound font links
- removed hardcoded soundfont links

* Thu Nov 12 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-1.b17
- updated to u65b17

* Mon Nov 09 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-17.b28
- policytool  manpage followed the binary from devel to jre

* Mon Nov 02 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-16.b28
added and applied patch604: aarch64-ifdefbugfix.patch to fix rhbz1276959

* Thu Oct 15 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-15.b28
- moved to single source integration forest
- removed patch patch9999 enableArm64.patch
- removed patch patch600  %%{name}-rh1191652-hotspot.patch

* Thu Aug 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-14.b24
- updated aarch64 tarball to contain whole forest of latest jdk8-aarch64-jdk8u60-b24.2.tar.xz
- using this forest instead of only hotspot
- generate_source_tarball.sh - temporarily excluded repos="hotspot" compression of download
- not only openjdk/hotspot is replaced, by wholeopenjdk
- ln -s openjdk jdk8 done after replacing of openjdk
- patches 9999 601 and 602 exclded for aarch64

* Wed Aug 26 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-13.b24
- updated aarch64 hotpost to latest jdk8-aarch64-jdk8u60-b24.2.tar.xz

* Wed Aug 19 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-12.b24
- updated to freshly released jdk8u60-jdk8u60-b27

* Thu Aug 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-11.b24
- another touching attempt to polycies...

* Mon Aug 03 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-10.b24
- arch64 updated to u60-b24 with hope to fix rhbz1249037

* Fri Jul 17 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-3.b24
- added one more md5sum test (thanx to Severin!)
 - I guess one more missing
- doubled slash in md5sum test in post

* Thu Jul 16 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-2.b24
- updated to security u60-b24
- moved to openjdk instead of jdk8 topdir in sources
- removed upstreamed patch99 java-1.8.0-openjdk-linux-4.x.patch
- removed upstreamed patch503 pr2444.patch
- removed upstreamed patch505 1208369_memory_leak_gcc5.patch
- removed upstreamed patch506: gif4.1.patch
 - note: usptream version is suspicious
  GIFLIB_MAJOR >= 5 SplashStreamGifInputFunc, NULL
  ELSE SplashStreamGifInputFunc
 - but the condition seems to be viceversa


* Mon Jun 22 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.60-7.b16
- Require javapackages-tools instead of jpackage-utils.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.60-6.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 09 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.60-5.b16
- allow build on Linux 4.x kernel
- refresh s390 size_t patch

* Fri Jun 05 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-4.b16
- added requires lksctp-tools for headless subpackage to make sun.nio.ch.sctp work

* Mon May 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-2.b16
- Patch503 d318d83c4e74.patch, patch505 1208369_memory_leak_gcc5.patch (and patch506 gif4.1.patch)
   moved out of "if with_systemtap" block

* Mon May 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-1.b16
- updated to u60b16
- deleted upstreamed patches:
   patch501 1182011_JavaPrintApiDoesNotPrintUmlautCharsWithPostscriptOutputCorrectly.patch
   patch502 1182694_javaApplicationMenuMisbehave.patch
   patch504 1210739_dns_naming_ipv6_addresses.patch
   patch402 atomic_linux_zero.inline.hpp.patch
   patch401 fix_ZERO_ARCHDEF_ppc.patch
   patch400 ppc_stack_overflow_fix.patch
   patch204 zero-interpreter-fix.patch
- added Patch506 gif4.1.patch to allow build agaisnt giflib > 4.1

* Wed May 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-38.b14
- updated to 8u45-b14 with hope to fix rhbz#1123870

* Wed May 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-37.b13
- added runtime requires for tzdata
- Remove reference to tz.properties which is no longer used (by gnu.andrew)

* Wed Apr 29 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.45-36.b13
- Patch hotspot to not use undefined code rather than passing
  -fno-tree-vrp via CFLAGS.
  Resolves: RHBZ#1208369
- Add upstream patch for DNS nameserver issue with IPv6 addresses.
  Resolves: RHBZ#1210739

* Wed Apr 29 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-35.b13
- Omit jsa files from power64 file list as well, as they are never generated
- moved to boot build by openjdk8
- Use the template interpreter on ppc64le

* Fri Apr 10 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-31.b13
- repacked sources

* Tue Apr 07 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-30.b13
- updated to security u45
- removed patch6: disable-doclint-by-default.patch
- added patch d318d83c4e74.patch
- added  rhbz1206656_fix_current_stack_pointer.patch
- renamed PStack-808293.patch -> java-1.8.0-openjdk-PStack-808293.patch
- renamed remove-intree-libraries.sh -> java-1.8.0-openjdk-remove-intree-libraries.sh
- renamed to preven conflix with jdk7

* Fri Apr 03 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-27.b25
- Add -fno-tree-vrp to flags to prevent hotspot miscompilation.
- Resolves: RHBZ#1208369

* Thu Apr 02 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-27.b25
- bumped release. Needed rebuild by itself on arm

* Tue Mar 31 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.40-26.b25
- Make Zero build-able on ARM32.
  Resolves: RHBZ#1206656

* Fri Mar 27 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.40-25.b25
- refresh s390 patches

* Fri Mar 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-24.b25
- added patch501 1182011_JavaPrintApiDoesNotPrintUmlautCharsWithPostscriptOutputCorrectly.patch
- added patch502 1182694_javaApplicationMenuMisbehave.patch
- both upstreamed, will be gone with u60

* Wed Mar 25 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-23.b25
- Disable various EC algorithms in configuration

* Mon Mar 23 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-22.b25
- sytemtap made working for dual package

* Tue Mar 03 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.40-21.b25
- Added compiler no-warn-

* Fri Feb 20 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-21.b25
- Fix zero interpreter build.

* Thu Feb 12 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-21.b25
- Fix building with gcc 5 by ignoring return-local-addr warning
- Include additional debugging info for java class files and test that they are
  present

* Thu Feb 12 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-20.b25
- bumped to b25
- removed upstreamed patch11 hotspot-build-j-directive.patch
- policies repacked to stop spamming yum update
- added and used source20 repackReproduciblePolycies.sh
- added mehanism to force priority size

* Fri Jan 09 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.40-19.b12
- refresh s390 patches

* Fri Nov 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-18.b12
- updated arm64 tarball to jdk8-jdk8u40-b12-aarch64-1263.tar.xz

* Fri Nov 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-17.b12
- obsoleted gcj and sindoc. rh1149674 and rh1149675
- removed backup/restore on images and docs in favor of reconfigure in different directory

* Mon Nov 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-16.b12
- updated both noral and aarch64 tarballs to u40b12

* Mon Nov 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-15.b02
- enabled debug packages
- removed all provides duplicating package name
- comments about files moved inside files section (to prevent different javadoc postuns)
 - see (RH1160693)

* Fri Oct 31 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-13.b02
- Build against libjpeg-turbo-1.4

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-13.b02
- preparing for parallel debug+normal build
- files and scripelts moved to extendable macros as first step to dual build
- install and build may be done in loop for both release and slowdebug
- debugbuild off untill its completed

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-12.b02
- added patch12,removeSunEcProvider-RH1154143
- xdump excluded from ppc64le (rh1156151)
- Add check for src.zip completeness. See RH1130490 (by sgehwolf@redhat.com)
- Resolves: rhbz#1125260

* Thu Sep 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-11.b02
- fixing flags usages (thanx to jerboaa!)

* Thu Sep 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-10.b26
- sync with rhel7

* Wed Sep 17 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-9.b26
- Remove LIBDIR and funny definition of _libdir.
- Fix rpmlint warnings about macros in comments.

* Thu Sep 11 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-8.b26
- fixed headless to become headless again
 - jre/bin/policytool added to not headless exclude list

* Wed Sep 10 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-7.b26
- Update aarch64 hotspot to latest upstream version

* Fri Sep 05 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-6.b26
- Use %%{power64} instead of %%{ppc64}.

* Thu Sep 04 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-5.b26
- Update aarch64 hotspot to jdk7u40-b02 to match the rest of the JDK
- commented out patch2 (obsolated by 666)
- all ppc64 added to jitarches

* Thu Sep 04 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-4.b26
- Use the cpp interpreter on ppc64le.

* Wed Sep 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-3.b26
- fixed RH1136544, orriginal issue, state of pc64le jit remians mistery

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-2.b26
- requirement Requires: javazi-1.8/tzdb.dat changed to tzdata-java >= 2014f-1
- see RH1130800#c5

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b02
- adapted aarch64 patch
- removed upstreamed patch  0001-PPC64LE-arch-support-in-openjdk-1.8.patch

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b02
- updated to u40-b02
- adapted aarch64 patches

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b01
- updated to u40-b01
- adapted  rh1648242-accessible_toolkit_crash_do_not_break_jvm.patch
- adapted  jdk8042159-allow_using_system_installed_lcms2.patch
- removed patch8 set-active-window.patch
- removed patch9 javadoc-error-jdk-8029145.patch
- removed patch10 javadoc-error-jdk-8037484.patch
- removed patch99 applet-hole.patch - itw 1.5.1 is able to ive without it

* Tue Aug 19 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-19.b12
- fixed desktop icons
- Icon set to java-1.8.0
- Development removed from policy tool

* Mon Aug 18 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-18.b12
- fixed jstack

* Mon Aug 18 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-17.b12
- added build requires and requires for headles  _datadir/javazi-1.8/tzdb.dat
- restriction of tzdata provider, so we will be aware of another possible failure

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org>
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Aug 14 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-15.b12
- fixed provides/obsolates

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-14.b12
- forced to build in fully versioned dir

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-13.b12
- fixing tapset to support multipleinstalls
- added more config/norepalce
- policitool moved to jre

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-12.b12
- bumped release to build by previous release.
- forcing rebuild by jdk8
- uncommenting forgotten comment on tzdb link

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-11.b12
- backporting old fixes:
- get rid of jre-abrt, uniquesuffix, parallel install, jsa files,
  config(norepalce) bug, -fstack-protector-strong, OrderWithRequires,
  nss config, multilib arches, provides/requires excludes
- some additional cosmetic changes

* Tue Jul 22 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.11-8.b12
- Modify aarch64-specific jvm.cfg to list server vm first

* Mon Jul 21 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-7.b12
- removed legacy aarch64 switches
 - --with-jvm-variants=client and  --disable-precompiled-headers

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-6.b12
- added patch patch9999 enableArm64.patch to enable new hotspot

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-5.b12
- Attempt to update aarch64 *jdk* to u11b12, by resticting aarch64 sources to hotpot only

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-1.b12
- updated to security u11b12

* Tue Jun 24 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-13.b13
- Obsolete java-1.7.0-openjdk

* Wed Jun 18 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-12.b13
- Use system tzdata from tzdata-java

* Thu Jun 12 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-11.b13
- Add patch from IcedTea to handle -j and -I correctly

* Wed Jun 11 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-11.b13
- Backport javadoc fixes from upstream
- Related: rhbz#1107273

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.5-10.b13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun 02 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-9.b13
- Build with OpenJDK 8

* Wed May 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-8.b13
- Backport fix for JDK-8012224

* Wed May 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-7.b13
- Require fontconfig and minimal fonts (xorg-x11-fonts-Type1) explicitly
- Resolves rhbz#1101394

* Fri May 23 2014 Dan Horák <dan[at]danny.cz> - 1:1.8.0.5-6.b13
- Enable build on s390/s390x

* Tue May 20 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-5.b13
- Only check for debug symbols in libjvm if it exists.

* Fri May 16 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-4.b13
- Include all sources in src.zip

* Mon Apr 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-4.b13
- Check for debug symbols in libjvm.so

* Thu Apr 24 2014 Brent Baude <baude@us.ibm.com> - 1:1.8.0.5-3.b13
- Add ppc64le support, bz# 1088344

* Wed Apr 23 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-2.b13
- Build with -fno-devirtualize
- Don't strip debuginfo from files

* Wed Apr 16 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-1.b13
- Instrument build with various sanitizers.

* Tue Apr 15 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-1.b13
- Update to the latest security release: OpenJDK8 u5 b13

* Fri Mar 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-2.b132
- Include version information in desktop files
- Move desktop files from tarball to top level source

* Tue Mar 25 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-1.0.b132
- Switch from java8- style provides to java- style
- Bump priority to reflect java version

* Fri Mar 21 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.35.b132
- Disable doclint for compatiblity
- Patch contributed by Andrew John Hughes

* Tue Mar 11 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.34.b132
- Include jdeps and jjs for aarch64. These are present in b128.

* Mon Mar 10 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.33.b132
- Update aarch64 tarball to the latest upstream release

* Fri Mar 07 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.32.b132
- Fix `java -version` output

* Fri Mar 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.31.b132
- updated to rc4 aarch64 tarball
- outdated removed: patch2031 system-lcmsAARCH64.patch patch2011 system-libjpeg-aarch64.patch
  patch2021 system-libpng-aarch64.patch

* Thu Mar 06 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.30.b132
- Update to b132

* Thu Mar 06 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.29.b129
- Fix typo in STRIP_POLICY

* Mon Mar 03 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.28.b129
- Remove redundant debuginfo files
- Generate complete debug information for libjvm

* Tue Feb 25 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.27.b129
- Fix non-headless libraries

* Tue Feb 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.26.b129
- Fix incorrect Requires

* Thu Feb 13 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.26.b129
- Add -headless subpackage based on java-1.7.0-openjdk
- Add abrt connector support
- Add -accessibility subpackage

* Thu Feb 13 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.26.b129
- Update to b129.

* Fri Feb 07 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.25.b126
- Update to candidate Reference Implementation release.

* Fri Jan 31 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.24.b123
- Forward port more patches from java-1.7.0-openjdk

* Mon Jan 20 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.23.b123
- Update to jdk8-b123

* Thu Nov 14 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.22.b115
- Update to jdk8-b115

* Wed Oct 30 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.21.b106
- added jre/lib/security/blacklisted.certs for aarch64
- updated to preview_rc2 aarch64 tarball

* Sun Oct 06 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.20.b106
- Fix paths in tapsets to work on non-x86_64
- Use system libjpeg

* Thu Sep 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.19.b106
- Fix with_systemtap conditionals

* Thu Sep 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.18.b106
- Update to jdk8-b106

* Tue Aug 13 2013 Deepak Bhole <dbhole@redhat.com> - 1:1.8.0.0-0.17.b89x
- Updated aarch64 to latest head
- Dropped upstreamed patches

* Wed Aug 07 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- The zero fix only applies on b89 tarball

* Tue Aug 06 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- Add patch to fix zero on 32-bit build

* Mon Aug 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- Added additional build fixes for aarch64

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.0-0.16.b89x
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Aug 02 2013 Deepak Bhole <dbhole@redhat.com> - 1:1.8.0.0-0.15.b89
- Added a missing includes patch (#302/%%{name}-arm64-missing-includes.patch)
- Added --disable-precompiled-headers for arm64 build

* Mon Jul 29 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.14.b89
- added patch 301 - removeMswitchesFromx11.patch

* Fri Jul 26 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.13.b89
- added new aarch64 tarball

* Thu Jul 25 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.12.b89
- ifarchaarch64 then --with-jvm-variants=client

* Tue Jul 23 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.11.b89
- prelink dependence excluded also for aaech64
- arm64 added to jitarches
- added source100 config.guess to repalce the outdated one in-tree
- added source101 config.sub  to repalce the outdated one in-tree
- added patch2011 system-libjpegAARCH64.patch (as aarch64-port is little bit diferent)
- added patch2031 system-lcmsAARCH64.patch (as aarch64-port is little bit diferent)
- added gcc-c++ build depndece so builddep will  result to better situation

* Tue Jul 23 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.10.b89
- moved to latest working osurces

* Tue Jul 23 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.10.b89
- Moved  to hg clone for generating sources.

* Sun Jul 21 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.9.b89
- added aarch 64 tarball, proposed usage of clone instead of tarballs

* Mon Jul 15 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.9.b89
- Switch to xz for compression
- Fixes RHBZ#979823

* Mon Jul 15 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.9.b89
- Priority should be 0 until openjdk8 is released by upstream
- Fixes RHBZ#964409

* Mon Jun 3 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.8.b89
- Fix incorrect permissions on ct.sym

* Mon May 20 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.7.b89
- Fix incorrect permissions on jars

* Fri May 10 2013 Adam Williamson <awilliam@redhat.com>
- update scriptlets to follow current guidelines for updating icon cache

* Tue Apr 30 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.5.b87
- Update to b87
- Remove all rhino support; use nashorn instead
- Remove upstreamed/unapplied patches

* Tue Apr 23 2013 Karsten Hopp <karsten@redhat.com> 1:1.8.0.0-0.4.b79
- update java-1.8.0-openjdk-ppc-zero-hotspot patch
- use power64 macro

* Thu Mar 28 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.3.b79
- Add build fix for zero
- Drop gstabs fixes; enable full debug info instead

* Wed Mar 13 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.2.b79
- Fix alternatives priority

* Tue Mar 12 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.1.b79.f19
- Update to jdk8-b79
- Initial version for Fedora 19

* Tue Sep 04 2012 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.0-b53.1
- Initial build from java-1.7.0-openjdk RPM

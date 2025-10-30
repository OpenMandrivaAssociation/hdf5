%global	_disable_ld_no_undefined 0
# Needed because we mix different compilers (clang and gfortran)
%global	_disable_lto 1

%define	major	310
%define	hl_major	310
%define	forfan_major	310

%define	libname %mklibname hdf5
%define	libname_hl %mklibname hdf5_hl
%define	devname %mklibname %{name} -d

# As of 1.14.6, building fortran bindings
# with cmake is broken, so for now we'll continue
# with autoconf
%bcond_with cmake

# Optionally run checks
%bcond_with check

Summary:	High-performance data management and storage suite
Name:	hdf5
Version:	1.14.6
Release:	1
#See included COPYING
License:	distributable
Group:	System/Libraries
Url:		https://www.hdfgroup.org/HDF5/
# Also: https://portal.hdfgroup.org/display/support/Downloads
Source0:	https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-%(echo %{version}|cut -d. -f1-2)/hdf5-%(echo %{version}|cut -d_ -f1)/src/hdf5-%(echo %{version}|sed -e 's,_,-,g').tar.gz
Source100:	hdf5.rpmlintrc
Patch0:		hdf5-1-14.6-fix-shebang.patch
%if %{with cmake}
BuildRequires:	cmake >= 3.24
BuildRequires:	ninja
%endif
BuildRequires:	gcc-gfortran
BuildRequires:	jdk-current
%ifnarch %{armx} riscv64
BuildRequires:	atomic-devel
BuildRequires:	quadmath-devel
%endif
#BuildRequires:	szip-devel
BuildRequires:	pkgconfig(krb5)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(libjpeg)
BuildRequires:	pkgconfig(ompi)
BuildRequires:	pkgconfig(openssl)
BuildRequires:	pkgconfig(zlib)

%description
HDF5 is a library and file format for storing scientific data. It was designed
to address some of the limitations of the HDF 4.x library and to address
current and anticipated requirements of modern systems and applications.
HDF5 includes the following improvements:
- A new file format designed to address some of the deficiencies of HDF4.x,
  particularly the need to store larger files and more objects per file.
- A simpler, more comprehensive data model that includes only two basic
  structures: a multidimensional array of record structures and a grouping
  structure.
- A simpler, better-engineered library and API, with improved support for
  parallel i/o, threads, and other requirements imposed by modern systems
  and applications.

%files
%doc COPYING release_docs/RELEASE.txt
%{_bindir}/h5*

#-----------------------------------------------------------------------------

%package -n %{libname}
Summary:	HDF5 libraries
Group:	System/Libraries

%description -n %{libname}
This package contains the libraries needed to run programs dynamically
linked with hdf5 libraries.

%files -n %{libname}
%{_libdir}/libhdf5.so.%{major}*
%{_libdir}/libhdf5_cpp.so.%{major}*
%{_libdir}/libhdf5_fortran.so.%{forfan_major}*

#-----------------------------------------------------------------------------

%package -n %{libname_hl}
Summary:	HDF5 high level libraries
Group:		System/Libraries

%description -n %{libname_hl}
This package contains the high level libraries needed to run programs
dynamically linked with hdf5 libraries.

%files -n %{libname_hl}
%{_libdir}/libhdf5_hl.so.%{hl_major}*
%{_libdir}/libhdf5_hl_cpp.so.%{hl_major}*
%{_libdir}/libhdf5hl_fortran.so.%{hl_major}*

#-----------------------------------------------------------------------------

%package -n %{devname}
Summary:	Devel libraries and header files for hdf5 development
Group:		Development/C
Provides:	%{name}-devel = %{version}-%{release}
Provides:	%{libname}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}
Requires:	%{libname_hl} = %{version}
%rename	%{_lib}hdf5-static-devel

%description -n %{devname}
This package provides devel libraries and header files needed
for develop applications requiring the "hdf5" library.

%files -n %{devname}
%{_libdir}/*.so
%{_libdir}/libhdf5.settings
%{_includedir}/*.h
%{_includedir}/*.inc
%{_includedir}/*.mod
#{_datadir}/hdf5_examples/

#-----------------------------------------------------------------------------

%package -n java-hdf5
Summary:	Java library for dealing with data in the HDF5 file format
Group:		Development/Java

%description -n java-hdf5
Java library for dealing with data in the HDF5 file format.

%files -n java-hdf5
%{_datadir}/java/*.jar

#-----------------------------------------------------------------------------

%prep
%autosetup -p1 -n %{name}-%(echo %{version}|sed -e 's,_,-,g')

find -name '*.[ch]' -o -name '*.f90' -exec chmod -x {} +


%build
find %{buildroot} -type f -size 0 -name Dependencies -print0 |xargs -0 rm -f
find %{buildroot} -type f -size 0 -name .depend -print0 |xargs -0 rm -f

. %{_sysconfdir}/profile.d/90java.sh

%if %{with cmake}
%cmake \
	-DHDF5_BUILD_CPP_LIB:BOOL=ON \
	-DHDF5_BUILD_FORTRAN:BOOL=ON \
	-DHDF5_BUILD_GENERATORS:BOOL=ON \
	-DHDF5_BUILD_JAVA:BOOL=ON \
	-DHDF5_BUILD_PARALLEL_TOOLS:BOOL=ON \
	-DHDF5_ENABLE_MAP_API:BOOL=ON \
	-DHDF5_ENABLE_MIRROR_VFD:BOOL=ON \
	-DHDF5_ENABLE_ROS3_VFD:BOOL=ON \
	-DHDF5_GENERATE_HEADERS:BOOL=ON \
	-DHDF5_USE_GNU_DIRS:BOOL=ON \
	-DZLIB_USE_EXTERNAL:BOOL=ON \
	-G Ninja

%ninja_build
%else
# Dropped unused options: --enable-fortran2003 --enable-linux-lfs
%configure \
	--disable-static \
	--disable-dependency-tracking \
	--enable-cxx \
	--enable-java \
	--enable-fortran \
	--with-pthread \
	--enable-build-mode=production

%make_build
%endif


%install
. %{_sysconfdir}/profile.d/90java.sh

mkdir -p %{buildroot}%{_libdir} %{buildroot}%{_datadir}/java
%if %{with cmake}
%ninja_install -C build
%else
%make_install
%endif

mv %{buildroot}%{_libdir}/jarhdf5*.jar %{buildroot}%{_datadir}/java
cd %{buildroot}%{_datadir}/java
ln -s jarhdf5*.jar jarhdf5.jar


%if %{with check}
%check
# All tests must pass on the following architectures
%ifarch %{ix86} x86_64
%make check || echo "make check failed"
%else
%make -k check || echo "make check failed"
%endif
%endif

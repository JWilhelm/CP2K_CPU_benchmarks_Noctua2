#!/bin/bash
# Fresh clone of CP2K master and a fresh CMake configuration (foss/2025b, libint 2.11.2, libxc 7.1.2,
# DBCSR 2.10.0, libxsmm 2.1.0, GreenX 2.2, libwignernj 0.8.0) into runtime_master. Run on a Noctua 2 login node.
set -eo pipefail
R=/scratch/hpc-prf-dyncrys/eprop2d1_Jan/34_CP2K_benchmarks_LRZ
B=$R/build
S=/opt/software/pc2/SPACK/spack/opt/spack/linux-zen3
G=/scratch/hpc-prf-dyncrys/eprop2d1_Jan/32_RTBSE_RI_AUTO_RIRS_OPTIMIZATION/0000_build/greenx
mkdir -p $B/tmp; export TMPDIR=$B/tmp
module --force purge; module load DefaultModules toolchain/foss/2025b
CM=/opt/software/pc2/EB-SW/software/CMake/3.31.8-GCCcore-14.3.0/bin/cmake
[ -d $B/source ] || git clone -q https://github.com/cp2k/cp2k.git $B/source
cd $B/source && git log -1 --format="%h %ad %s" --date=short
# libwignernj 0.8.0 (required by CP2K master since Nov 2026), as tools/toolchain/scripts/stage7/install_libwignernj.sh
W=$B/libwignernj
if [ ! -f $W/install/lib/cmake/wignernj/wignernjConfig.cmake ] && [ ! -d $W/install/lib/cmake ]; then
  mkdir -p $W && cd $W
  [ -f libwignernj-0.8.0.tar.gz ] || curl -fsSLo libwignernj-0.8.0.tar.gz https://www.cp2k.org/static/downloads/libwignernj-0.8.0.tar.gz
  echo "7220cea92652040d6456aba92ff151124d9c69ce8695840490c18dd25a0da80c  libwignernj-0.8.0.tar.gz" | sha256sum -c
  rm -rf libwignernj-0.8.0 && tar -xzf libwignernj-0.8.0.tar.gz && cd libwignernj-0.8.0
  $CM -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$W/install -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF -DWIGNERNJ_BUILD_FORTRAN=OFF -DWIGNERNJ_BUILD_TESTS=OFF \
    -DWIGNERNJ_BUILD_CXX_TESTS=OFF -DWIGNERNJ_BUILD_EXAMPLES=OFF -DWIGNERNJ_BUILD_LTO=OFF > $W/cmake.log 2>&1
  $CM --build build --target install -j 16 > $W/build.log 2>&1
  echo WIGNERNJ_OK
fi
export LIBRARY_PATH=$G/gmp/lib:$LIBRARY_PATH CPATH=$G/gmp/include:$CPATH LD_LIBRARY_PATH=$G/gmp/lib:$LD_LIBRARY_PATH
$CM -S $B/source -B $B/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_Fortran_COMPILER=gfortran \
  -DCMAKE_PREFIX_PATH="$G/install;$G/gmp;$W/install" \
  -DCP2K_USE_MPI=ON -DCP2K_BLAS_VENDOR=OpenBLAS -DCP2K_BLAS_THREADING=gnu-thread -DCP2K_SCALAPACK_VENDOR=GENERIC \
  -DCP2K_USE_LIBINT2=ON -DLibint2_DIR=$S/libint-2.11.2-sor7fly756f6owyx6oworvpap6ofjdcy/lib/cmake/libint2 \
  -DCP2K_USE_LIBXC=ON -DLibxc_DIR=$S/libxc-7.1.2-blvek6q64thlh334bczaedil5wqw22ki/lib64/cmake/Libxc \
  -DDBCSR_DIR=$S/dbcsr-2.10.0-pccg3sb2vobymsktjlzkq4xs6afvmstw/lib64/cmake/dbcsr \
  -DCP2K_USE_LIBXSMM=ON -Dlibxsmm_DIR=$S/libxsmm-2.1.0-de3aroyxuccnwlzjtgy3xynjpqdbrjmg/lib64/cmake/libxsmm \
  -Dlibxs_DIR=$S/libxs-1.0.0-buuvydmk4zba2nn3soeyfz5pgc5zyiut/lib64/cmake/libxs \
  -DBoost_INCLUDE_DIR=$S/boost-1.90.0-7k43d4v3zsmyviyoxl6rguwfrmkyx3de/include \
  -DCP2K_USE_GREENX=ON > $B/configure.log 2>&1 || { tail -40 $B/configure.log; echo CLAUDE_CONFIGURE_FAIL; exit 1; }
$CM --build $B/build --target cp2k-bin -j 32 > $B/build.log 2>&1 || { grep -B2 -A12 -i "error" $B/build.log | head -80; echo CLAUDE_BUILD_FAIL; exit 1; }
mkdir -p $B/runtime_master; cp $B/build/bin/cp2k.psmp $B/build/src/libcp2k.so.* $B/runtime_master/
cp -P $G/install/lib/lib*.so* $G/gmp/lib/libgmp*.so* $B/runtime_master/
LD_LIBRARY_PATH=$B/runtime_master:$LD_LIBRARY_PATH ldd $B/runtime_master/cp2k.psmp | grep -iE "not found" || true
echo CLAUDE_BUILD_OK

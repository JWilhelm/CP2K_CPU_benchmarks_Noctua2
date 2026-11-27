#!/bin/bash
# Diamond k-point transform timings of cp2k/cp2k#6454: 8 MPI ranks x 1 OpenMP thread, all inputs one after the other.
#SBATCH --account=hpc-prf-dyncrys
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=60000M
#SBATCH --time=2:00:00
module --force purge
module load DefaultModules toolchain/foss/2025b
B=/scratch/hpc-prf-dyncrys/eprop2d1_Jan/34_CP2K_benchmarks_LRZ/build
export LD_LIBRARY_PATH=$B/runtime_master:${LD_LIBRARY_PATH:-} CP2K_DATA_DIR=$B/source/data OMP_NUM_THREADS=1
for f in diamond_k4_GEMM diamond_k4_FFT diamond_k6_GEMM diamond_k6_FFT diamond_k8_GEMM diamond_k8_FFT diamond_k10_GEMM diamond_k10_FFT diamond_k20_GEMM diamond_k20_FFT diamond_k30_GEMM diamond_k30_FFT; do
  srun --ntasks=8 --cpus-per-task=1 --cpu-bind=cores $B/runtime_master/cp2k.psmp -i $f.inp -o $f.out > $f.stdout 2>&1
  echo "$f $(grep -E '^ CP2K  ' $f.out | awk '{print $NF}')"
done

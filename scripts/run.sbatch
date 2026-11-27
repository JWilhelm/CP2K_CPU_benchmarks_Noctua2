#!/bin/bash
# One CP2K benchmark run. Submitted by submit_all.sh with --nodes/--ntasks/--time set per case.
# 8 OpenMP threads per MPI rank, 16 ranks per full node (8 ranks on a half node).
#SBATCH --account=hpc-prf-dyncrys
#SBATCH --partition=normal
#SBATCH --qos=cont
#SBATCH --cpus-per-task=8
set -uo pipefail
module --force purge
module load DefaultModules toolchain/foss/2025b
# RT = folder with cp2k.psmp (default: newest master), DATA = CP2K data directory of that build
B=/scratch/hpc-prf-dyncrys/eprop2d1_Jan/34_CP2K_benchmarks_LRZ/build
RT=${RT:-$B/runtime_master}
export LD_LIBRARY_PATH=$RT:${LD_LIBRARY_PATH:-}
export CP2K_DATA_DIR=${DATA:-$B/source/data}
export OMP_NUM_THREADS=8 OMP_PROC_BIND=close OMP_PLACES=cores OMP_STACKSIZE=256M OPENBLAS_NUM_THREADS=1
ulimit -s unlimited
echo "binary $RT data $CP2K_DATA_DIR"
echo "start $(date +%s) nodes $SLURM_JOB_NUM_NODES ranks $SLURM_NTASKS host $(hostname)"
srun --ntasks=$SLURM_NTASKS --cpus-per-task=8 --cpu-bind=cores --distribution=block:block \
  $RT/cp2k.psmp -i input.inp -o output.out > cp2k.stdout 2> cp2k.stderr
echo "end $(date +%s) exit $?"

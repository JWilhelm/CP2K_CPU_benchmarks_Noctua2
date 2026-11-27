#!/bin/bash
# Create runs/<case>/<n>n for every case and node count and submit one job each.
# Usage: submit_all.sh <case> [<node counts>]   (node count "0.5" = half node, 64 cores)
set -e
R=/scratch/hpc-prf-dyncrys/eprop2d1_Jan/34_CP2K_benchmarks_LRZ
CASE=$1; shift
NODES=${@:-0.5 1 2 4}
# walltimes per case and node count (estimate from earlier runs + margin)
declare -A T=(
 [anatase_GW_aug-SZ2]="16:00:00 8:00:00 4:00:00 2:00:00"
 [anatase_DFT_aug-TZ2_FFT]="3:00:00 2:00:00 1:00:00 1:00:00"
 [anatase_GW_aug-SZ2_FFT]="16:00:00 8:00:00 4:00:00 2:00:00"
 [anatase_GW_aug-TZ2]="72:00:00 40:00:00 20:00:00 12:00:00"
 [anatase_DFT_aug-TZ2]="3:00:00 2:00:00 1:00:00 1:00:00"
 [water_64_PBE_TZV2P]="1:00:00 1:00:00 1:00:00 1:00:00"
 [nanographene_L16_GW_aug-SZ2]="4:00:00 2:00:00 1:00:00 1:00:00"
 [nanographene_L56_GW_aug-SZ2]="24:00:00 12:00:00 6:00:00 3:00:00"
)
read -r -a TT <<< "${T[$CASE]}"
for n in $NODES; do
  case $n in 8) i=3; ARGS="--nodes=8 --ntasks=128 --exclusive --mem=0";; 0.5) i=0; ARGS="--nodes=1 --ntasks=8 --mem=120000M";; 1) i=1; ARGS="--nodes=1 --ntasks=16 --exclusive --mem=0";;
             2) i=2; ARGS="--nodes=2 --ntasks=32 --exclusive --mem=0";; 4) i=3; ARGS="--nodes=4 --ntasks=64 --exclusive --mem=0";; esac
  D=$R/runs/$CASE/${n}n; mkdir -p $D; cp $R/inputs/$CASE/* $D/
  cd $D; sbatch --parsable $ARGS --time=${TT[$i]} -J b34_${CASE}_${n}n -o slurm-%j.out $R/scripts/run.sbatch | sed "s/^/$CASE ${n}n job /"
done

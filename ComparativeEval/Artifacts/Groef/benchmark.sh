#!/usr/bin/env bash

runs=10

# Input files
files=(
  "r11.xml"
  "r12.xml"
  "r32.xml"
  "r61.xml"
  "r62.xml"
)

# Build classpath once
CLASSPATH="$(printf "%s:" lib/*.jar)"

for file in "${files[@]}"; do

  echo "========================================"
  echo "Benchmarking: $file"
  echo "========================================"

  times=()

  for ((i=1; i<=runs; i++)); do
    printf "Run %2d... " "$i"

    start=$(date +%s%3N)

    java -cp "$CLASSPATH" \
      nl.rug.ds.bpm.CommandlineVerifier \
      -p ../Artifacts/Groef/runningexample.pnml \
      -s "../Artifacts/Groef/$file" \
      -c ../NuSMV-2.7.1-linux64/bin/NuSMV \
      -v kripke \
      -o output \
      -l debug \
      > /dev/null 2>&1

    end=$(date +%s%3N)

    duration=$((end - start))
    times+=("$duration")

    echo "${duration} ms"
  done

  echo
  echo "Results for $file:"
  for i in "${!times[@]}"; do
    printf "  Run %2d: %d ms\n" $((i+1)) "${times[$i]}"
  done

  echo
done


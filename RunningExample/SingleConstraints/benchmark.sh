#!/usr/bin/env bash

runs=10

# List of files to test (include Running_Example.xml first)
files=(
  "../Running_Example.xml"
  "R11.xml" "R12.xml" "R2.xml" "R31.xml" "R32.xml"
  "R41.xml" "R42.xml" "R51.xml" "R52.xml"
  "R61.xml" "R62.xml" "R71.xml" "R72.xml"
)

# Print table header for Excel
header="File"
for ((i=1; i<=runs; i++)); do
  header+="\tRun${i}"
done
echo -e "$header"

for file in "${files[@]}"; do
  times=()
  for ((i=1; i<=runs; i++)); do
    start=$(date +%s%3N)
    python3 ../../python_code/test_script.py "$file" > /dev/null 2>&1
    end=$(date +%s%3N)
    duration=$((end - start))
    times+=("$duration")
  done

  # Print row for this file
  row="$file"
  for t in "${times[@]}"; do
    row+="\t$t"
  done
  echo -e "$row"
done


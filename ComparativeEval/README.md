# Comparative Evaluation

## Reproducing the Comparative Evaluation

To repeat the comparative evaluation, follow these steps:

These instructions assume linux systems but should work on windows/mac with minor adjustments (chaging paths from \ to /). The most challenging part on other systems is likely to install the NuSMV model checker as is described on their [webpage](https://nusmv.fbk.eu/).

### Step 1: Clone the Required Repositories

Clone the following two repositories into this directory:

1. Clone the Kogi repository: ``git clone https://github.com/jc4v1/Kogi-Python.git``
2. Clone the BPMVerification repository: ``git clone https://github.com/rug-ds-lab/BPMVerification``
3. Follow the installation steps in the respective repository readmes for installation

### Step 2.1: Execute Kogi-Python

1. Move the evalscript.py from the Artifacts/Kogi directory to the Kogi directory: ``mv Artifacts\Kogi\evalscript.py Kogi-Python``
2. (Potentially change permissions) ``chmod 755 evalscript.py``
3. Execute the script:`` python3 Kogi-Python/evalscript.py --goal-model Artifacts/Kogi/goalModel.txt --petri-net Artifacts/RunningExample.pnml --event-mapping Artifacts/Kogi/mapping.csv``

Obviously, the eval script can also be used with other models/mappings and if used from a different directory then the paths have to be adjusted as follows


### Step 2.2: Execute BPMVerification

1. Install NuSMV as described in the BPMVerification ReadMe and on their website
2. Use the provided CLI tool as described in the BPMVerification ReadMe with the created artifacts

```bash
java -cp "$CLASSPATH" \
    nl.rug.ds.bpm.CommandlineVerifier \
    -p ../Artifacts/Groef/runningexample.pnml \
    -s ../Artifacts/Groef/fullspec.xml \
    -c ../NuSMV-2.7.1-linux64/bin/NuSMV \
    -v kripke \
    -o output \
    -l debug
```

### Results

The evaluation results are available in the `Results/` directory, which contains CSV files with the comparative analysis data.

# PTV - Process Tree Verifier

The Process Tree Verifier (PTV) is a subscription-based REST service for verifying regulatory requirements on processes represented as process trees in the [CPEE](https://cpee.org) format. It was developed as part of *Tree-based Compliance Verification: Bridging the Gap between Compliance Requirements and Process Execution* (TRPro project, DFG project no. 514769482).

- Full method documentation: [annotated_verification_methods.md](https://github.com/JohannesLbck/ProcessTreeVerify/blob/master/python_code/annotated_verification_methods.md)
- Compliance log format: [log_doc.md](https://github.com/JohannesLbck/ProcessTreeVerify/blob/master/log_doc.md)
- Quick method reference: [methods_doc_concise.md](python_code/methods_doc_concise.md)

---

## Quick Demo

A live instance is available at:

**[https://cpee.org/hub/server/Staff.dir/Loebbi.dir/Compliance.dir/Running%20Example.xml/open-new?stage=compliance](https://cpee.org/hub/server/Staff.dir/Loebbi.dir/Compliance.dir/Running%20Example.xml/open-new?stage=compliance)**

Open the link, navigate to the **Compliance** tab, and press **Verify** to run verification against the pre-loaded process and requirements. The results panel shows per-requirement verdicts with detailed reasoning steps, and links to the full compliance log.

---

## (A) Testing with Existing Processes

Pre-loaded example processes (running example, user study, composite dataset) are available in the [CPEE hub](https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir). Open any model, accept the terms of use, and any edit to the process triggers a verification run. Results appear in the [compliance log directory](https://cpee.org/comp-log/) — match the log by the instance UUID shown in the URL. The composite dataset XML files are also available [here](https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir/CompositeDataSet.dir/). Add **compliance.html** before the ?monitor in the URL when you are in a particular instance and press verify to test. It is possible you will have to edit the process/requirements first before verification results appear.

---

## (B) Adding the Subscriber to a New Process

1. Create a new model in the [PTV playground](https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir/PTVPlayground.dir/).
2. Download the testset via **save testset**, add one of the subscriptions below, then reload it via **load testset**.
3. Add compliance requirements as ASTs in the **Attributes → requirements** field.

Any subsequent change to the model triggers verification. Logs appear at [cpee.org/comp-log](https://cpee.org/comp-log/).

**Exact label matching:**
```xml
<subscriptions xmlns="http://riddl.org/ns/common-patterns/notifications-producer/2.0">
  <subscription id="_compliance" url="https://power.bpm.cit.tum.de/compliance/Subscriber">
    <topic id="description"><event>change</event></topic>
  </subscription>
</subscriptions>
```

**Semantic label matching:**
```xml
<subscriptions xmlns="http://riddl.org/ns/common-patterns/notifications-producer/2.0">
  <subscription id="_compliance" url="https://power.bpm.cit.tum.de/compliance/SubscriberSemantic">
    <topic id="description"><event>change</event></topic>
  </subscription>
</subscriptions>
```

---

## (C) Local Testing Script

```bash
git clone https://github.com/JohannesLbck/ProcessTreeVerify.git
cd python_code
pip install -r requirements.txt          # optional venv recommended
python3 test_script.py ../RunningExample/Running_Example.xml
```

Any XML from the composite dataset or hub can be used in place of the running example. Add `-semantic` to enable semantic label matching (useful for the `*adjusted.xml` dataset files which contain intentionally perturbed activity labels):

```bash
python3 test_script.py ../CompositeDataset/HaarmannetAL2021adjusted.xml -semantic
```

---

## (D) Deployment

```bash
git clone https://github.com/JohannesLbck/ProcessTreeVerify.git
cd python_code
pip install -r requirements.txt
python3 subscriber.py                    # start daemon (port 9321)
python3 subscriber.py --status           # check status
python3 subscriber.py --stop             # stop daemon
python3 subscriber.py --foreground       # debug/foreground mode
```

Point the subscription URL at your endpoint instead of the hosted one. We recommend nginx for port forwarding and Let's Encrypt for TLS.

---

## Comparative Evaluation

Replication instructions are in the `ComparativeEval/` directory.

---

## Visualising Requirement ASTs (`drawast.py`)

Renders requirements from a JSON file or CPEE XML as AST diagrams via [Graphviz](https://graphviz.org/).

**Prerequisites:** `pip install graphviz` + the Graphviz system package (`apt`/`dnf install graphviz`).

```bash
python drawast.py CompositeDataset/DCR/requirementsmapping.json
python drawast.py RunningExample/Running_Example.xml
python drawast.py myprocess.xml --output-dir /tmp/asts --format pdf
```

| Flag | Description |
|---|---|
| *(none)* | Draws the requirement expression AST only. |
| `--full-tree` | Expands each compliance-pattern call with its implementation AST. |
| `--full-tree-with-logs` | Like `--full-tree` but includes `logger.*` nodes. |
| `--av-path PATH` | Path to `annotated_verification.py` (default: `python_code/annotated_verification.py`). |
| `--format FMT` | Output format (`png`, `pdf`, `svg`, …). Default: `png`. |
| `--output-dir DIR` | Override the auto-generated output directory. |


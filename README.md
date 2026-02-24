# PTV - Process Tree Verifier

This is the Github of the Process Tree Verification tool developed for *Tree-based Compliance Verification: Bridging the Gap between Compliance Requirements and Process Execution* as part of the *TRPro project* Project funded by the DFG under the project number 514769482. The Process Tree Verifier is a Subscribtion based Rest Service that can be used to verify regulatory requirements on processes represented as process trees in the [cpee](https://www.cpee.org)-tree format.

This ReadMe contains instructions on how to use the developed tool as well as the processes used during the evaluation and all artifacts of the user study with additional documentation in the respective subfolders. The tool can be tested (A) with an existing process to see the functionality directly, (B) with new processes/requirements to show how it affects process modeling, (C) with a small testing script locally, and (D) with a locally deployed copy of the PTV for future development.

The prompts used for generating ASTs out of Natural Language / Textual Process Descriptions are in the ExtractionPrototype Directory.

The dataset used for evaluation as XML files is in the CompositeDataset directory which also contains an additional README explaining how the dataset was createtd. The XML files already contain the requirement ASTs so they can be loaded into the CPEE and verified as described in (B). Furthermore they can be directly tested according to (A) using the already loaded models which can be found [here](https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir/CompositeDataSet.dir/).

The complete Documentation of the PTV can be found in the  [annotated_verification_methods.md](https://github.com/JohannesLbck/ProcessTreeVerify/blob/master/python_code/annotated_verification_methods.md) file.

## (A) Testing with existing Processes

1. Navigate to the cpee directory containing the processes used as running example, for the user study and the composite dataset: [https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir]
2. Open any of the example processes. For example, simply click on the "Running Example", and accept the terms of use (no user data is collected).
3. The example process is already connected to the PTV running on our server, so you can view resulting logs [here](https://power.bpm.cit.tum.de/PTVLogs/) or in XES format on the [cpee](https://cpee.org/comp-log/) while editing the process. We recommend the XES format logs, as the other logs often break and are deprecated. Simply look for the log in that directory where the instance number matches your number. You can find your instance number in the URL after opening a model as well as on the top right next to the cpee logo. Any edit in the model will trigger a rerun of the verification. So, for example you can add a additionl activity by right clicking on any activity and selecting "Service call with scripts". If you want to change an existing activity, left click the activity and change the values on the right. You can choose to save these to the repository, but we will regularily revert these changes to keep reproducibiltiy. If you want to fully play around with these or own models, we suggest loading the XML into a own model as described in (B).

## (B) Adding the subscription to a new Process

If you want to try out the verification yourself, you can also create a new model on the CPEE and connect it to the compliance subscriber. For this, follow the following steps:

1. Navigate to the following [cpee directory](https://cpee.org/hub/?stage=development&dir=Staff.dir/Loebbi.dir/Compliance.dir/PTVPlayground.dir/) and create a New Model
2. Use the CPEE functionality "save testset" to download the XML test set.
3. Add the Compliance Subscriber to the test by copy-pasting the following at the end of the XML. (You can also check the xml files of the composite dataset for examples with the subscriber added ) and we will add a button for this in the future

```
  <subscriptions xmlns="http://riddl.org/ns/common-patterns/notifications-producer/2.0">
    <subscription xmlns="http://riddl.org/ns/common-patterns/notifications-producer/2.0" id="_compliance" url="https://power.bpm.cit.tum.de/compliance/Subscriber">
      <topic id="description">
        <event>change</event>
      </topic>
    </subscription>
  </subscriptions>
```

4. Now, use the "load testset" button to load the edited XML into the process. Save the model for safety.
5. To actually verify anything you have to still add compliance requirements. The compliance requirements are sent to the subscriber via the Attributes fields. Accordingly, add any requirements encoded as an AST you want into it like so:

![Add Requirements](DemoImages/3.png)

6. Now any change to the process model will send a message to the subscriber, so you can again check the compliance log as described in (A)

For a complete overview of all verification methods, you can check the source code in the python\_code dictionary or the Documentation linked above. 


## (C) Local Testing Scripts
Complete local deployment requires setting up a server / configuring a firewall. In order to simplify local testing for users who do not want to spend that time but do want to test the PTV locally, we prepared a simple script interface for the PTV. To use the testing script, you first have to clone the repository and install dependencies. Instructions were tested on a fresh Fedora 43 installation but should work on other distributions and Windows/Mac as well.

1. Clone the Repository `git clone https://github.com/JohannesLbck/ProcessTreeVerify.git`
2. Navigate to the python\_code dictionary `cd python_code`. Optionally set up a virtual enviroment (This tool has barely any dependencies)
3. (This was optional on Fedora): Install all dependencies `pip install -r requirements.txt`
4. On Linux: Launch the testing script `python3 test_script.py ../RunningExample/Running_Example.xml`
5. On Windows: Launch the testing script `python3 test_script.py ..\RunningExample\Running_Example.xml`

The above example tests the running example process also used throughout the paper, but you can also verify any other process xml found in the Composite Dataset, the two survey processes as well as any processes created in the process hub (as long as you add requirements to them)


## (D) Custom Deployment
Finally, you can also deploy the PTV locally, which we recommend in case you want to add additional functionality or simply run different tests.
The CPEE side would be handled the same as before, with the only change being that the URL needs to point toward your own endpoint. We recommend using a server such as nginx to forward the port (default is port 9321, which can be changed in python\_code/subscriber.py) towards a URL. These instructions were tested on a fresh Fedora 43 Installation but should work on different systems as well. Depending on your distribution or Windows/Mac, you might have to install additional packages such as python3 and pip (any current version should do; all required packages are standard libraries).

To actually launch the project follow these steps:

1. Clone the Repository `git clone https://github.com/JohannesLbck/ProcessTreeVerify.git`
2. Navigate to the python\_code dictionary `cd python_code`. Optionally set up a virtual enviroment.
3. Install all dependencies `pip install -r requirements.txt`
4. Launch the Application using `python3 subscriber.py` (launches as a daemon, short explanation below)
5. Either use the endpoint at local host (127.0.0.1:9321) or set up port forwarding by setting up your firewall and webserver (we recommend using nginx and also setting up let's encrypt)
6. End the Daemon after using by executing `python3 subscriber.py` again

subscriber.py also contains a little script (def run\_server():) to ensure that the subscriber is started as a daemon. We are unsure how this will work on Windows/Mac so if you encounter any issues on these systems you can remove that codepiece and use the "normal" way to run fastapi rest services using `uvicorn.run subscriber:app port=9321`. If you still encounter any issues on these systems you can contact us or just try out the example scripts presented in Section (C).
Technially you can also set up a local deployment of the CPEE as well, but this can be somewhat challenging. For instructions on a locally deployed CPEE we refer to the official documentation at [cpee.org].

## General Guidance & Best Practices

### Process Modeling Tips
- **Clear Activity Labels**: Use descriptive, unique names for activities to ensure requirements can properly reference them
- **Resource Annotations**: Explicitly annotate resource assignments for segregation of duty requirements
- **Data Objects**: Clearly define and name data objects that flow through the process
- **Exception Handling**: Use rescue activities and compensation mechanisms for failure handling requirements

### Requirement Specification Tips
- **AST Syntax**: Ensure requirements are correctly encoded as Abstract Syntax Trees (ASTs) with proper method calls and parameters
- **Testing Requirements**: Start with simpler requirements (control flow) before adding complex constraints (time, data, resources)
- **Reference Documentation**: Consult `methods_doc_concise.md` for quick reference or `annotated_verification_methods.md` for detailed documentation
- **Logical Combinations**: Use `and`, `or`, and `not` operators to combine multiple verification checks

### Contributing & Extending

The codebase is organized as follows:
- **`annotated_verification.py`**: Core verification methods for all compliance patterns
- **`verificationAST.py`**: AST parsing and requirement evaluation
- **`assurancelogger.py`**: Custom logging with assurance tracking
- **`util.py`**: Utility functions for XML tree traversal and analysis
- **`python_code/utils/`**: Specialized utilities for control, data, resources, and time handling

To add new verification methods:
1. Implement the verification logic in `annotated_verification.py`
2. Document the method signature in both `annotated_verification_methods.md` and `methods_doc_concise.md`
3. Add the newly added method to the allowed methods dict in `verificationAST.py` 
4. Update `util.py` interface if necessary



This project is licensed under a GNU GENERAL PUBLIC LICENSE license so you are allowed to reuse the code of this project under its copy left specifications. In addition if you use this project for any publication you can cite the associated paper as follows:

   



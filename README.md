## Code2DFD


Code2DFD can automatically extract dataflow diagrams (DFDs) that are enriched with security-relevant annotations from the source code of microservice applications.
It is structured as a framework, where the *technology-specific extractors* in `technology_specific_extractors/` are executed and detect evidence for DFD items in the code.
They use some general functionality from `core/`.


##### 1. Installation and configuration
Before running the tool, [Python](https://www.python.org/downloads/) version 3.x and the packages specified in `requirements.txt` need to be installed.
The path to the application that is to be analysed can be written in the `config/config.ini` file or given as parameter (see 2.).
A number of repositories is already given in that file, for all of which a manually created DFD exists [here](https://github.com/tuhh-softsec/microSecEnD).
The corresponding path only needs to be un-commented for analysis (all others have to be commented out with a ";")

##### 2. Running the tool
To start the tool via the terminal, simply enter `python3 code2DFD.py` in a command line opened in the root directory.
The extraction will start and some status messages appear on the screen.
Alternatively, the repository path can be given as parameter: `python3 code2DFD.py repository/path`.
Path as parameter overrules path in config-file.
Once the analysis is finished, the results can be found in the `output/` folder.

To run the tool as a RESTful API service, run `python3 flask_code2DFD.py`.
This will spawn up a Flask server and you can trigger DFD-extractions by sending a request to or opening your browser at `localhost:5000/dfd?path=*repository/path*`


##### 3. Output
The tool creates multiple outputs:
- The extracted DFD is saved as a .png rendered with [PlantUML](https://plantuml.com) in `output/png/`.
An internet connection is needed for this, otherwise no PNG will be created.
- A machine-readable version of the DFD is created in JSON format in `output/json/`
- Additionally, a version in [CodeableModels](https://github.com/uzdun/CodeableModels) format is created in `output/codeable_models/`, if you want a more flexible format for further work.
To render these, you need to install CodeableModels as described on their site.
Further, our metamodel is needed for that, which can be found in the [repository of our dataset](https://anonymous.4open.science/r/dataset-submission-592E)
If interoperability with other software or further processing of the models is of no concern, this offers no advantages.
The DFDs rendered by CodeableModels do not follow standard DFD-notation.
- A textual version of the results (list of microservices, external entities, and information flows) is created in `output/results/`.
- The traceability information for the DFD items is saved in `output/traceability/`.
Note that this is ongoing work and the traceability is not created for all items as of now.
However, we implemented it for enough items to show that this technique works and the full traceability is only a question of further implementation work.
- Logs are saved in `output/logs/`.

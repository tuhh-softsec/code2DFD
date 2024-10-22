## Code2DFD

Code2DFD can automatically extract dataflow diagrams (DFDs) that are enriched with security-relevant annotations from the source code of microservice applications.
It is structured as a framework, where the *technology-specific extractors* in `technology_specific_extractors/` are executed and detect evidence for DFD items in the code.
They use some general functionality from `core/`.

The tool and underlying approach are presented in a publication in the Journal of Systems and Software (JSS).
You can find the paper on [arXiv](https://arxiv.org/abs/2304.12769) or the publisher's [website](https://www.sciencedirect.com/science/article/abs/pii/S0164121223001176).
If you use the tool in a scientific context, please cite as:

```bibtex
@article{Code2DFD23,
  title = {Automatic Extraction of Security-Rich Dataflow Diagrams for Microservice Applications written in Java},
  journal = {Journal of Systems and Software},
  volume = {202},
  pages = {111722},
  year = {2023},
  issn = {0164-1212},
  doi = {https://doi.org/10.1016/j.jss.2023.111722},
  author = {Simon Schneider and Riccardo Scandariato},
  keywords = {Dataflow diagram, Automatic extraction, Security, Microservices, Architecture reconstruction, Feature detection}
}
```


##### 1. Installation and configuration
Before running the tool, [Python](https://www.python.org/downloads/) version 3.x and the packages specified in `requirements.txt` need to be installed.
The path to the application that is to be analysed can be written in the `config/config.ini` file or given as parameter (see 2.).
A number of repositories is already given in that file, for all of which a manually created DFD exists [here](https://github.com/tuhh-softsec/microSecEnD).
The corresponding path only needs to be un-commented for analysis (all others have to be commented out with a ";")


##### 2. Running the tool
To start the tool via the terminal using the config file, simply enter `python3 code2DFD.py --config_path PATH_TO_CONFIG` in a command line opened in the root directory.
For example, `python3 code2DFD.py --config_path config/config.ini` for the [example config](config/config.ini) in this repository.

The config file needs to specify the following sections and parameters:
- Repository
  - `path`: `organization/repository` part of GitHub URL
  - `url`: the full URL of the repository to clone from (may be local path)
  - `local_path`: local directory to clone the repository to (without the repository name itself)
- Technology profiles: same as in [example config](config/config.ini)
- DFD: empty section
- Analysis Settings (optional)
  - `development_mode`: boolean, turns on development mode
  - `commit`: hash of the commit to checkout and analyze; repository will be returned to the same commit it was in before analysis; if commit not provided, attempts to checkout `HEAD`
  
It is possible to provide these parameters also by command line, see `python3 code2DFD.py --help` for exact usage

If both config file and CLI arguments provided, CLI arguments take precedence

###### 2.1 RESTful service
To run the tool as a RESTful API service, run `python3 flask_code2DFD.py`.

This will spawn up a Flask server and you can trigger DFD-extractions by sending a request to  `localhost:5001/dfd` with parameters `url` and optionally `commit`.

Currently only GitHub URLs are supported this way.


##### 3. Output
The tools puts the `PROJECT` analysis output into `code2DFD_output/PROJECT`
The tool creates multiple outputs:
- The extracted DFD is saved as a UML diagram in `code2DFD_output/PROJECT/PROJECT_uml.txt`
and as a .png rendered with [PlantUML](https://plantuml.com) in `code2DFD_output/PROJECT/PROJECT_uml.png`
An internet connection is needed for this, otherwise no PNG will be created.
- A machine-readable version of the DFD is created in JSON format in `code2DFD_output/PROJECT/PROJECT_json_architecture.json`
  - Edges information only is saved in `code2DFD_output/PROJECT/PROJECT_edges.json`
- A textual version of the results (list of microservices, external entities, and information flows) is created in `code2DFD_output/PROJECT/PROJECT_results.txt`.
- Additionally, a version in [CodeableModels](https://github.com/uzdun/CodeableModels) format is created in `code2DFD_output/PROJECT/PROJECT.py`, if you want a more flexible format for further work.
To render these, you need to install CodeableModels as described on their site.
Further, our metamodel [`microservice_dfds_metamodel.py`](microservice_dfds_metamodel.py) is needed for that.
If interoperability with other software or further processing of the models is of no concern, this offers no advantages.
The DFDs rendered by CodeableModels do not follow standard DFD-notation.
- The traceability information for the DFD items is saved in `code2DFD_output/PROJECT/PROJECT_traceability.json`.
Note that this is ongoing work and the traceability is not created for all items as of now.
However, we implemented it for enough items to show that this technique works and the full traceability is only a question of further implementation work.
- Logs are saved in `code2DFD_output/logs/`.

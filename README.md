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
For example, `python3 code2DFD.py --config_path config/config.ini` for the example config in this repository.
The extraction will start and some status messages appear on the screen.
If you want to analyse in application on GitHub, simply put in the GitHub handle, using the `--github_path` option.
For example, for the repository `https://github.com/sqshq/piggymetrics`, run the command `python3 code2DFD.py --github_path sqshq/piggymetrics`
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
Further, our metamodel `microservice_dfds_metamodel.py` is needed for that.
If interoperability with other software or further processing of the models is of no concern, this offers no advantages.
The DFDs rendered by CodeableModels do not follow standard DFD-notation.
- A textual version of the results (list of microservices, external entities, and information flows) is created in `output/results/`.
- The traceability information for the DFD items is saved in `output/traceability/`.
Note that this is ongoing work and the traceability is not created for all items as of now.
However, we implemented it for enough items to show that this technique works and the full traceability is only a question of further implementation work.
- Logs are saved in `output/logs/`.

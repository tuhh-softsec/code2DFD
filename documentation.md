Naming conventions:

To add a new technology-specific extractor, you need to come up with a nam for it first. 
If possible, simply name it after the technology it extracts model items from.
Given this `name`, create a new folder in /technology_specific_extractors with the chosen `name` and add a Python file called `name.py` (insert your chosen name there). 
Finally, this Python file has to contain a main method called `detect_name()`.

The main method `name_main()` has to take the following input arguments and return the following values:
Input: list of services (object of type CServices), list of information flows (object of type CInformationFlows), and list of external entities (object of type CExternalEntities
Output: list of services (object of type CServices), list of information flows (object of type CInformationFlows), and list of external entities (object of type CExternalEntities)
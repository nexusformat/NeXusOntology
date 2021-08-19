**NeXusOntology creation script**

Run either the Jupyter notebook or exported Python script

Ensure that owlready2 and pygithub are installed (pip install)

Add four parameters when running the code:

_script_version (change version if the ontology has been modified by changes to the script)  
1. token (your github token - see below)  
2. out_path (path for created .owl file)  
3. tmp_file_path (temporary file path)  

To get a Github access token:  
Github/settings/developer settings/personal access tokens/create new token

Run the script (using Python 3)

Some deprecation warnings are likely to be displayed before the .owl file is created.

The .owl file (RDF/XML syntax) can be opened by a text editor or ontology tool such as Protege (https://protege.stanford.edu/)

See ontology metadata for more information.

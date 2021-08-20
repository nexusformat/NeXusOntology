**NeXusOntology creation script**

Ensure that owlready2 and pygithub are installed (pip install) by running the requirements.txt

Add four parameters when running the code:  
python3 -m nxsOnto.generator [github access token] [out path for ontology] [temporary file path]
 
To get a Github access token:  
Github/settings/developer settings/personal access tokens/create new token

Some deprecation warnings are likely to be displayed before the .owl file is created.

The .owl file (RDF/XML syntax) can be opened by a text editor or ontology tool such as Protege (https://protege.stanford.edu/)

See ontology metadata for more information.

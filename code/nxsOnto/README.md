**NeXusOntology creation script**

Ensure that packages `owlready2` and `pygithub` are installed by running: `pip install -r requirements.txt`

Alternative: If you have [conda](https://docs.conda.io/) available, a custom
conda environment can be created and this package installed (by `pip`) with
these steps:

```bash
    conda env create -f environment.
    conda activate NeXusOntology
    pip install -e .
```

Add four parameters when running the code:  

```
python3 -m nxsOnto.generator [github access token] [out path for ontology] [temporary file path]
 ```

To get a Github access token:  
Github/settings/developer settings/personal access tokens/create new token

Some deprecation warnings are likely to be displayed before the `.owl` file is created.

The `.owl` file (RDF/XML syntax) can be opened by a text editor or ontology tool such as Protege (https://protege.stanford.edu/)

See ontology metadata for more information.

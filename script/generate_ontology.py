import owlready2
from NeXusOntology import NeXusOntology
import pygit2
import os

local_dir = os.path.abspath(os.path.dirname(__file__))
nexus_def_path = os.path.join(local_dir, f"..{os.sep}definitions")
os.environ['NEXUS_DEF_PATH']=nexus_def_path

repo = pygit2.Repository(nexus_def_path)
def_commit = repo.head.target.hex[:7]

web_page_base_prefix = 'https://fairmat-nfdi.github.io/nexus-fairmat-proposal/9636feecb79bb32b828b1a9804269573256d7696/'

base_iri = 'http://purl.org/nexusformat/v2.0/definitions/' + def_commit + '/'
onto = owlready2.get_ontology(base_iri + "NeXusOntology")

nexus_ontology = NeXusOntology(onto, base_iri, web_page_base_prefix)
nexus_ontology.gen_classes()
nexus_ontology.gen_children()
nexus_ontology.gen_datasets()

onto.save(file = os.path.join(local_dir, f"..{os.sep}ontology{os.sep}NeXusOntology.owl"), format = "rdfxml")
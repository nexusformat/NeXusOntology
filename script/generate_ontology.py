import owlready2
from NeXusOntology import NeXusOntology
import pygit2

nexus_def_path = "../definitions"

repo = pygit2.Repository(nexus_def_path)
def_commit = repo.head.target.hex[:7]

web_page_base_prefix = 'https://fairmat-experimental.github.io/nexus-fairmat-proposal/1c3806dba40111f36a16d0205cc39a5b7d52ca2e/'

base_iri = 'http://purl.org/nexusformat/v2.0/definitions/' + def_commit + '/'
onto = owlready2.get_ontology(base_iri + "NeXusOntology")

nexus_ontology = NeXusOntology(onto, base_iri, web_page_base_prefix)
nexus_ontology.gen_classes()
nexus_ontology.gen_children()
nexus_ontology.gen_datasets()

onto.save(file = "../ontology/NeXusOntology.owl", format = "rdfxml")
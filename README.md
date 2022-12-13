# How to run the latest Ontology

Make sure you have the definitions submodule initialized using: git submodule update --init
CD to the script folder. Run 'python NeXusOntology.py'

# NeXusOntology
NeXusOntology: Machine-readable ontology of the NeXus definitions.

The published ontology _describes_ the NeXus standard, it _does not define_ the standard.

note (2021-05-05): This repository is under development.  Content may change at any time without notice.

This ontology extracts information about NeXus classes and fields from
NeXus nxdl definition files on the NeXus GitHub site.  
See 'seeAlso' for links to the NeXus project, including licencing information.  
    This project was undertaken under ExPaNDS WP3.2 (https://expands.eu/)
    
**Purpose**    
The ontology is designed to fulfil several purposes. First, it creates unique identifiers
for each of the NeXus fields which would normally exist only within the namespaces of the
defining NeXus classes. This is the primary goal and provides PIDs for annotation and tagging.
The second purpose is to allow, via separate ontologies, NeXus fields and classes to be mapped
onto equivalent or related terms defined elsewhere.  
Finally, we hope that this ontology, when used with a tool such as Protege, will provide a
useful 'NeXus Explorer' tool to gain a quick overview of NeXus with links to official NeXus 
documentation.
    
**Design Philosophy**    
The terms in the ontology are extracted almost entirely from NeXus nxdl definition file and converted to
an OWL ontology using the owlready2 python module (https://pypi.org/project/Owlready2/)
NeXus classes - Base Classes and Application Definitions - are expressed as OWL classes.
NeXus fields, which contain the NeXus metadata, are expressed as Owl data properties.
While NeXus provides a subclassing method ('extends') for NeXus classes, this is not currently reflected
in the corresponding OWL classes.  
One can think of the main purpose of the ontology as being to 'flatten' the NeXus fields into a single
namespace, rather than existing in the multiple namespaces of the NeXus classes. This requires longer and
more explicit names for the NeXus fields, which are created by prepending the NeXus base class name to the
NeXus field name. It is very important to note that a NeXus application definition can extend a base class
adding new fields, and that it is understood (see NeXus documentation) that the new fields then reserve names
within the class dictionary in order to avoid later duplication. These new fields are therefore shown as data
properties of the NeXus Base Classes, even though they are defined outside the original class definition.  
    
NeXus classes are reviewed periodically by the NeXus NIAC. It is anticipated that this ontology can be updated 
quickly and automatically to reflect the updated definitions.
    
**Caveats**  
Some NeXus classes (e.g. NXtransformations) are related specifically to the class that they are contained in.
This relationship is not preserved.  
NeXus allows multiple instances of metadata fields within a dataset. Relating multiple field values to a
single identifier will require a selection algorithm.
    
**Version**  
The version string is the NeXus version followed by the ontology version.

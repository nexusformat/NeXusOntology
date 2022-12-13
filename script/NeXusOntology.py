from os import walk
import owlready2
import xml.dom.minidom
import xml.etree.ElementTree as ET
import types

web_page_base_prefix = 'https://fairmat-experimental.github.io/nexus-fairmat-proposal/1c3806dba40111f36a16d0205cc39a5b7d52ca2e/'
web_page_prefix = web_page_base_prefix + "classes/"
nexus_def_path = "../definitions"

nxdl_folders = ["contributed_definitions", "base_classes", "applications"]

namespace = {"nxdl": "http://definition.nexusformat.org/nxdl/3.1"}

def get_all_tags(iterator, xml_tag):
    path = []
    for event, element in iterator:
        if element.get("name") or (element.tag == "{http://definition.nexusformat.org/nxdl/3.1}group" and element.get("type")):
            if event == "start":
                name = element.get("name") or element.get("type").upper()[2:]
                path.append(name)
                if element.tag == "{http://definition.nexusformat.org/nxdl/3.1}"+xml_tag:
                    yield '/'.join(path), element
            else:
                if len(path)>0:
                    path.pop()

def safe_get_xml_doc(element):
    docEl = element.find("nxdl:doc", namespace)
    if docEl is None or docEl.text is None:
        return ""
    return docEl.text

def load_data_types():
    types_dom = xml.dom.minidom.parse(nexus_def_path + "/nxdlTypes.xsd")

    typesDict = {}
    for nxtype in types_dom.getElementsByTagName('xs:simpleType'):
        name = nxtype.getAttribute('name')
        if name == "primitiveType":
            union_el = nxtype.getElementsByTagName('xs:union')
            types = union_el[0].getAttribute('memberTypes')
            types = types.replace(" ", "").split("nxdl:")[1:]
    
    for type in types:
        typesDict[type] = {}

    for nxtype in types_dom.getElementsByTagName('xs:simpleType'):
        name = nxtype.getAttribute('name')
        if name in types:
            doc = nxtype.getElementsByTagName("xs:documentation")[0]
            typesDict[name]["doc"] = doc.firstChild.nodeValue

    return typesDict

def load_unit_categories():
    types_dom = xml.dom.minidom.parse(nexus_def_path + "/nxdlTypes.xsd")

    typesDict = {}
    for nxtype in types_dom.getElementsByTagName('xs:simpleType'):
        name = nxtype.getAttribute('name')
        if name == "anyUnitsAttr":
            union_el = nxtype.getElementsByTagName('xs:union')
            types = union_el[0].getAttribute('memberTypes')
            types = types.replace(" ", "").split("nxdl:")[1:]
    
    for type in types:
        typesDict[type] = {}

    for nxtype in types_dom.getElementsByTagName('xs:simpleType'):
        name = nxtype.getAttribute('name')
        if name in types:
            doc = nxtype.getElementsByTagName("xs:documentation")[0]
            typesDict[name]["doc"] = doc.firstChild.nodeValue
            examples = doc.getElementsByTagName("xs:element")
            typesDict[name]["examples"] = []
            for example in examples:
                typesDict[name]["examples"].append(example.firstChild.nodeValue)      
    return typesDict


def load_all_nxdls() -> dict:
    nxdl_info = {"base_classes":{}, "applications":{}, "field":{}, "attribute":{}, "group":{}}
    just_fnames = []
    files = []

    for folder in nxdl_folders:
        files_in_folder = next(walk(nexus_def_path + "/" + folder), (None, None, []))[2]
        files_in_folder = list(filter(lambda filename: filename.endswith(".nxdl.xml"), files_in_folder))
        intersection = [value for value in just_fnames if value in files_in_folder]
        just_fnames.extend(files_in_folder)
        files.extend([nexus_def_path+"/"+folder+"/"+path for path in files_in_folder])
        if len(intersection)>0:
            for f in intersection:
                files.remove(nexus_def_path+"/"+folder+"/"+f)
    
    for file in files:
        root = ET.parse(file).getroot()
        
        class_dict_to_append = nxdl_info["base_classes"]
        if root.get("category") == "application":
            class_dict_to_append = nxdl_info["applications"]
        
        className = root.get("name")
        class_dict_to_append[className] = {"doc": root.find("nxdl:doc", namespace).text, "extends": root.get("extends"), "category": file.split("/")[-2]}

        # Take care of all fields here
        for xml_tag in list(nxdl_info.keys())[2:]:
            iterator = ET.iterparse(file, events=("start", "end"))
            for path, element in get_all_tags(iterator, xml_tag):
                nxdl_info[xml_tag][path] = {"comment": safe_get_xml_doc(element), "category": file.split("/")[-2]}

    return nxdl_info

owlready2.onto_path.append(nexus_def_path+"/ontology")
base_iri = 'http://purl.org/nexusformat/definitions/'
onto = owlready2.get_ontology(base_iri + "NeXusOntology")
nxdl_info = load_all_nxdls()

with onto:
    class NeXus(owlready2.Thing):
        comment = 'NeXus concept'

    class NXobject(NeXus):
        comment = nxdl_info["base_classes"]['NXobject']['doc'].replace('\t','') # NeXus documentation string
        # seeAlso = base_class_web_page_prefix + 'NXobject' + '.html'
    NXobject.set_iri(NXobject, base_iri + 'NXobject')   #set iri using agree pattern for Nexus

    class NeXusBaseClass(NXobject):
        comment = 'NeXus Base Class (Newer entries are found in Contributed Definitions)'
        seeAlso = web_page_prefix + 'base_classes/index.html'
    
    class NeXusApplicationClass(NXobject):
        comment = 'NeXus Application Class (Newer entries are found in Contributed Definitions)'
        seeAlso = web_page_prefix + 'applications/index.html'

    class NeXusField(NXobject):
        comment = 'NeXus Field'

    class NeXusGroup(NXobject):
        comment = 'NeXus Group'

    class NeXusAttribute(NXobject):
        comment = 'NeXus Attribute'
    
    class NeXusAttributeUnit(NeXusAttribute):
        comment = ('NeXus allows users to add units to values stored as NeXusAttributes. For such NeXusAttributes with a unit'
                   ' the following convention is used: \n'
                   ' <attribute_name>_units')
        seeAlso = 'https://manual.nexusformat.org/classes/base_classes/NXdetector_module.html?highlight=_units#nxdetector-module-slow-pixel-direction-offset-units-attribute'

    class NeXusUnit(NeXusAttribute):
        comment = "NeXus Unit is the string representation of the unit for a given NeXus Field."
        label = "NeXusUnit"
    
    class NeXusValue(NXobject):
        comment = "NeXus Value is the value for a given field or attribute."
        label = "NeXusValue"

    class NeXusUnitCategory(NeXus):
        comment = ("Unit categories in NXDL specifications describe the expected type of units for a NeXus field."
                    ""
                    "They should describe valid units consistent with"
                    "the manual section on NeXus units (based on UDUNITS)."
                    "Units are not validated by NeXus.")
        label = "NeXusUnitCategory"

    class NeXusDataType(NeXus):
        comment = "any valid NeXus field or attribute type"
        label = "NeXusDataType"

    class extends(owlready2.AnnotationProperty):
        pass

    # Adding base classes to our ontology
    for nxBaseClass in nxdl_info["base_classes"].keys():
        
        if not nxBaseClass == 'NXobject':    # NXobject can't be subclass of NXobject
            _nx_class = types.new_class(nxBaseClass, (NeXusBaseClass,))
            _nx_class.set_iri(_nx_class, base_iri + "BaseClass/" + nxBaseClass) # use agreed term iri
            nxdl_info["base_classes"][nxBaseClass]['onto_class'] =  _nx_class    # add class to dict 
            _nx_class.comment.append(nxdl_info["base_classes"][nxBaseClass]['doc'])
            _nx_class.extends.append(nxdl_info["base_classes"][nxBaseClass]['extends'])
            _nx_class.label.append(nxBaseClass)
            web_page = web_page_prefix + nxdl_info["base_classes"][nxBaseClass]["category"] + "/" + nxBaseClass + '.html' 
            
            _nx_class.seeAlso.append(web_page)

    for application in nxdl_info["applications"].keys():
        
        if not application == 'NXobject':    # NXobject can't be subclass of NXobject
            _nx_class = types.new_class(application, (NeXusApplicationClass,))
            _nx_class.set_iri(_nx_class, base_iri + "Application/" + application) # use agreed term iri
            nxdl_info["applications"][application]['onto_class'] =  _nx_class    # add class to dict 
            _nx_class.comment.append(nxdl_info["applications"][application]['doc'])
            _nx_class.extends.append(nxdl_info["applications"][application]['extends'])
            _nx_class.label.append(application)
            web_page = web_page_prefix + nxdl_info["applications"][application]["category"] + "/" + application + '.html' 
            
            _nx_class.seeAlso.append(web_page)

    
    for field in nxdl_info["field"].keys():
        _nx_field = types.new_class(field, (NeXusField,))
        _nx_field.set_iri(_nx_field, base_iri + "Field/" + field)
        _nx_field.label.append(field)
        _nx_field.comment.append(nxdl_info["field"][field]["comment"])
        web_page = web_page_prefix + nxdl_info["field"][field]["category"] + "/" + field.split("/")[0] + ".html#"+field.lower().replace("/", "-").replace("_", "-") + "-field"
        _nx_field.seeAlso.append(web_page)

    for group in nxdl_info["group"].keys():
        _nx_group = types.new_class(group, (NeXusGroup,))
        _nx_group.set_iri(_nx_group, base_iri + "Group/" + group)
        _nx_group.label.append(group)
        _nx_group.comment.append(nxdl_info["group"][group]["comment"])
        web_page = web_page_prefix + nxdl_info["group"][group]["category"] + "/" + group.split("/")[0] + ".html#"+group.lower().replace("/", "-").replace("_", "-") + "-group"
        _nx_group.seeAlso.append(web_page)
    
    for attribute in nxdl_info["attribute"].keys():
        _nx_attribute = types.new_class(attribute, (NeXusAttribute,))
        _nx_attribute.set_iri(_nx_attribute, base_iri + "Attribute/" + attribute)
        _nx_attribute.label.append(attribute)
        _nx_attribute.comment.append(nxdl_info["attribute"][attribute]["comment"])
        web_page = web_page_prefix + nxdl_info["attribute"][attribute]["category"] + "/" + attribute.split("/")[0] + ".html#"+attribute.lower().replace("/", "-").replace("_", "-") + "-attribute"
        _nx_attribute.seeAlso.append(web_page)

    unit_categories = load_unit_categories()
    for unit in unit_categories.keys():
        _nx_unit = types.new_class(unit, (NeXusUnitCategory,))
        _nx_unit.set_iri(_nx_unit, base_iri + "Units/" + unit)
        _nx_unit.label.append(unit)
        _nx_unit.comment.append(unit_categories[unit]["doc"])
        # _nx_unit.example.extend(unit_categories[unit]["examples"])  #TODO: Figure out how to add examples to the ontology
        web_page = web_page_base_prefix + "nxdl-types.html#" + unit.lower().replace("_", "-")
        _nx_unit.seeAlso.append(web_page)

    data_types = load_data_types()
    for dtype in data_types.keys():
        _nx_dtype = types.new_class(dtype, (NeXusDataType,))
        _nx_dtype.set_iri(_nx_dtype, base_iri + "DataTypes/" + dtype)
        _nx_dtype.label.append(dtype)
        _nx_dtype.comment.append(data_types[dtype]["doc"])
        web_page = web_page_base_prefix + "nxdl-types.html#" + dtype.lower().replace("_", "-")
        _nx_dtype.seeAlso.append(web_page)


onto.save(file = "../ontology/NeXusOntology.owl", format = "rdfxml")
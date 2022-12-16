from os import walk
import owlready2
import xml.dom.minidom
import xml.etree.ElementTree as ET
import types
from nexusutils.nexus import nexus

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

def get_min_occurs_from_xml_node(element, isBase):
    if element.get("minOccurs"):
        return int(element.get("minOccurs"))
    elif element.get("optional") == "true" or element.get("recommended") == "true" or element.get("required") == "false":
        return 0
    elif element.get("optional") == "false" or element.get("recommended") == "false" or element.get("required") == "true":
        return 1
    elif isBase:
        return 0
    return 1

def get_max_occurs_from_xml_node(element):
    maxOccurs = element.get("maxOccurs")
    if maxOccurs and maxOccurs != "unbounded":
        return int(element.get("maxOccurs"))
    return None

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
                nxdl_info[xml_tag][path] = {"comment": safe_get_xml_doc(element), "category": file.split("/")[-2], "type": element.get("type") or "NX_CHAR", "unit_category": element.get("units") or "NX_ANY",
                                            "minOccurs": get_min_occurs_from_xml_node(element, root.get("category") == "base"), "maxOccurs": get_max_occurs_from_xml_node(element)}
                enums = nexus.get_enums(element)[1].strip("[").strip("]")
                if enums != "":
                    nxdl_info[xml_tag][path]["enums"] = enums.split(",")
                elist = nexus.get_inherited_nodes(nxdl_path=path[path.find("/"):], nx_name=path[:path.find("/")])[2]
                if len(elist)>1:
                    nxdl_info[xml_tag][path]["superclass_path"] = nexus.get_node_docname(elist[1]).replace(".nxdl.xml:","")

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
    
    class NeXusAttribute(NXobject):
        comment = 'NeXus Attribute'

    #class NeXusUnit(NeXusAttribute):
    #    comment = "NeXus Unit is the string representation of the unit for a given NeXus Field."
    #    label = "NeXusUnit"

    class NeXusField(NXobject):
        comment = 'NeXus Field'
        # is_a = [has.some(NeXusUnit)]

    class NeXusGroup(NXobject):
        comment = 'NeXus Group'
    
    #class NeXusAttributeUnit(NeXusAttribute):
    #    comment = ('NeXus allows users to add units to values stored as NeXusAttributes. For such NeXusAttributes with a unit'
    #               ' the following convention is used: \n'
    #               ' <attribute_name>_units')
    #    seeAlso = 'https://manual.nexusformat.org/classes/base_classes/NXdetector_module.html?highlight=_units#nxdetector-module-slow-pixel-direction-offset-units-attribute'
    
    #class NeXusUnit(NXobject):
    #    comment = "NeXus Unit is the unit for a given field or attribute."
    #    label = "NeXusUnit"

    class NeXusUnitCategory(NeXus):
        comment = ("Unit categories in NXDL specifications describe the expected type of units for a NeXus field."
                    ""
                    "They should describe valid units consistent with"
                    "the manual section on NeXus units (based on UDUNITS)."
                    "Units are not validated by NeXus.")
        label = "NeXusUnitCategory"

    class NeXusEnumerationItem(NeXus):
        comment = "This represents an individual as an enumeration item acceptable for certain NeXusValue."
        label = "NeXusEnumerationItem"

    class NeXusDataType(NeXus):
        comment = "any valid NeXus field or attribute type"
        label = "NeXusDataType"

    owlready2.AllDisjoint([NeXusDataType, NeXusEnumerationItem,NeXusUnitCategory,NXobject])
    owlready2.AllDisjoint([NeXusGroup,NeXusField,NeXusAttribute])
    owlready2.AllDisjoint([NeXusBaseClass,NeXusField,NeXusAttribute])
    owlready2.AllDisjoint([NeXusApplicationClass,NeXusField,NeXusAttribute])



    class extends(owlready2.AnnotationProperty):
        pass

    class has(NXobject >> NXobject):
        comment = 'A representation of a "has a" relationship.'
    class actualValue(owlready2.DataProperty):
        domain = [NeXus]
    class hasValue(owlready2.FunctionalProperty, NXobject >> NeXusDataType):
        comment = 'Representation fo having a Value assigned.'
    class hasUnit(owlready2.FunctionalProperty, NeXusField >> NeXusUnitCategory):
        comment = 'Representation of having a Unit assigned.'
    owlready2.AllDisjoint([has,hasValue,hasUnit,actualValue])

    def set_is_a_or_equivalent(subclass, superclass):
        def has_diff_relations(subclass, superclass):
            return len(list(set([str(x) for x in subclass.is_a if isinstance(x, owlready2.class_construct.Restriction)]) - set([str(x) for x in superclass.is_a if isinstance(x, owlready2.class_construct.Restriction)])))>0
        def has_oneof_relation(owl_class):
            return "'OneOf([" in str([str(x) for x in subclass.is_a])
        if subclass.comment[0] != "" or has_diff_relations(subclass, superclass) or has_oneof_relation(subclass):
            subclass.is_a.append(superclass)

            # To show that we override values we need to add an exception to the base class if the subclass overrides it in NeXus.
            # Example where NXarpes/../probe overrides NXsource/probe's enumeration list. The syntax below is the protege syntax.
            #         The list in the curly brackets shows a OneOf relationship. 
            # NXsource/probe and (not (NXarpes/ENTRY/INSTRUMENT/SOURCE/probe)) SubClassOf {NXsource/probe/electron , NXsource/probe/muon , NXsource/probe/neutron , NXsource/probe/positron , NXsource/probe/proton , NXsource/probe/ultraviolet , NXsource/probe/x-ray , 'NXsource/probe/visible light'}
        else:
            subclass.equivalent_to.append(superclass)



    unit_categories = load_unit_categories()
    for unit in unit_categories.keys():
        nx_unit = types.new_class(unit, (NeXusUnitCategory,))
        nx_unit.set_iri(nx_unit, base_iri + "Units/" + unit)
        nx_unit.label.append(unit)
        nx_unit.comment.append(unit_categories[unit]["doc"])
        # nx_unit.example.extend(unit_categories[unit]["examples"])  #TODO: Figure out how to add examples to the ontology
        web_page = web_page_base_prefix + "nxdl-types.html#" + unit.lower().replace("_", "-")
        nx_unit.seeAlso.append(web_page)
        unit_categories[unit]["onto_class"] = nx_unit
    owlready2.AllDisjoint([v["onto_class"] for k,v in unit_categories.items()])


    data_types = load_data_types()
    for dtype in data_types.keys():
        # nx_dtype = types.new_class(dtype, (str,)) # TODO: This should be the appropriate Python data type.
        # owlready2.declare_datatype(nx_dtype, base_iri + "DataTypes/" + dtype, lambda x : x, lambda x : x)
        nx_dtype = types.new_class(dtype, (NeXusDataType,)) # TODO: This should be the appropriate Python data type.
        nx_dtype.set_iri(nx_dtype, base_iri + "DataTypes/" + dtype)
        nx_dtype.label.append(dtype)
        nx_dtype.comment.append(data_types[dtype]["doc"])
        web_page = web_page_base_prefix + "nxdl-types.html#" + dtype.lower().replace("_", "-")
        nx_dtype.seeAlso.append(web_page)
        data_types[dtype]["onto_class"] = nx_dtype       
    owlready2.AllDisjoint([v["onto_class"] for k,v in data_types.items()])

    # Adding base classes to our ontology
    for nxBaseClass in nxdl_info["base_classes"].keys():
        if not nxBaseClass == 'NXobject':    # NXobject can't be subclass of NXobject
            nx_class = types.new_class(nxBaseClass, (NeXusBaseClass,))
            nx_class.set_iri(nx_class, base_iri + "BaseClass/" + nxBaseClass) # use agreed term iri
            nxdl_info["base_classes"][nxBaseClass]['onto_class'] =  nx_class    # add class to dict 
            nx_class.comment.append(nxdl_info["base_classes"][nxBaseClass]['doc'])
            # TODO: replace this extends with set_is_a_or_equivalent() 
            nx_class.extends.append(nxdl_info["base_classes"][nxBaseClass]['extends'])
            nx_class.label.append(nxBaseClass)
            web_page = web_page_prefix + nxdl_info["base_classes"][nxBaseClass]["category"] + "/" + nxBaseClass + '.html' 
            
            nx_class.seeAlso.append(web_page)

    for application in nxdl_info["applications"].keys():
        if not application == 'NXobject':    # NXobject can't be subclass of NXobject
            nx_class = types.new_class(application, (NeXusApplicationClass,))
            nx_class.set_iri(nx_class, base_iri + "Application/" + application) # use agreed term iri
            nxdl_info["applications"][application]['onto_class'] =  nx_class    # add class to dict 
            nx_class.comment.append(nxdl_info["applications"][application]['doc'])
            nx_class.extends.append(nxdl_info["applications"][application]['extends'])
            nx_class.label.append(application)
            web_page = web_page_prefix + nxdl_info["applications"][application]["category"] + "/" + application + '.html' 
            
            nx_class.seeAlso.append(web_page)
        
    for group in nxdl_info["group"].keys():
        nx_group = types.new_class(group, (NeXusGroup,))
        nx_group.set_iri(nx_group, base_iri + "Group/" + group)
        nx_group.label.append(group)
        nxdl_info["group"][group]["onto_class"] = nx_group
        nx_group.comment.append(nxdl_info["group"][group]["comment"])
        web_page = web_page_prefix + nxdl_info["group"][group]["category"] + "/" + group.split("/")[0] + ".html#"+group.lower().replace("/", "-").replace("_", "-") + "-group"
        nx_group.seeAlso.append(web_page)

        def set_has_a_relationships(path, xml_tag, nx_class, parent_tag):
            parent = path[:path.rfind("/")]
            if "/" not in parent: # is either base class or appdef
                if parent in nxdl_info["base_classes"]:
                    nxdl_info["base_classes"][parent]["onto_class"].is_a.append(has.min(nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                    if nxdl_info[xml_tag][path]["maxOccurs"]:
                        nxdl_info["base_classes"][parent]["onto_class"].is_a.append(has.max(nxdl_info[xml_tag][path]["maxOccurs"], nx_class))
                else:
                    nxdl_info["applications"][parent]["onto_class"].is_a.append(has.min(nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                    if nxdl_info[xml_tag][path]["maxOccurs"]:
                        nxdl_info["applications"][parent]["onto_class"].is_a.append(has.max(nxdl_info[xml_tag][path]["maxOccurs"], nx_class))
            else:
                nxdl_info[parent_tag][parent]["onto_class"].is_a.append(has.min(nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                if nxdl_info[xml_tag][path]["maxOccurs"]:
                    nxdl_info[parent_tag][parent]["onto_class"].is_a.append(has.max(nxdl_info[xml_tag][path]["maxOccurs"], nx_class))
        set_has_a_relationships(group, "group", nx_group, "group")


    for group in nxdl_info["group"].keys():
        if "superclass_path" in nxdl_info["group"][group].keys():
            superclass_path = nxdl_info["group"][group]["superclass_path"]
            if superclass_path in nxdl_info["group"].keys():
                pclass_super = nxdl_info["group"][superclass_path]["onto_class"]
            else:
                pclass_super = nxdl_info["base_classes"][superclass_path]["onto_class"]
            set_is_a_or_equivalent(nxdl_info["group"][group]["onto_class"], pclass_super)
    
    for field in nxdl_info["field"].keys():
        nx_field = types.new_class(field, (NeXusField,))
        nx_field.set_iri(nx_field, base_iri + "Field/" + field)
        nx_field.label.append(field)
        nx_field.comment.append(nxdl_info["field"][field]["comment"])
        web_page = web_page_prefix + nxdl_info["field"][field]["category"] + "/" + field.split("/")[0] + ".html#"+field.lower().replace("/", "-").replace("_", "-") + "-field"
        nx_field.seeAlso.append(web_page)
        # nx_field.is_a.append(has.some(data_types[nxdl_info["field"][field]["type"]]["onto_class"]))
        nx_field.is_a.append(hasValue.some(data_types[nxdl_info["field"][field]["type"]]["onto_class"]))
        nx_field.is_a.append(hasValue.max(0,owlready2.Not(data_types[nxdl_info["field"][field]["type"]]["onto_class"])))
        nx_field.is_a.append(hasUnit.max(1, unit_categories[nxdl_info["field"][field]["unit_category"]]["onto_class"]))
        nxdl_info["field"][field]["onto_class"] = nx_field

        if "enums" in nxdl_info["field"][field]:
            nxdl_info["field"][field]["enums_classes"] = []
            for enum in nxdl_info["field"][field]["enums"]:
                nx_enum = types.new_class(field+"/"+enum, (NeXusEnumerationItem,))
                nx_enum.label.append(field+"/"+enum)
                nx_enum.seeAlso.append(web_page)
                nxdl_info["field"][field]["enums_classes"].append(nx_enum)
                    
            nx_field.is_a.append(owlready2.OneOf(nxdl_info["field"][field]["enums_classes"]))
        set_has_a_relationships(field, "field", nx_field, "group")

    for field in nxdl_info["field"].keys():
        if "superclass_path" in nxdl_info["field"][field].keys():
            superclass_path = nxdl_info["field"][field]["superclass_path"]
            pclass_super = nxdl_info["field"][superclass_path]["onto_class"]
            set_is_a_or_equivalent(nxdl_info["field"][field]["onto_class"], pclass_super)
    
    for attribute in nxdl_info["attribute"].keys():
        nx_attribute = types.new_class(attribute, (NeXusAttribute,))
        nx_attribute.set_iri(nx_attribute, base_iri + "Attribute/" + attribute)
        nx_attribute.label.append(attribute)
        nx_attribute.comment.append(nxdl_info["attribute"][attribute]["comment"])
        web_page = web_page_prefix + nxdl_info["attribute"][attribute]["category"] + "/" + attribute.split("/")[0] + ".html#"+attribute.lower().replace("/", "-").replace("_", "-") + "-attribute"
        nx_attribute.seeAlso.append(web_page)
        nx_attribute.is_a.append(hasValue.some(data_types[nxdl_info["attribute"][attribute]["type"]]["onto_class"]))
        nx_attribute.is_a.append(hasValue.max(0,owlready2.Not(data_types[nxdl_info["attribute"][attribute]["type"]]["onto_class"])))
        nxdl_info["attribute"][attribute]["onto_class"] = nx_attribute

        if "enums" in nxdl_info["attribute"][attribute]:
            nxdl_info["attribute"][attribute]["enums_classes"] = []
            for enum in nxdl_info["attribute"][attribute]["enums"]:
                nx_enum = types.new_class(attribute+"/"+enum, (NeXusEnumerationItem,))
                nx_enum.label.append(attribute+"/"+enum)
                nx_enum.seeAlso.append(web_page)
                nxdl_info["attribute"][attribute]["enums_classes"].append(nx_enum)
                    
            nx_attribute.is_a.append(owlready2.OneOf(nxdl_info["attribute"][attribute]["enums_classes"]))
        set_has_a_relationships(attribute, "attribute", nx_attribute, "group" if attribute[:attribute.rfind("/")] in nxdl_info["group"] else "field")

    for attribute in nxdl_info["attribute"].keys():
        if "superclass_path" in nxdl_info["attribute"][attribute].keys():
            superclass_path = nxdl_info["attribute"][attribute]["superclass_path"]
            try:
                pclass_super = nxdl_info["attribute"][superclass_path]["onto_class"]
                set_is_a_or_equivalent(nxdl_info["attribute"][attribute]["onto_class"], pclass_super)
            except KeyError:
                print("Warning: " + attribute + " is not of same type as " + superclass_path)
            
    
    # Instances - Dataset
    dataset="dataset_000/"
    
    # value = data_types["NX_CHAR"]["onto_class"]("Key something")
    # valueInt = data_types["NX_INT"]["onto_class"](123)
    # valueFloat = data_types["NX_FLOAT"]["onto_class"](123.456)
    # unit1 = unit_categories["NX_ANY"]["onto_class"]("keV")
    value = data_types["NX_CHAR"]["onto_class"]()
    value.actualValue = ["Key something"]
    valueInt = data_types["NX_INT"]["onto_class"]()
    valueInt.actualValue = [123]
    valueFloat = data_types["NX_FLOAT"]["onto_class"]()
    valueFloat.actualValue = [123.456]
    unit1 = unit_categories["NX_ANY"]["onto_class"]()
    unit1.actualValue = ["keV"]

    name = nxdl_info["field"]["NXsensor/name"]["onto_class"]()
    name.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor/name")
    name.hasValue = value
    name.hasUnit = unit1

    ltv = nxdl_info["field"]["NXsensor/low_trip_value"]["onto_class"]()
    ltv.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor/low_trip_value")
    ltv.hasValue = valueFloat
    ltv.hasUnit = unit1

    current_sensor = nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor"]["onto_class"]()
    current_sensor.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor")
    current_sensor.has = [name,ltv]

    environment = nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT"]["onto_class"]()
    environment.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT")
    environment.has = [current_sensor]

    instrument = nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT"]["onto_class"]()
    instrument.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT")
    instrument.has = [environment]

    entry = nxdl_info["group"]["NXiv_temp/ENTRY"]["onto_class"]()
    entry.label.append(dataset+"NXiv_temp/ENTRY")
    entry.has = [instrument]

    appdef = nxdl_info["applications"]["NXiv_temp"]["onto_class"]()
    appdef.label.append(dataset+"NXiv_temp")
    appdef.has = [entry]

    root = nxdl_info["base_classes"]["NXroot"]["onto_class"]()
    root.label.append(dataset)
    root.has = [entry]


    # introducing contradictions
    
    # different datatypes
    # ltv.hasValue.append(valueInt)
    # ltv.hasValue.append(value)

    # wrong enums



onto.save(file = "../ontology/NeXusOntology.owl", format = "rdfxml")
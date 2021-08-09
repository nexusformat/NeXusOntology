#!/usr/bin/env python
# coding: utf-8

# # Python code to parse nexus base class nxdl file contents to python dict and create owl ontology
# 
# ## To create the NeXus ontology edit cell 2 and execute the whole notebook.

# In[1]:


#modules to install
#pip install owlready2
#pip install pygithub


# In[2]:


#################################################################
#github token and file path for created owl file - edit this cell
_script_version = '1.1' # script version - update after edit
token = "" # insert your github token
out_path = '/home/mvs/ontology'
tmp_file_path = '/home/mvs/tmp'
#################################################################


# In[3]:


#get a list of NeXus base class urls from github

base_iri = 'http://purl.org/nexusformat/definitions/'
nexus_repo = 'nexusformat/definitions' # for github api
onto_name = 'NeXusOntology'
_creator = 'NeXus International Advisory Committee (NIAC)'
_licence = 'https://creativecommons.org/licenses/by/4.0/'
_publication = 'https://doi.org/10.5281/zenodo.4806026'

onto_iri = base_iri + onto_name

# pickle files used to avoid uneccesary parsing of NeXus files, mainly for development
defn_pickle_file = tmp_file_path + '/defn.p'
baseclass_pickle_file = tmp_file_path + '/baseclass.p'
types_pickle_file = tmp_file_path + '/types.p'
tags_pickle_file = tmp_file_path + '/tags.p'

base_class_web_page_prefix = 'https://manual.nexusformat.org/classes/base_classes/'
application_definition_web_page_prefix = 'https://manual.nexusformat.org/classes/applications/'
types_url = 'https://raw.githubusercontent.com/nexusformat/definitions/main/nxdlTypes.xsd'

join_string = '-'       #string added between joined base class and field names for identifiers
join_string_label = ' ' #string added between joined base class and fieldnames for rdfs:label

nexus_website = 'https://www.nexusformat.org/'
nexus_repository = 'https://github.com/nexusformat'

default_units = 'NX_UNITLESS'   #use this if units not specified

import datetime
import pickle
   
# Ontology metadata comment
onto_comment = '''

    This ontology extracts information about NeXus classes and fields from
    NeXus nxdl definition files on the NeXus GitHub site.
    See 'seeAlso' for links to the NeXus project, including licencing information.
    This project was undertaken under ExPaNDS WP3.2 (https://expands.eu/)
    
    Purpose
    The ontology is designed to fulfil several purposes. First, it creates unique identifiers
    for each of the NeXus fields which would normally exist only within the namespaces of the
    defining NeXus classes. This is the primary goal and provides PIDs for annotation and tagging.
    The second purpose is to allow, via separate ontologies, NeXus fields and classes to be mapped
    onto equivalent or related terms defined elsewhere.
    Finally, we hope that this ontology, when used with a tool such as Protege, will provide a
    useful 'NeXus Explorer' tool to gain a quick overview of NeXus with links to official NeXus 
    documentation.
    
    Design Philosophy
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
    
    Caveats
    Some NeXus classes (e.g. NXtransformations) are related specifically to the class that they are contained in.
    This relationship is not preserves.
    NeXus allows multiple instances of metadata fields within a dataset. Relating multiple field values to a
    single identifier will require a selection algorithm.
    
    Version
    The version string is the NeXus version followed by the ontology version.
    
'''

# To avoid re-parsing NeXus files after initial run, execute this
# cell instead of the next three

classDict = pickle.load( open(baseclass_pickle_file , "rb" ) )
applicationDict = pickle.load( open(defn_pickle_file , "rb" ) )
typesDict = pickle.load( open(types_pickle_file , "rb" ) )
tagsDict = pickle.load( open(tags_pickle_file , "rb" ) )

# In[4]:


# Create a dictionary of NeXus simple types (unit categories)

from github import Github
import xml.dom.minidom
import urllib
import pickle

types_dom = xml.dom.minidom.parse(urllib.request.urlopen(types_url))

typesDict = {}
for nxtype in types_dom.getElementsByTagName('xs:simpleType'):
    name = nxtype.getAttribute('name')
    doc = nxtype.getElementsByTagName('xs:documentation')
    docstr = doc[0].firstChild.nodeValue
    docstr = docstr.replace('\n','').replace('\t','')
    typesDict[name] = {'doc': docstr}


pickle.dump(typesDict, open(types_pickle_file, "wb" ) )


# In[5]:


# parse nexus base class files via url to python dictionary


from github import Github
import xml.dom.minidom
import os
import urllib
import time
import pickle
import json

g = Github(token)
repo = g.get_repo(nexus_repo)

with urllib.request.urlopen(repo.tags_url) as url:
    tags = json.loads(url.read().decode())
    tagsDict = tags[0]  # get version tags from master branch


base_class_url = []
for file in repo.get_contents("base_classes"):
    if str(file).split('.')[-2] == 'nxdl':
        base_class_url += [file.download_url]


_maxTries = 10 # try to parse file this many times before giving up

def addFieldToDict(classDict, field, defn_name): # make a function to be reused later
    #defn_name is used to add application definition to field dict if the field is defined in an app deff.
    field_name = field.getAttribute('name')
    
    deprecationAttribute = field.getAttribute('deprecated')
    if not deprecationAttribute == '':
        print("=== Deprecation warning %s in %s: %s" % (field_name, className, deprecationAttribute))    

    long_name = className + join_string + field_name
    label = className + join_string_label + field_name

    if not long_name in classDict[className]['fields'].keys():
        #print('~~~ field did not exist: %s' % long_name)
        classDict[className]['fields'][long_name] = {} # create dictionary for field if doesn't exist

        
        classDict[className]['fields'][long_name]['fieldName'] = field_name
        classDict[className]['fields'][long_name]['units'] = field.getAttribute('units')
        if classDict[className]['fields'][long_name]['units'] == '':
            classDict[className]['fields'][long_name]['units'] = default_units
                        
        classDict[className]['fields'][long_name]['xml_file'] = file #xml file where field is defined
        classDict[className]['fields'][long_name]['defn_name'] = defn_name # application defn name is passed in if field is defined in a defn, else None is used
        classDict[className]['fields'][long_name]['label'] = label # compound name for label

        _type = field.getAttribute('type')
        if _type == '':
            _type = 'NX_CHAR'   # default if not specified

        classDict[className]['fields'][long_name]['type'] = _type

        try:
            field_doc = field.getElementsByTagName('doc')[0].firstChild.nodeValue.replace('\n','')
        except:
            field_doc = ''
        classDict[className]['fields'][long_name]['fieldDoc'] = field_doc
   

classDict = {} # create empty classDict dictionary


for file in base_class_url:
    #print(file)

    for i in range(_maxTries):
        try:
            dom1 = xml.dom.minidom.parse(urllib.request.urlopen(file))
            break
        except:
            print('=== Problem parsing %s; try %i times then give up' % (file, _maxTries))
            time.sleep(1)
    
    defn = dom1.getElementsByTagName('definition')[0]
    
    className = defn.getAttribute('name') #class name from name attribute in definition
     
    if not className in classDict.keys():
        classDict[className] = {} # each class is a dictionary - create a new one if doesn't exist
    
    classDict[className]['xml_file'] = file

    classDict[className]['extends'] = defn.getAttribute('extends')
    
    
    docstr = ''
    for docelement in dom1.getElementsByTagName('doc'):
        if docelement.parentNode.tagName == 'definition':
            docstr = docelement.firstChild.nodeValue.replace('\n','')
            break
    classDict[className]['classDoc'] = docstr
    
    
    
    if not 'fields' in classDict[className].keys():
        classDict[className]['fields'] = {} # create fields dictionary for class if doesn't exist
    
 
    # look for fields in group but not recursive
    flds = (field for field in defn.getElementsByTagName('field') if field.parentNode == defn)        
    
    for field in flds:
        addFieldToDict(classDict, field, None)
        
    classDict[className]['groups_cited'] = []
    for group in defn.getElementsByTagName('group'):
        groupName = group.getAttribute('type')
        classDict[className]['groups_cited'] += [groupName]

        
pickle.dump(classDict, open(baseclass_pickle_file, "wb" ) )
pickle.dump(tagsDict, open(tags_pickle_file, "wb" ) )



# In[6]:


# parse nexus application definitions
# extract extra base class fields and add to base class dictionary

import xml.dom.minidom
import os
#import yaml
import urllib
import time
import pickle


#get a list of NeXus base application definition urls from github       
application_url = []
for file in repo.get_contents("applications"):
    try:
        if str(file).split('.')[-2] == 'nxdl':
            application_url += [file.download_url]
    except:
        pass


applicationDict = {}

for file in application_url:


    dom1 = xml.dom.minidom.parse(urllib.request.urlopen(file)) # pick one at random 

    appdefn = dom1.getElementsByTagName('definition')[0]
    defn_name = appdefn.getAttribute('name')

    group = dom1.getElementsByTagName('group')
    classList, classNameList = [], []
    for defn in group:
        className = defn.getAttribute('type')
        classNameList += [className]
    
        # look for fields in group but not recursive
        flds = (field for field in defn.getElementsByTagName('field') if field.parentNode == defn)           
        for field in flds:
            #print('=== Added field %s from class %s in application definition %s' % (field.getAttribute('name'), className, defn_name))
            addFieldToDict(classDict, field, defn_name)

            
    docstr = ''        
    for docelement in dom1.getElementsByTagName('doc'):
        if docelement.parentNode.tagName == 'definition':
            docstr = docelement.firstChild.nodeValue.replace('\n','')
            break
            
    
    # get information about application definition (name, xml_file, extends, doc) and add to dict
    
    applicationDict[defn_name] = {} # new entry with definition nae as key
    applicationDict[defn_name]['extends'] = appdefn.getAttribute('extends')
    applicationDict[defn_name]['doc'] = docstr
    applicationDict[defn_name]['xml_file'] = file
    applicationDict[defn_name]['groups_cited'] = classNameList     


pickle.dump(classDict, open(baseclass_pickle_file, "wb" ) ) # re-save class dict (now has new fields)
pickle.dump(applicationDict, open(defn_pickle_file, "wb" ) )
#pprint(applicationDict)
        
        
     


# In[7]:


# create owl ontology from previously created dicts using owlready2 module

from owlready2 import *
import types
import datetime

onto_path.append(out_path)
onto = get_ontology(onto_iri)

# get properties from cdterms
with get_ontology("http://purl.org/dc/terms/"):
    class creator(AnnotationProperty): pass
    class licence(AnnotationProperty): pass
    class created(AnnotationProperty): pass

with onto:
   
    #xxxx delete ###############################################
    #try:
    #    nexus_version = tagsDict['name']
    #except:
    #    nexus_version = 'Unknown'
    #    print('=== Problem getting version from github name tag')
    #    
    #version = 'Creation date: %s\nNeXus version: %s' % (datetime.date.today().strftime("%b-%d-%Y"), nexus_version)

    
    version = '%s-%s' % (tagsDict['name'], _script_version) # from NeXus tag and script version
    
    
    onto.metadata.versionInfo.append(version)
    onto.metadata.creator = _creator
    onto.metadata.licence = _licence
    onto.metadata.seeAlso.append(nexus_website)
    onto.metadata.seeAlso.append(nexus_repository)
    onto.metadata.seeAlso.append(_publication)
    onto.metadata.comment.append(onto_comment)
    onto.metadata.created.append(datetime.date.today().strftime("%b-%d-%Y"))
    
    
    class NeXus(Thing):
        comment = 'NeXus concept'
        
    class dataset(Thing):
        comment = 'Dummy data set'
   
    class NeXusField(ObjectProperty):
        domain = [dataset]
        comment = 'NeXus field (ObjectProperty). Unique names are created by prepending the NeXus class name to the NeXus field name'
      
    class NXobject(NeXus):
        comment = classDict['NXobject']['classDoc'].replace('\t','') # NeXus documentation string
        seeAlso = base_class_web_page_prefix + 'NXobject' + '.html'
    NXobject.set_iri(NXobject, base_iri + 'NXobject')   #set iri using agree pattern for Nexus
           
    class NeXusBaseClass(NXobject):
        comment = 'NeXus Base Class'
        seeAlso = 'https://manual.nexusformat.org/classes/index.html'
    
    class NeXusApplicationDefinition(NXobject):
        comment = 'NeXus Application Definition'
        seeAlso = 'https://manual.nexusformat.org/classes/index.html'
      
    class citesGroup(NXobject >> NeXusBaseClass):
        comment = 'NXobject cites base class relationship'
           
    class extends(AnnotationProperty):
        pass
    
    class NeXusType(AnnotationProperty):
        pass
    
    class unit(AnnotationProperty):
        pass
    
    class NeXusClass(AnnotationProperty):
        pass
    
    class unitCategory(NeXus):
        comment = 'NeXus unit category. Can be considered instances of a measure. Assign data properties '             'hasValue(any), hasMinValue(any), hasMaxValue(any), hasUnits(str)'
        
    class hasValue(DataProperty, FunctionalProperty):
        domain = [unitCategory]
        comment = 'NeXus field value'
        
    class hasMinValue(DataProperty, FunctionalProperty):
        domain = [unitCategory]
        comment = 'Minimum of NeXus field value'
        
    class hasMaxValue(DataProperty, FunctionalProperty):
        domain = [unitCategory]
        comment = 'Maximum of NeXus field value'    
    
    class hasUnit(DataProperty, FunctionalProperty):
        domain = [unitCategory]
        range = [str]
        comment = 'NeXus unit (string). Should be consistent with unit category.'
    
    
    for unit in typesDict.keys():
        if unit == 'anyUnitsAttr': # general description, not specific unit category
            unitCategory.comment.append(typesDict[unit]['doc']) # use to document unitCategory class
        elif unit == 'primitiveType': # do nothing with this entry
            pass
        else:
            typesDict[unit]['class'] = types.new_class(unit, (unitCategory,)) # create new unit category subclass
            typesDict[unit]['class'].comment.append(typesDict[unit]['doc'])   # document it

    
    
    for nxBaseClass in classDict.keys():
        
        if not nxBaseClass == 'NXobject':    # NXobject can't be subclass of NXobject
            _nx_class = types.new_class(nxBaseClass, (NeXusBaseClass,))
            _nx_class.set_iri(_nx_class, base_iri + nxBaseClass) # use agreed term iri
            classDict[nxBaseClass]['onto_class'] =  _nx_class    # add class to dict 
            _nx_class.comment.append(classDict[nxBaseClass]['classDoc'])
            _nx_class.extends.append(classDict[nxBaseClass]['extends'])
            web_page = base_class_web_page_prefix + nxBaseClass + '.html' 
            
            _nx_class.seeAlso.append(web_page) 
                
            for nxField in classDict[nxBaseClass]['fields'].keys():  #loop through each field in base class
   
                _nx_field = types.new_class(nxField, (NeXusField, ))
    
                _nx_field.set_iri(base_iri + nxField) # use agreed term iri (seem to need only single parameter for properties)
            
                classDict[nxBaseClass]['fields'][nxField]['class'] = _nx_field
    
                
                _nx_field.comment.append(classDict[nxBaseClass]['fields'][nxField]['fieldDoc'])
                _nx_field.label.append(classDict[nxBaseClass]['fields'][nxField]['label'])
      
        
                defn_name = classDict[nxBaseClass]['fields'][nxField]['defn_name']
            
                            
                if defn_name != None:
                    #Field is defined by an application definition; give app defn web page (no anchor - might add later)
                    web_page = application_definition_web_page_prefix + defn_name + '.html'
                    _nx_field.seeAlso.append(web_page)
                else:
                    #Field is defined by base class file; give base class web page with arhchor
                    
                    anchor = '#%s-%s-field' % (nxBaseClass.lower(), 
                                               classDict[nxBaseClass]['fields'][nxField]['fieldName'].lower())
                    anchor = anchor.replace('_', '-') # replace symbols for anchors
                    
                    web_page = base_class_web_page_prefix + nxBaseClass + '.html' + anchor
                    _nx_field.seeAlso.append(web_page)
                
                
                unit_string = classDict[nxBaseClass]['fields'][nxField]['units']
                unit_class = typesDict[unit_string]['class']
                _nx_class.is_a.append(_nx_field.some(unit_class))
                     
                _nx_field.NeXusClass.append(_nx_class)

                _nx_field.range = [unit_class]
                

    # second loop required to ensure all classes defined before trying to cite them            
    for nxBaseClass in classDict.keys():  
        if not nxBaseClass == 'NXobject':    # NXobject can't be subclass of NXobject
            for cited in classDict[nxBaseClass]['groups_cited']:
                classDict[nxBaseClass]['onto_class'].is_a.append(citesGroup.some(classDict[cited]['onto_class']))
                
                
    for application in applicationDict.keys():
        _nx_app = types.new_class(application, (NeXusApplicationDefinition,))
        _nx_app.set_iri(_nx_app, base_iri + application) # use agreed term iri
        
        _nx_app.comment.append(applicationDict[application]['doc'])
        _nx_app.extends.append(applicationDict[application]['extends'])

        web_page = application_definition_web_page_prefix + application + '.html'
        _nx_app.seeAlso.append(web_page)
        
        for base_class in applicationDict[application]['groups_cited']:
            _nx_app.is_a.append(citesGroup.some(classDict[base_class]['onto_class']))


onto.save()




# In[8]:


# create individuals - these are just for testing


with onto:
        
    sample_temp_1 = typesDict['NX_TEMPERATURE']['class']('sample_temp_1')
    sample_temp_1.hasUnit = 'Kelvin'
    sample_temp_1.hasValue = 10
    
    dataset_1 = dataset('dataset1')
    setattr(dataset_1,'NXsample%stemperature' % join_string, [sample_temp_1])
    
    
    beam_energy_1 = typesDict['NX_ENERGY']['class']('beam_energy_1')
    beam_energy_1.hasUnit = 'keV'
    beam_energy_1.hasValue = 12.4
    
    dataset_2 = dataset('dataset2')
    setattr(dataset_2,'NXbeam%sfinal_energy' % join_string, [beam_energy_1]) 

        
onto.save()


# In[ ]:





# In[ ]:





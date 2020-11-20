#!/usr/bin/python3

# Finds unused types defined in a XML schema file.
# Usage: ./SchemaCleanup.py schema.xsd
#
# Limitations:
#   * quick & dirty
#   * ignores namespaces (may not detect unused type if another type with same name exists and is used)
#   * may not be 100% bulletproof and handle 100% of possible cases - please double-check reported results

import sys
import lxml.etree as ET
import collections

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

ns = {
    'xs' : 'http://www.w3.org/2001/XMLSchema'
}
typeDefinitions = dict()
typeUsageCounts = {
    # types added here will be ignored
    # e.g. 'SomeXsdTypeName': 1
}

def typeFound(typeName, schemaFile, sourceline):
    typeDefinitions[typeName] = schemaFile
    typeUsageCounts[typeName] = typeUsageCounts.get(typeName, 0)

def typeUsageFound(typeName):
    typeUsageCounts[typeName] = typeUsageCounts.get(typeName, 0) + 1

def removeNamespace(typeName):
    return typeName.split(':')[-1]

def findTypes(xsdTree, elementName, attributeName, schemaFile):
    for occurrence in xsdTree.getroot().iter("{%s}%s" % (ns['xs'], elementName)):
        typeName = occurrence.attrib.get(attributeName)
        if typeName is not None:
            typeFound(removeNamespace(typeName), schemaFile, occurrence.sourceline)

def findUsageRecursive(xsdTree, rootElement):
    for tag, attribute in [('element', 'type'), ('restriction', 'base'), ('extension', 'base')]:
        for children in rootElement.iter("{%s}%s" % (ns['xs'], tag)):
            typeName = children.get(attribute)
            if typeName is not None:
                element = xsdTree.find("./*[@name='" + typeName + "']")
                if element is not None:
                    typeUsageFound(removeNamespace(typeName))
                    findUsageRecursive(xsdTree, element)

def removeType(xsdTree, typeName):
    element = xsdTree.find("./*[@name='" + typeName + "']")
    if element is not None:
        xsdTree.getroot().remove(element)

def writeFile(tree, filepath):
    xml_str = ET.tostring(tree, doctype='<?xml version="1.0"?>', pretty_print=True, xml_declaration=False)
    with open(filepath, 'wb') as xml_file:
        xml_file.write(xml_str.replace(UNIX_LINE_ENDING, WINDOWS_LINE_ENDING).strip())

if __name__ == "__main__":
    schemaFile = sys.argv[1]

    print("Processing %s..." % schemaFile)
    xsd = ET.parse(schemaFile)

    findTypes(xsd, 'simpleType', 'name', schemaFile)
    findTypes(xsd, 'complexType', 'name', schemaFile)

    # find unused elements in root
    findUsageRecursive(xsd, xsd.find("./"))

    # find unused elements in complex and simple types
    for typeName, usageCount in typeUsageCounts.items():
        if usageCount > 1:
            element = xsd.find("./*[@name='" + typeName + "']")
            if element is not None:
                findUsageRecursive(xsd, element)

    print("*** Unused XSD types ***")
    foundUnused = 0
    for typeName in collections.OrderedDict(sorted(typeUsageCounts.items(), key=lambda t: t[0].lower())):
        if typeUsageCounts[typeName] < 1:
            print("Deleted unused type: %s" % typeName)
            removeType(xsd, typeName)
            foundUnused += 1

    writeFile(xsd, schemaFile)
    print("\n" + "*** Deleted items: %s ***" % foundUnused)
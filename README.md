# Finds unused types defined in a XML schema file.
# Usage: ./SchemaCleanup.py schema.xsd
#
# Limitations:
#   * quick & dirty
#   * ignores namespaces (may not detect unused type if another type with same name exists and is used)
#   * may not be 100% bulletproof and handle 100% of possible cases - please double-check reported results

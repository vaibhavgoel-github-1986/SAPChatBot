from Tools.GetClassDefinition import GetClassDefinition
from Tools.GetExamples import GetExamples
from Tools.GetInterfaceDefinition import GetInterfaceDefinition
from Tools.GetMethodCode import GetMethodCode
from Tools.GetMethodList import GetMethodList 
from Tools.GetTableSchema import GetTableSchema


# Collecting all the Tools
tools = [
    GetMethodList(),
    GetClassDefinition(),
    GetInterfaceDefinition(),
    GetMethodCode(),
    GetTableSchema(),
    GetExamples()
]   


import inspect
import afni_processors
import pkgutil
import re


if __name__ == '__main__':
    package = afni_processors
    for importer,modname,ispkg in pkgutil.iter_modules(package.__path__):
        print "found submodule %s (is a package: %s)" % (modname, ispkg)
        current_module = importer.find_module(modname).load_module(modname)
        for class_name,class_obj in inspect.getmembers(current_module, inspect.isclass):
            print class_name
            print class_obj
            split_classname = [x.lower() for x in re.findall('[A-Z][^A-Z]*',class_name)]
            print '_'.join(split_classname)

"""This module contains helper functions for code generation."""

import re, os
from output import instant_assert, instant_warning, instant_debug, write_file


def mapstrings(format, sequence):
    return "\n".join(format % i for i in sequence)
    

def reindent(code):
    '''Reindent a multiline string to allow easier to read syntax.
    
    Each line will be indented relative to the first non-empty line.
    Start the first line without text like shown in this example::
    
        code = reindent("""
            Foo
            Bar
                Blatti
            Ping
            """)
    
    makes all indentation relative to Foo.
    '''
    lines = code.split("\n")
    space = ""
    # Get initial spaces from first non-empty line:
    for l in lines:
        if l:
            r = re.search(r"^( [ ]*)", l)
            if r is not None:
                space = r.groups()[0]
            break
    if not space:
        return code
    n = len(space)
    instant_assert(space == " "*n, "Logic breach in reindent.")
    return "\n".join(re.sub(r"^%s" % space, "", l) for l in lines)


def write_interfacefile(filename, modulename, code, init_code,
                        additional_definitions, additional_declarations,
                        system_headers, local_headers, wrap_headers, arrays):
    """Generate a SWIG interface file. Intended for internal library use.
    
    The input arguments are as follows:
      - modulename (Name of the module)
      - code (Code to be wrapped)
      - init_code (Code to put in the init section of the interface file)
      - additional_definitions (Definitions to be placed in initial block with
        C code as well as in the main section of the SWIG interface file)
      - additional_declarations (Declarations to be placed in the main section
        of the SWIG interface file)
      - system_headers (A list of system headers with declarations needed by the wrapped code)
      - local_headers (A list of local headers with declarations needed by the wrapped code)
      - wrap_headers (A list of local headers that will be included in the code and wrapped by SWIG)
      - arrays (A nested list, the inner lists describing the different arrays)
    
    The result of this function is that a SWIG interface with
    the name modulename.i is written to the current directory.
    """
    instant_debug("Generating SWIG interface file '%s'." % filename)
    
    # create typemaps 
    typemaps = ""
    valid_types = ['float', 'double', 'short', 'int', 'long', 'long long',
                   'unsigned short', 'unsigned int', 'unsigned long',
                   'unsigned long long']
    for a in arrays:
        if type(a) == tuple:
            a = list(a)
        DATA_TYPE = 'double'
        for vt in valid_types:
            if vt in a:
                DATA_TYPE = vt
                a.remove(vt)
        if 'in' in a:
            # input arrays
            a.remove('in')
            instant_assert(len(a) > 1 and len(a) < 5, "Wrong number of elements in input array")
            if len(a) == 2:
                # 1-dimensional arrays, i.e. vectors
                typemaps += reindent("""
                %%apply (int DIM1, %(dtype)s* IN_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
            elif len(a) == 3:
                # 2-dimensional arrays, i.e. matrices
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, %(dtype)s* IN_ARRAY2) {(int %(n1)s, int %(n2)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            else:
                # 3-dimensional arrays, i.e. tensors
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, int DIM3, %(dtype)s* IN_ARRAY3) {(int %(n1)s, int %(n2)s, int %(n3)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'n3' : a[2], 'array' : a[3], 'dtype' : DATA_TYPE })
        elif 'out' in a:
            # output arrays
            a.remove('out')
            instant_assert(len(a) == 2, "Output array must be 1-dimensional")
            # 1-dimensional arrays, i.e. vectors
            typemaps += reindent("""
            %%apply (int DIM1, %(dtype)s* ARGOUT_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
            """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
        else:
            # in-place arrays
            instant_assert(len(a) > 1 and len(a) < 5, "Wrong number of elements in output array")
            if 'multi' in a:
                # n-dimensional arrays, i.e. tensors > 3-dimensional
                a.remove('multi')
                typemaps += reindent("""
                %%typemap(in) (int %(n)s,int* %(ptv)s,%(dtype)s* %(array)s){
                  if (!PyArray_Check($input)) { 
                    PyErr_SetString(PyExc_TypeError, "Not a NumPy array");
                    return NULL; ;
                  }
                  PyArrayObject* pyarray;
                  pyarray = (PyArrayObject*)$input; 
                  $1 = int(pyarray->nd);
                  int* dims = new int[$1]; 
                  for (int d=0; d<$1; d++) {
                     dims[d] = int(pyarray->dimensions[d]);
                  }
            
                  $2 = dims;  
                  $3 = (%(dtype)s*)pyarray->data;
                }
                %%typemap(freearg) (int %(n)s,int* %(ptv)s,%(dtype)s* %(array)s){
                    // deleting dims
                    delete $2; 
                }
                """ % { 'n' : a[0] , 'ptv' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            elif len(a) == 2:
                # 1-dimensional arrays, i.e. vectors
                typemaps += reindent("""
                %%apply (int DIM1, %(dtype)s* INPLACE_ARRAY1) {(int %(n1)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'array' : a[1], 'dtype' : DATA_TYPE })
            elif len(a) == 3:
                # 2-dimensional arrays, i.e. matrices
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, %(dtype)s* INPLACE_ARRAY2) {(int %(n1)s, int %(n2)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'array' : a[2], 'dtype' : DATA_TYPE })
            else:
                # 3-dimensional arrays, i.e. tensors
                typemaps += reindent("""
                %%apply (int DIM1, int DIM2, int DIM3, %(dtype)s* INPLACE_ARRAY3) {(int %(n1)s, int %(n2)s, int %(n3)s, %(dtype)s* %(array)s)};
                """ % { 'n1' : a[0], 'n2' : a[1], 'n3' : a[2], 'array' : a[3], 'dtype' : DATA_TYPE})
            # end
        # end if
    # end for
    
    system_headers_code = mapstrings('#include <%s>', system_headers)
    local_headers_code  = mapstrings('#include "%s"', local_headers)
    wrap_headers_code1  = mapstrings('#include "%s"', wrap_headers)
    wrap_headers_code2  = mapstrings('%%include "%s"', wrap_headers)

    numpy_i_include = ''
    if arrays:
        numpy_i_include = r'%include "numpy.i"'
    
    interface_string = reindent("""
        %%module  %(modulename)s
        //%%module (directors="1") %(modulename)s

        //%%feature("director");

        %%{
        #include <iostream>
        %(additional_definitions)s 
        %(system_headers_code)s 
        %(local_headers_code)s 
        %(wrap_headers_code1)s 
        %(code)s
        %%}

        //%%feature("autodoc", "1");
        %(numpy_i_include)s
        
        %%init%%{
        %(init_code)s
        %%}

        %(additional_definitions)s
        %(additional_declarations)s
        %(wrap_headers_code2)s
        //%(typemaps)s
        %(code)s;

        """ % locals())
    
    write_file(filename, interface_string)
    instant_debug("Done generating interface file.")


def write_setup(filename, modulename, csrcs, cppsrcs, local_headers, include_dirs, library_dirs, libraries, swig_include_dirs, swigargs, cppargs, lddargs):
    """Generate a setup.py file. Intended for internal library use."""
    instant_debug("Generating %s." % filename)

    swig_include_dirs.append(os.path.join(os.path.dirname(__file__), 'swig'))
    
    # Handle arguments
    swigfilename = "%s.i" % modulename
    wrapperfilename = "%s_wrap.cxx" % modulename
    
    # Treat C and C++ files in the same way for now
    cppsrcs = cppsrcs + csrcs + [wrapperfilename]
    
    swig_args = ""
    if swigargs:
        swig_args = " ".join(swigargs)

    compile_args = ""
    if cppargs:  
        compile_args = ", extra_compile_args=%r" % cppargs 

    link_args = ""
    if lddargs:  
        link_args = ", extra_link_args=%r" % lddargs 

    swig_include_dirs = " ".join("-I%s"%d for d in swig_include_dirs)
    if len(local_headers) > 0:
        swig_include_dirs += " -I.."
    
    # Generate code
    code = reindent("""
        import os
        from distutils.core import setup, Extension
        name = '%s'
        swig_cmd =r'swig -python %s %s %s'
        os.system(swig_cmd)
        sources = %s
        setup(name = '%s',
              ext_modules = [Extension('_' + '%s',
                             sources,
                             include_dirs=%s,
                             library_dirs=%s,
                             libraries=%s %s %s)])  
        """ % (modulename, swig_include_dirs, swig_args, swigfilename, cppsrcs, 
               modulename, modulename, include_dirs, library_dirs, libraries, compile_args, link_args))
    
    write_file(filename, code)
    instant_debug("Done writing setup.py file.")


def _test_write_interfacefile():
    modulename = "testmodule"
    code = "void foo() {}"
    init_code = "/* custom init code */"
    additional_definitions = "/* custom definitions */"
    additional_declarations = "/* custom declarations */"
    system_headers = ["system_header1.h", "system_header2.h"]
    local_headers = ["local_header1.h", "local_header2.h"]
    wrap_headers = ["wrap_header1.h", "wrap_header2.h"]
    arrays = [["length1", "array1"], ["dims", "lengths", "array2"]]
    
    write_interfacefile("%s.i" % modulename, modulename, code, init_code, additional_definitions, additional_declarations, system_headers, local_headers, wrap_headers, arrays)
    print "".join(open("%s.i" % modulename).readlines())


def _test_write_setup():
    modulename = "testmodule"
    csrcs = ["csrc1.c", "csrc2.c"]
    cppsrcs = ["cppsrc1.cpp", "cppsrc2.cpp"]
    local_headers = ["local_header1.h", "local_header2.h"]
    include_dirs = ["includedir1", "includedir2"]
    library_dirs = ["librarydir1", "librarydir2"]
    libraries = ["lib1", "lib2"]
    swig_include_dirs = ["swigdir1", "swigdir2"],
    swigargs = ["-Swigarg1", "-Swigarg2"]
    cppargs = ["-cpparg1", "-cpparg2"]
    lddargs = ["-Lddarg1", "-Lddarg2"]
    
    write_setup("setup.py", modulename, csrcs, cppsrcs, local_headers, include_dirs, library_dirs, libraries, swig_include_dirs, swigargs, cppargs, lddargs)
    print "".join(open("setup.py").readlines())

def unique(list):
    set = {}
    map(set.__setitem__, list, [])
    return set.keys()


def find_vtk_classes(str): 
    pattern = "vtk\w*"
    l = unique(re.findall(pattern, str))
    return l 

def create_typemaps(classes): 
    s = ""

    typemap_template = """
%%typemap(in) %(class_name)s * {
    vtkObjectBase* obj = vtkPythonGetPointerFromObject($input, "%(class_name)s");
    %(class_name)s * oobj = NULL;  
    if (obj->IsA("%(class_name)s")) {
        oobj = %(class_name)s::SafeDownCast(obj); 
        $1 = oobj;  
    }
}

%%typemap(out) %(class_name)s * {
   $result = vtkPythonGetObjectFromPointer($1);
}
   
   """

    for cl in classes: 
        s += typemap_template % { "class_name" : cl } 

    return s


def generate_vtk_includes(classes):
    s = """
#include "vtkPythonUtil.h"
    """
    for cl in classes: 
        s += """
#include \"%s.h\" """ % cl
    return s 


def generate_interface_file_vtk(signature, code):

    interface_template =  """
%%module test
%%{

%(includes)s

%(code)s

%%}

%(typemaps)s 

%(code)s 

"""
    
    class_list = find_vtk_classes(code)
    includes = generate_vtk_includes(class_list) 
    typemaps = create_typemaps(class_list)
    s = interface_template % { "typemaps" : typemaps, "code" : code, "includes" : includes } 
    return s


def write_cmakefile(name):    
    file_template = """
cmake_minimum_required(VERSION 2.6.0)

# This project is designed to be built outside the Insight source tree.
PROJECT(%(name)%s)

# Find ITK.
FIND_PACKAGE(ITK REQUIRED)
IF(ITK_FOUND)
  INCLUDE(${ITK_USE_FILE})
ENDIF(ITK_FOUND)

# Find VTK.
FIND_PACKAGE(VTK REQUIRED)
IF(VTK_FOUND)
  INCLUDE(${VTK_USE_FILE})
ENDIF(VTK_FOUND)

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})


set(SWIG_MODULE_NAME %(name)s)
set(CMAKE_SWIG_FLAGS
  -module ${SWIG_MODULE_NAME}
  -shadow
  -modern
  -modernargs
  -fastdispatch
  -fvirtual
  -nosafecstrings
  -noproxydel
  -fastproxy
  -fastinit
  -fastunpack
  -fastquery
  -nobuildnone
  -Iinclude/swig
  )

set(CMAKE_SWIG_OUTDIR ${CMAKE_CURRENT_BINARY_DIR})

set(SWIG_SOURCES %(name)s.i)

set_source_files_properties(${SWIG_SOURCES} PROPERTIES CPLUSPLUS ON)

include_directories(${PYTHON_INCLUDE_PATH} ${%(name)s_SOURCE_DIR})

set(VTK_LIBS ITKCommon vtkCommon vtkImaging vtkIO vtkFiltering vtkRendering vtkGraphics vtkCommonPythonD vtkFilteringPythonD)

swig_add_module(${SWIG_MODULE_NAME} python ${SWIG_SOURCES})

swig_link_libraries(${SWIG_MODULE_NAME} ${PYTHON_LIBRARIES} ${VTK_LIBS})


    """ % { "name" : name }

    f = open("CMakeLists.txt", 'w')

    f.write(file_template)


def write_vtk_interface_file(signature, code):     
    filename = signature
    ifile = filename + ".i"
    iff = open(ifile, 'w')
    ifile_code = generate_interface_file_vtk(signature, code)
    iff.write(ifile_code)






if __name__ == "__main__":
    _test_write_interfacefile()
    print "\n"*3
    _test_write_setup()

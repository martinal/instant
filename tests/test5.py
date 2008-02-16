#!/usr/bin/python

from instant import create_extension  
import Numeric
import sys
import time


c_code = """
/* add function for vectors with all safety checks removed ..*/ 
void add(int n1, double* array1, int n2, double* array2, int n3, double* array3){
  if ( n1 == n2 && n1 == n3 ) {
     for (int i=0; i<n1; i++) {  
        array3[i] = array1[i] + array2[i]; 
     }
  }
  else {
    printf("The arrays should have the same size."); 
  }
  
}
"""


create_extension(code=c_code, system_headers=["arrayobject.h"], cppargs='-pg',
          include_dirs=[sys.prefix + "/include/python" + sys.version[:3] + "/Numeric"],
          init_code='import_array();', module='test5_ext', 
          arrays = [['n1', 'array1'],['n2', 'array2'],['n3', 'array3']])

from test5_ext import add 
a = Numeric.arange(10000000); a = Numeric.sin(a)
b = Numeric.arange(10000000); b = Numeric.cos(b)
c = Numeric.arange(10000000); c = Numeric.cos(c)
d = Numeric.arange(10000000); d = Numeric.cos(d)



t1 = time.time() 
add(a,b,c)
t2 = time.time()
print 'With instant:',t2-t1,'seconds'

t1 = time.time() 
Numeric.add(a,b,d)
t2 = time.time()
print 'Med numpy:   ',t2-t1,'seconds'

difference = abs(d - c) 
sum = reduce( lambda a,b: a+b, difference)  
print "The difference between the arrays computed by numpy and instant is " + str(sum) 



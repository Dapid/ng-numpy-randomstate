cdef extern from "Python.h":
    double PyFloat_AsDouble(object ob) except? -1.0
    long PyInt_AsLong(object ob) except? -1
    int PyErr_Occurred()
    void PyErr_Clear()

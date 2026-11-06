# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# How to run: imported by deployment_resume before the tiny GPU capability fit.
"""Identify the NVIDIA OpenCL device without installing a GPU package."""
import ctypes


def nvidia_device():
    """Enumerate OpenCL platforms and select the NVIDIA device explicitly."""
    try:
        library = ctypes.WinDLL('OpenCL.dll')
    except OSError as error:
        return {'enumeration_error':str(error),'platforms':[],'selected_parameters':{}}
    library.clGetPlatformIDs.argtypes = [ctypes.c_uint,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint)]
    library.clGetPlatformInfo.argtypes = [ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t)]
    library.clGetDeviceIDs.argtypes = [ctypes.c_void_p,ctypes.c_ulonglong,ctypes.c_uint,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint)]
    library.clGetDeviceInfo.argtypes = [ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t)]
    count = ctypes.c_uint()
    status = library.clGetPlatformIDs(0,None,ctypes.byref(count))
    if status != 0:
        return {'enumeration_status':status,'platforms':[],'selected_parameters':{}}
    platforms = (ctypes.c_void_p*count.value)()
    assert library.clGetPlatformIDs(count,platforms,None)==0
    records = []
    selected = {}
    for pi, platform in enumerate(platforms):
        name = ctypes.create_string_buffer(1024)
        assert library.clGetPlatformInfo(platform,0x0902,len(name),name,None)==0
        device_count = ctypes.c_uint()
        status = library.clGetDeviceIDs(platform,4,0,None,ctypes.byref(device_count))
        if status != 0:
            records.append({'platform':pi,'name':name.value.decode(),'gpu_status':status})
            continue
        devices = (ctypes.c_void_p*device_count.value)()
        assert library.clGetDeviceIDs(platform,4,device_count,devices,None)==0
        for di,device in enumerate(devices):
            device_name = ctypes.create_string_buffer(1024)
            assert library.clGetDeviceInfo(device,0x102B,len(device_name),device_name,None)==0
            record = {'platform':pi,'platform_name':name.value.decode(),'gpu_device':di,'device_name':device_name.value.decode()}
            records.append(record)
            if 'NVIDIA' in record['device_name'].upper():
                selected = {'gpu_platform_id':pi,'gpu_device_id':di}
    return {'enumeration_status':0,'platforms':records,'selected_parameters':selected}

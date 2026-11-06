"""Optional native engine, explicit argv configuration and bounded execution."""
import json
import os
import subprocess
from fastapi import HTTPException

def invoke(payload):
    config=os.getenv('NATIVE_ENGINE')
    if not config: return None
    try:
        argv=json.loads(config)
        if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv):
            raise ValueError('Expected JSON argv array')
        result=subprocess.run(argv,input=payload,text=True,capture_output=True,timeout=5,check=True)
        value=json.loads(result.stdout)
        if not isinstance(value,dict): raise ValueError('Expected JSON object')
        return value
    except (ValueError,OSError,subprocess.SubprocessError):
        raise HTTPException(502,'Native engine unavailable or invalid response')

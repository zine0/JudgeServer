import base64
import ctypes
import json
import resource
import subprocess
# from testcase.models import TestCases,InputFile,OutputFile
from django.http import JsonResponse
from django.views.generic import View


class Judge(View):
    def build(self, lang: str, code: str):
        # 构建命令
        C_BUILD_COMMAND = "gcc --std=c11 -o /tmp/tmp_program -x c -"
        CPP_BUILD_COMMAND = "g++ -o /tmp/tmp_program -x c++ -"
        COMMAND = ''
        
        if lang == 'C':
            COMMAND = C_BUILD_COMMAND
        elif lang == 'Cpp':
            COMMAND = CPP_BUILD_COMMAND
        else:
            raise ValueError("Unsupported language")
        
        # 执行编译命令
        try:
            res = subprocess.run(COMMAND.split(), input=code, encoding='utf-8', stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            if res.returncode != 0:
                raise RuntimeError(f"Compilation failed: {res.stderr}")
            
            # 返回临时文件路径
            return '/tmp/tmp_program'
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess error: {e.stderr}")
    
    def run(self, lang: str, executable_path: str, time: int, mem: int):
        PR_SET_NO_NEW_PRIVS = 38
        PR_SET_SECCOMP = 22
        SECCOMP_MODE_STRICT = 1
        libc = ctypes.CDLL('libc.so.6', use_errno=True)
        
        def set_limit():
            libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
            libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT)
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            resource.setrlimit(resource.RLIMIT_CPU, (time, time))
        
        run_res = subprocess.run([executable_path], preexec_fn=set_limit, capture_output=True)
        if run_res.returncode != 0:
            if run_res.stderr:
                raise RuntimeError(run_res.stderr)
            elif run_res.returncode == 152:
                raise TimeoutError
            elif run_res.returncode == 137:
                raise MemoryError
        return run_res.stdout
    
    # def judge(self,lang:str,executablePath:str,testCase:TestCases) -> list:
    #     result = []
    #     item = {"name":None,"status":None}
    #
    #
    #     res = self.run(lang,executablePath,inp)
    
    def post(self, request):
        result = {}
        json_data = json.loads(request.body)
        lang: str = json_data['lang']
        code: str = base64.b64decode(json_data['code'].encode('utf-8')).decode('utf-8')
        # 构建并编译代码
        executable_path = self.build(lang, code)
        
        try:
            res = self.run(lang,executable_path,json_data['time'],json_data['mem'])
        except RuntimeError as e:
            result['status'] = 'RE'
            result['message'] = str(e)
        except TimeoutError as e:
            result['status'] = 'TLE'
        except MemoryError as e:
            result['status'] = 'MLE'
            
        
        return JsonResponse(result)

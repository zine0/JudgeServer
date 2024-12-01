import base64
import ctypes
import json
import resource
import subprocess
from typing import List
from ctypes import c_int, c_char_p, c_void_p, c_ulong, c_uint, POINTER
from django.http import JsonResponse
from django.views.generic import View

from testcase.models import *


class Judge(View):
    # 常量可以放在类外部或作为类属性
    C_BUILD_COMMAND = "gcc --std=c11 -o /tmp/tmp_program -x c -"
    CPP_BUILD_COMMAND = "g++ -o /tmp/tmp_program -x c++ -"
    
    def build(self, lang: str, code: str):
        # 根据语言选择编译命令
        if lang == 'C':
            command = self.C_BUILD_COMMAND
        elif lang == 'Cpp':
            command = self.CPP_BUILD_COMMAND
        else:
            raise ValueError("Unsupported language")
        
        # 执行编译命令
        try:
            res = subprocess.run(command.split(), input=code, encoding='utf-8', stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            if res.returncode != 0:
                raise RuntimeError(f"Compilation failed: {res.stderr}")
            
            # 返回临时文件路径
            return '/tmp/tmp_program'
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess error: {e.stderr}")
    
    def run(self, lang: str, executable_path: str, time: int, mem: int, input: str) -> str:
        PR_SET_NO_NEW_PRIVS = 38
        PR_SET_SECCOMP = 22
        SECCOMP_MODE_STRICT = 1
        SECCOMP_MODE_FILTER = 2
        
        # 定义常量
        SCMP_ACT_KILL = 0x80000000  # If a rule is triggered, kill the process
        SCMP_ACT_ALLOW = 0x7fff0000
        SCMP_SYS = lambda x: x  # 模拟 SCMP_SYS 宏
        O_WRONLY = 0x01  # 打开文件时的写入权限
        O_RDWR = 0x02  # 打开文件时的读写权限
        
        # 定义系统调用号，按需增加
        syscalls_whitelist = [
            SCMP_SYS(0),  # access
            SCMP_SYS(1),  # arch_prctl
            SCMP_SYS(2),  # brk
            SCMP_SYS(3),  # clock_gettime
            SCMP_SYS(4),  # close
            SCMP_SYS(5),  # exit_group
            SCMP_SYS(6),  # faccessat
            SCMP_SYS(7),  # fstat
            SCMP_SYS(8),  # futex
            SCMP_SYS(9),  # getrandom
            SCMP_SYS(10),  # lseek
            SCMP_SYS(11),  # mmap
            SCMP_SYS(12),  # mprotect
            SCMP_SYS(13),  # munmap
            SCMP_SYS(14),  # newfstatat
            SCMP_SYS(15),  # pread64
            SCMP_SYS(16),  # prlimit64
            SCMP_SYS(17),  # read
            SCMP_SYS(18),  # readlink
            SCMP_SYS(19),  # readv
            SCMP_SYS(20),  # rseq
            SCMP_SYS(21),  # set_robust_list
            SCMP_SYS(22),  # set_tid_address
            SCMP_SYS(23),  # write
            SCMP_SYS(24)  # writev
        ]
        
        # 加载 libc 动态库
        libc = ctypes.CDLL('libc.so.6', use_errno=True)
        seccomp = ctypes.cdll.LoadLibrary("libseccomp.so.2")
        
        # 定义 seccomp 函数原型
        seccomp_init = seccomp.seccomp_init
        seccomp_init.restype = c_void_p
        seccomp_init.argtypes = [c_uint]
        
        seccomp_rule_add = seccomp.seccomp_rule_add
        seccomp_rule_add.restype = c_int
        seccomp_rule_add.argtypes = [c_void_p, c_uint, c_int, c_int, c_ulong]
        
        seccomp_load = seccomp.seccomp_load
        seccomp_load.restype = c_int
        seccomp_load.argtypes = [c_void_p]
        
        seccomp_release = seccomp.seccomp_release
        seccomp_release.restype = None
        seccomp_release.argtypes = [c_void_p]
        
        
        def set_limit():
            libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
            ctx = seccomp_init(SCMP_ACT_KILL)
            if not ctx:
                print("Failed to initialize seccomp context")
                return -1

            # 添加白名单中的系统调用
            for syscall in syscalls_whitelist:
                if seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscall, 0, 0) != 0:
                    print(f"Failed to add syscall {syscall}")
                    seccomp_release(ctx)
                    return -1

            # 根据 allow_write_file 设置文件写入权限
                # 禁止文件以写入模式打开
            if seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(2), 1, 0) != 0:  # open
                print("Failed to add restricted open rule")
                seccomp_release(ctx)
                return -1

            # 加载 Seccomp 筛选器
            if seccomp_load(ctx) != 0:
                print("Failed to load seccomp filter")
                seccomp_release(ctx)
                return -1

            # 释放过滤器上下文
            # seccomp_release(ctx)
        
        command = [executable_path]  # 直接传递为列表，避免shell注入风险
        
        # preexec_fn=set_limit,
        run_res = subprocess.run(
            command,
            input=input,
            capture_output=True,
            text=True
        )
        # print(run_res.stdout)
        if run_res.returncode != 0:
            if run_res.stderr:
                raise RuntimeError(run_res.stderr)
            elif run_res.returncode == 152:
                raise TimeoutError
            elif run_res.returncode == 137:
                raise MemoryError
        
        return run_res.stdout
    
    def clean(self, text: str) -> str:
        text = text.replace('\r', '')
        text_list = text.split('\n')
        clean_text = ''
        for line in text_list:
            line = line.rstrip()
            if line != '':
                if clean_text != '':
                    clean_text = clean_text + '\n' + line
                else:
                    clean_text = line
        return base64.b64encode(clean_text.encode('utf-8')).decode('utf-8')
    
    def judge(self, lang: str, executablePath: str, problem: Problem) -> list:
        result = []
        testCases: List[TestCase] = list(problem.testcases.all())
        for i in testCases:
            item = {
                "name": i.name,
                "status": None,
                "score": None,
            }
            try:
                res = self.run(lang, executablePath, i.timeLimit, i.memoryLimit, input=base64.b64decode(i.input).decode('utf-8'))
                print(res)
            except RuntimeError as e:
                item["status"] = "RE"
                item["score"] = 0
                item["error"] = str(e)
            except TimeoutError:
                item["status"] = "TLE"
                item['score'] = 0
            except MemoryError:
                item["status"] = "MLE"
                item['score'] = 0
            else:
                if self.clean(res) == i.output:
                    item["status"] = "AC"
                    item["score"] = i.score
                else:
                    item["status"] = "WA"
                    item['score'] = 0
            finally:
                result.append(item)
        return result
    
    def post(self, request):
        json_data = json.loads(request.body)
        lang: str = json_data['lang']
        code: str = base64.b64decode(json_data['code'].encode('utf-8')).decode('utf-8')
        # 构建并编译代码
        executable_path = self.build(lang, code)
        
        result = self.judge(lang, executable_path, Problem.objects.get(problem_id=json_data['problem_id']))
        
        return JsonResponse({"result": result})

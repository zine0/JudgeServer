from django.views.generic import View
from django.http import JsonResponse
from .models import *
import json
import base64


# Create your views here.

class SetTestcases(View):
    
    def clean(self,text:str) -> str:
        text:str = base64.b64decode(text).decode('utf-8')
        text = text.replace('\r','')
        text_list = text.split('\n')
        clean_text=''
        for line in text_list:
            line = line.rstrip()
            if line!='':
                if clean_text!='':
                    clean_text = clean_text + '\n' + line
                else:
                    clean_text = line
        return base64.b64encode(clean_text.encode('utf-8')).decode('utf-8')
            
    
    def post(self, request):
        response = {
            'result':'Ok',
            'message':'',
        }
        data = json.loads(request.body)
        problem, created = Problem.objects.get_or_create(problem_id=data['problem_id'])
        if not created:
            problem.testcases.all().delete()
        for item in data['testcases']:
            try:
                new_testcase = TestCase(
                    problem=problem,
                    timeLimit=item['timeLimit'],
                    memoryLimit=item['memoryLimit'],
                    score=item['score'],
                    name=item['name'],
                    input=self.clean(item['input']),
                    output=self.clean(item['output']),
                )
                new_testcase.save()
            except KeyError:
                response['resulr'] ='Err'
                response['message'] = 'KeyError'
        return JsonResponse(response)

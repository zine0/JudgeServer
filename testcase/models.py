from django.db import models

# Create your models here.settings.

class Problem(models.Model):
    problem_id = models.CharField(max_length=100)
    
    def __str__(self):
        return self.problem_id

class TestCase(models.Model):
    problem = models.ForeignKey(Problem,on_delete=models.CASCADE,related_name='testcases')
    timeLimit = models.IntegerField()
    memoryLimit = models.IntegerField()
    score = models.IntegerField(default=100)
    name = models.CharField(max_length=100)
    input = models.TextField()
    output = models.TextField()
    
    def __str__(self):
        return f'testcases of {self.problem.problem_id}: {self.name}'
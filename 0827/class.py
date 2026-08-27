
import sys
#sys.stdout.reconfigure(encoding='utf-8')
class person:
    def __init__(self,name):
        self.name=name

    def sayhello(self, to_name):
        print("안녕"+ to_name + "나는" + self.name )
wonie=person("워니")
michael=person("마이클")
jenny =person("제니")
wonie.sayhello("철수") 
michael.sayhello("영희")
jenny.sayhello("미지")     





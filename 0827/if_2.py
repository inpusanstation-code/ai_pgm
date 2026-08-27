#if ~elif ~else
i=0
while i<3 :
    text=input('알파벳입력:')
    if text.isupper():
        print('대문자')
    elif text.islower():
        print('소문자')
    else:
        print('대소문자 구분 불가능')
    i=i+1
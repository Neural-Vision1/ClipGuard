import time



def first():
    for i in range(10):
        
        yield i

def second(frames):
    for frame in frames:
        time.sleep(1)
        if frame%2==0:
            yield frame * frame

f = first()
s = second(f)
for i in s:
    print(i) 
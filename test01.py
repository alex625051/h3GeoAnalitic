NM=input().split(' ')
N=int(NM[0])
M=int(NM[1])
w=int(input())
#####
whites=[]
for i in range(0,w):
    oneOdd=input().split(' ')
    whites.append((int(oneOdd[0]),int(oneOdd[1])))
b=int(input())
blacks=[]
for i in range(0,b):
    oneOdd=input().split(' ')
    blacks.append((int(oneOdd[0]),int(oneOdd[1])))
step=input();

if step=='white':
    odds=whites;antioadds=blacks
else:
    odds=blacks;antioadds=whites

yes=False
for odd in odds:
    n=odd[0];m=odd[1]
    steps = []
    for n2 in [-1,+1]:
        for m2 in [-1,+1]:
            if not (n+n2,m+m2) in antioadds: continue
            steps.append((n2,m2))
    n2, m2 = 0, 0
    steps2=[]
    for i, step1 in enumerate(steps):
        n2=n+(step1[0]*2); m2=m+(step1[1]*2);
        if n2 < 1 or n2 > N: continue
        if m2 < 1 or m2 > M: continue
        if (n2, m2) in blacks or (n2, m2) in whites: continue
        yes=True
if yes:
    print("Yes")
else:
    print("No")



import sys

def makeGrid(c):
	grid = []
	for n in range(len(c)):
		row = []
		for m in range(len(c)):
			if m==n:
				row.append(2)
			else:
				row.append(0)
		grid.append(row)
	print grid
	return grid

f = open(sys.argv[1], 'r')
d = []
c = f.readline() 
for line in f:
	d.append(line)
print d
cons = c.split()
print cons
makeGrid(cons)





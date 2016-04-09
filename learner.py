"""
This is a computational learner for cophonologies. Given a set of constraints and data, this program seeks to create a
grammar of ranked constraints with as many pairs of constraints ranked as possible while still correctly predicting the
frequency of the input data.

It uses the expectation driven learning algorithm proposed in Jarosz 2015 to sample a pair of constraints and attempt
to update the grammar with a new ranking.

Arguments: a text file of constraints and data 
"""
import sys
import networkx as nx

#############################################################

def makeGrid(c):
	"""
	Given a list of n constraints, builds an n-by-n grid of pairwise constraint rankings
	Self-rankings are set automatically to 2; unranked pairs are set to 0
	1 indicates that the row constraint dominates the column constraint; -1 indicates the reverse
	"""
	grid = []
	c.insert(0,"X")
	grid.append(c)
	for n in range(1,len(c)):
		row = [c[n]]
		for m in range(1,len(c)):
			if m==n:
				row.append(2)
			else:
				row.append(0)
		grid.append(row)
	return grid

#####################################################################################################################

def makeData(d,n):
	"""
	Build a dictionary of tableaux
	Data: a dictionary of data : constraint violation pairs
	"""
	data = {}
	i = 0
	offset = 0
	while(i<n): #find all tableaux and then stop
		name = d[offset].strip() #underlying form
		rows = []
		m = 1
		while(len(d[offset+m].split()) > 1): #new candidate row
			rows.append(d[m+offset].split())
			if (offset+m+1 == len(d)): #end of list
				break
			m=m+1
		data[name] = rows
		offset = m+offset
		i=i+1
	return data

############################################################################################################

def makeFreq(f):
	"""
	Create a list representing form frequencies
	"""
	freqs = []
	for i in f:
		dpoint = i.split()
		for n in range(int(dpoint[1])):
			freqs.append(dpoint[0])
	return freqs

##################################################################################################

def buildGraph(g):
	root=nx.DiGraph()
	root.add_node("ROOT")
	print g
	for i in range(1,len(g)):
		added = 0
		for j in range(1,len(g)):
			print g[i][j]
			if (g[i][j]==2):
				if (added == 0):
					root.add_edge("ROOT",g[i][0])
				break
			else:
				if (g[i][j]==1):
					print "bigger"
					root.add_edge(g[i][0],g[0][j])
				else:
					if (g[i][j]==-1):
						print "smaller"
						added = 1
						root.add_edge(g[0][j],g[i][0])
	print root.edges()
	return root

##################################################################################################

tabs = open(sys.argv[1], 'r')#read in constraints and tableaux
f = open(sys.argv[2],'r')#read in frequency
d = []
c = tabs.readline()
n = tabs.readline()
n = n.split()
n = int(n[0]) #number of tableaux
for line in tabs:
	d.append(line) #create a list of data points
cons = c.split()#create a list of constraints
grid = makeGrid(cons) #create an initialized grid of pairwise constraint rankings
data = makeData(d, n) #create a dictionary of data
freqs = makeFreq(f)#create a list representing data frequencies
grid[3][1] = -1
grid[3][2] = -1
grid[4][2] = 1
grid[4][3] = 1 
graph = buildGraph(grid)



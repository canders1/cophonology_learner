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
import random

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
	"""
	Builds a directed acyclic graph representing the partial order from the pairwise constraint rankings
	"""
	root=nx.DiGraph() #directed acyclic graph
	root.add_node(("ROOT",-1))#add a dummy root node in case not all parts of the graph are connected
	for i in range(1,len(g)):#iterate through rows
		for j in range(1,len(g)):#iterate through columns
			if (g[i][j]==2):#if you've passed the diagonal, go on to the next row
				break
			else:
				if (g[i][j]==1):#bigger
					root.add_edge((g[i][0],i),(g[0][j],j))
				else:
					if (g[i][j]==-1):#smaller
						root.add_edge((g[0][j],j),(g[i][0],i))
	for i in range(1,len(g)):#if node isn't dominated by any other node, add to root
		if (root.predecessors((g[i][0],i)) == []):
			root.add_edge(("ROOT",-1),(g[i][0],i))
	return root

#################################################################################################

def sampleGrammar(g):
	"""
	Probabilistically samples a total order from the partial order graph
	Keeps track of nodes with no incoming edges (possible next constraints)
	Randomly chooses one, deletes from graph, adds children to accessible node list 
	if they have no other parents
	"""
	grammar = []
	n = len(g)
	roots = [("ROOT",-1)]#start at root node, which has no incoming edges
	for i in range(n):#add every node once
		random.shuffle(roots)#Shuffle nodes with no parents
		c = roots.pop()#Choose one
		childs = g.neighbors(c)#Get list of children of chosen node
		g.remove_node(c)#remove node from graph
		for child in childs:#iterate through children
			if (g.predecessors(child) == []):#if child has no other parent,
				roots.append(child)#add to list of nodes with no incoming edges
		grammar.append(c)#add chosen node to grammar
	grammar = grammar[1:len(grammar)]#remove dummy constraint from grammar
	return grammar

##################################################################################################

def winner(gram, tab):
	for j in range(len(gram)):
		if (len(tab)==1):
			break
		best = sys.maxint
		winner = ""
		losers = []
		for i in range(len(tab)):
			score = int(tab[i][gram[j][1]])
			if (score < best):
				if (best != sys.maxint):
					losers.append(winner)
				winner = tab[i]
				best = score
			if (score > best):
				losers.append(tab[i])
		for l in losers:
			tab.remove(l)
	return winner

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
graph = buildGraph(grid)#build a graph representing partial order from the pairwise constraint ranking grid
grammar = sampleGrammar(graph)#sample a total order from the partial order graph
win = winner(grammar,data["west"])
print data
print grammar
print win


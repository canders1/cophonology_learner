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
	current = ""
	for i in range(len(d)): #find all tableaux and then stop
		line = d[i].split()
		if (len(line)==1):#you've found a name; start a new entry in dictionary
			current = line[0]
			data[current] = []
		else:#you've found a candidate; update existing entry
			prev = data[current]
			prev.append(line)
			data[current] = prev
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

def winner(gram, t):
	"""
	Determines the winning candidate given a grammar and a tableau
	Non-deterministically selects a winner from winning candidate list in case of a tie
	"""
	tab = t[:]#copy list
	for j in range(len(gram)):#for each constraint
		if (len(tab)==1):#if you've narrowed it down to 1 candidate, that's the winner
			break
		best = sys.maxint
		winner = ""
		losers = []
		for i in range(len(tab)):#for each candidate
			score = int(tab[i][gram[j][1]])#find score
			if (score < best):#if it's better than the previous winner
				if (best != sys.maxint):
					losers.append(winner)#add previous winner to the loser list
				winner = tab[i]
				best = score
			if (score > best):#if it's worse than the winner
				losers.append(tab[i])#add to the loser list
		for l in losers:#remove all losers from the candidate list
			tab.remove(l)
	return winner

##################################################################################################

def genGrammars(n, grid):
	"""
	Returns a list of n numbers of randomly sampled grammars
	Calls buildGraph to make a graph representing the partial order from the pairwise constraint ranking grid
	Samples grammars from the partial order n times using sampleGrammar
	"""
	graph = buildGraph(grid)#build graph of partial order from the pairwise grid
	gramlist = []
	for i in range(n):
		g = graph.copy()
		newg = sampleGrammar(g) #sample a total order from the partial order graph
		gramlist.append(newg)
	return gramlist

##################################################################################################

def freqDict(n, gl, t, f):
	"""
	Finds the frequencies of output forms over n trials
	Randomly selects a grammar and (according to frequency) a tableau, then calls winner()
	Creates a dictionary of frequencies for each output
	"""
	fd = {} #dictionary with output form keys and frequency values
	for i in range(n):
		gram = gl[random.randrange(0, len(gl))]
		tab = t[f[random.randrange(0,len(f))]]
		w = winner(gram, tab)
		if (w[0] not in fd):
			fd[w[0]] = 1
		else:
			old = fd[w[0]]
			fd[w[0]] = old + 1
	return fd

##################################################################################################

tabs = open(sys.argv[1], 'r')#read in constraints and tableaux
f = open(sys.argv[2],'r')#read in test frequency
freq = open(sys.argv[3], 'r')
trials = int(sys.argv[4])
freqs = makeFreq(freq)
d = []
c = tabs.readline()
n = tabs.readline()
n = n.split()
n = int(n[0]) #number of tableaux
for line in tabs:
	d.append(line.strip()) #create a list of data points
cons = c.split()#create a list of constraints
grid = makeGrid(cons) #create an initialized grid of pairwise constraint rankings
data = makeData(d, n) #create a dictionary of data
ofreq = makeFreq(f)#create a list representing data frequencies
grid[3][1] = -1
grid[3][2] = -1
grid[4][2] = 1
grid[4][3] = 1 
glist = genGrammars(trials,grid)#get list of n grammars sampled from pairwise constraint ranking grid
fd = freqDict(trials, glist, data, freqs)
print fd



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
import copy

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
		if (root.has_node((g[i][0],i))==False):
			root.add_edge(("ROOT",-1),(g[i][0],i))
		else:
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
	print g.nodes()
	print g.edges()
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
	tab = copy.deepcopy(t)#copy list
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
	gramlist = []
	g = buildGraph(grid)
	for i in range(n):
		gr = g.copy()
		newg = sampleGrammar(gr) #sample a total order from the partial order graph
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
		gram = gl[random.randrange(0, len(gl))]#randomly select a grammar
		tab = t[f[random.randrange(0,len(f))]]#randomly select a tableau
		w = winner(gram, tab)#find winner
		if (w[0] not in fd):#add/update entry in frequency dictionary
			fd[w[0]] = 1
		else:
			old = fd[w[0]]
			fd[w[0]] = old + 1
	return fd

################################################################################################

def pickUpdate(grid):
	row = ""
	col = ""
	trys = []
	for i in range(len(grid)):
		for j in range(len(grid)):
			if (grid[i][j] == 0):
				trys.append((i,j))
	if(len(trys) == 0):
		print "all done!"
		return row, col
	else:
		trialcon = trys[random.randrange(0,len(trys))]#randomly pick a new constraint to add
		print trialcon
		row = trialcon[0]
		col = trialcon[1]
	return row, col

##################################################################################################

def estep(e, n, grid, data, ofreq, freqs):
	"""
	Perform the e-step: attempt to add a new ranking and recalculate
	"""
	newgrid = grid
	print grid
	print "here"
	row, col = pickUpdate(grid)
	if (row == ""):
		return newgrid
		print "All done!"
	bgrid, sgrid, test = bigsmall(row, col, grid)#generate grids with ranking added
	if (test == True):
		return newgrid
		print "Fail"
	else:
		blist = genGrammars(n,bgrid)#get list of n grammars sampled from both grids
		slist = genGrammars(n,sgrid)
		b_fd = freqDict(n, blist, data, freqs)#get frequency predictions from both grids
		s_fd = freqDict(n,slist,data,freqs)
		m_b = match(b_fd, ofreq, n)#get number of matches from both grids
		m_s = match(s_fd,ofreq,n)
		#This is where you have to make a choice about what to do next
		# Currently, I fix the ranking if the gap in matches is greater than e
		print m_b
		print m_s
		if ((m_b-m_s) > e):
			print "update!"
			newgrid = bgrid
		else:
			if ((m_s-m_b) > e):
				print "update!"
				newgrid = sgrid
		print "new"
		print newgrid
		return newgrid

#################################################################################################

def bigsmall(r,c,g):
	"""
	Generate two new grids with fixed rankings for constraints r and c. 
	"""
	b_grid = copy.deepcopy(g)
	s_grid = copy.deepcopy(g)
	biggraph, testb = closure(r,c,b_grid)#Build graph with new ranking of r above c
	smallgraph, tests = closure(c,r,s_grid)#Build graph with new ranking of c above r
	test = testb or tests
	new_b_grid = tabClosure(r,c,b_grid)
	new_s_grid = tabClosure(c,r,s_grid)
	return new_b_grid, new_s_grid, test

##################################################################################################

def closure(b,s,g):
	"""
	Attempts to add a new ranking
	If the ranking conflicts with existing rankings, set fail to true and return
	"""
	graph = buildGraph(g)#build graph of partial order from the pairwise grid
	bignode = (g[b][0],b)
	smallnode = (g[s][0],s)
	fail = False
	preds = graph.predecessors(bignode)
	succs = graph.successors(smallnode)
	for i in preds:
		for j in succs:
			if (graph.has_edge(j,i)):#conflicting ranking
				fail = True
				break
			else:
				graph.add_edge(i,j)#transitive closure
	return graph, fail

#################################################################################################

def tabClosure(b,s,t):
	preds = []
	succs = []
	for n in range(len(t)):
		print t[b][n]
		if (t[b][n] == 1):
			preds.append(n)
		if (t[s][n]==-1):
			succs.append(n)
	for pre in preds:
		print "updated!"
		t[pre][s] = 1
		t[s][pre] = -1
	for suc in succs:
		print "updated!"
		t[suc][b]=-1
		t[b][suc] =1
	t[b][s] = 1
	t[s][b] = -1
	return t

##################################################################################################

def match(fd, ofd, n):
	matches = 0
	scale = float(n)/float(ofd["TOTAl"])
	for key in fd:
		exp = float(ofd[key])*scale
		act = float(fd[key])
		m = min(act,exp)
		matches = matches + m
	return matches

##################################################################################################

def makefdict(f):
	"""
	Creates a dictionary of output frequencies
	"""
	freqs = {}
	total = 0
	for i in f:
		dpoint = i.split()
		freqs[dpoint[0]] = dpoint[1]
		total = total + int(dpoint[1])
	freqs["TOTAl"] = total
	return freqs

###############################################################################################

tabs = open(sys.argv[1], 'r')#read in constraints and tableaux
f = open(sys.argv[2],'r')#read in test frequencies
freq = open(sys.argv[3], 'r')#read in tableau frequencies
trials = int(sys.argv[4])#number of samplings
e = int(sys.argv[5])#size of gap in order to set a new ranking
freqs = makeFreq(freq)#make a list of tableau frequencies
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
ofreq = makefdict(f)#create a list of expected frequencies
oldgrid = estep(e, trials, grid, data, ofreq, freqs)
for j in range(50):
	newgrid = estep(e, trials, oldgrid, data, ofreq, freqs)
	oldgrid = newgrid
print oldgrid






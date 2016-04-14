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

def pickUpdate(n,grid,data,ofreq,freqs,prevf):
	"""
	Iterate through possible updates and return a grid updated with the best new constraint
	"""
	row = ""
	col = ""
	trys = []
	conlist = {}
	done = 0
	for i in range(len(grid)):#Iterate through constraint rankings
		for j in range(len(grid)):
			if (grid[i][j] == 0):#If the constraints haven't been ranked yet
				trys.append((i,j))
	if(len(trys) == 0):#If all constraints are ranked, return
		print "all done!"
		done = 1
		return grid, done, prevf
	else:
		random.shuffle(trys)#pick a random constraint ranking to try to add
		oldgrid = grid
		for i in range(len(trys)):
			newgrid, f, m = estep(n,oldgrid,data,ofreq,freqs,trys[i][0],trys[i][1])
			if (f > 0):#if constraint ranking would result in inconsistency
				print "not a can!"
			else:
				conlist[i] = (newgrid,m)
	best = ([],0)
	for entry in conlist:#find constraint ranking with most matches
		if (conlist[entry][1] > best[1]):
			best = (conlist[entry][0],conlist[entry][1])
	"""
	if (prevf>=best[1]):
		done = 1
		print "no change is better"
		return grid, done, prevf
	else:
	"""
	return best[0], done, best[1]

##################################################################################################

def estep(n, grid, data, ofreq, freqs,row,col):
	"""
	Perform the e-step: attempt to add a new ranking and recalculate
	"""
	newgrid = grid
	fail = 0
	matches = 0
	bgrid, sgrid, testb, tests = bigsmall(row, col, grid)#generate grids with ranking added
	if ((tests + testb) > 1):
		print "Both fail"
		fail = 1
		return newgrid, fail, 0
	else:
		if(testb>0):
			m_b = 0
			slist = genGrammars(n,sgrid)
			s_fd = freqDict(n,slist,data,freqs)
			m_s = match(s_fd,ofreq,n)
		else:
			if(tests>0):
				m_s = 0
				blist = genGrammars(n,bgrid)#get list of n grammars sampled
				b_fd = freqDict(n, blist, data, freqs)#get frequency prediction
				m_b = match(b_fd, ofreq, n)#get number of matches
			else:

				blist = genGrammars(n,bgrid)#get list of n grammars sampled from both grids
				slist = genGrammars(n,sgrid)
				b_fd = freqDict(n, blist, data, freqs)#get frequency predictions from both grids
				s_fd = freqDict(n,slist,data,freqs)
				m_b = match(b_fd, ofreq, n)#get number of matches from both grids
				m_s = match(s_fd,ofreq,n)
		#This is where you have to make a choice about what to do next
		# Currently, I fix the ranking if the gap in matches is greater than e

		if (m_b>m_s):
			newgrid = bgrid
			matches = m_b
		else:
			newgrid = sgrid
			matches = m_s
		return newgrid, fail, matches

#################################################################################################

def bigsmall(r,c,g):
	"""
	Generate two new grids with fixed rankings for constraints r and c. 
	"""
	testb = closure(r,c,copy.deepcopy(g))#Test whether ranking is possible
	tests = closure(c,r,copy.deepcopy(g))
	new_b_grid = tabClosure(r,c,g)
	new_s_grid = tabClosure(c,r,g)
	return new_b_grid, new_s_grid, testb, tests

##################################################################################################

def closure(b,s,g):
	"""
	Attempts to add a new ranking
	If the ranking conflicts with existing rankings, set fail to true and return
	"""
	graph = buildGraph(g)#build graph of partial order from the pairwise grid
	bignode = (g[b][0],b)
	smallnode = (g[s][0],s)
	fail = 0
	preds = graph.predecessors(bignode)
	succs = graph.successors(smallnode)
	preds.append(bignode)
	succs.append(smallnode)
	for i in preds:
		for j in succs:
			if (graph.has_edge(j,i) or (i[1]==j[1])):#conflicting ranking
				fail = 1
				break
			else:
				graph.add_edge(i,j)#transitive closure
	return fail

#################################################################################################

def tabClosure(b,s,t):
	"""
	Performs transitive closure on the tableau
	"""
	newt = copy.deepcopy(t)
	preds = [b]
	succs = [s]
	for n in range(0,len(t)):
		if (t[b][n] == -1):
			preds.append(n)
		if (t[s][n]==1):
			succs.append(n)
	for pre in preds:#predecessors of the b constraint also dominate the s constraint
		for suc in succs:#successors of the s constraint are also dominated by the b constraint
			newt[pre][suc] = 1
			newt[suc][pre] = -1
	return newt

##################################################################################################

def match(fd, ofd, n):
	"""
	Calculate matches
	"""
	matches = 0
	scale = float(n)/float(ofd["TOTAl"])#Scale matches based on size of input
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
l = int(sys.argv[6])#number of learning iterations
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
oldgrid = grid
prevf =0
for j in range(l):
	print j
	newgrid, done, m = pickUpdate(trials, oldgrid, data, ofreq, freqs, prevf)
	print newgrid
	print "Matches: " + str(m) + " out of " + str(trials)
	if (done ==1):
		print "done!"
		break
	else:
		oldgrid = newgrid
		prevf = m
print oldgrid
glist = genGrammars(trials,oldgrid)#get list of n grammars sampled from both grids
fpred = freqDict(trials, glist, data, freqs)#get frequency predictions from both grids
m = match(fpred, ofreq, trials)#get number of matches from both grids
print "Matches for final rankings: " + str(m) + " out of " + str(trials)






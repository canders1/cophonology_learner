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
	for n in range(1,len(c)):#don't change values in first row/column slot, they are constraint names
		row = [c[n]]
		for m in range(1,len(c)):
			if m==n:
				row.append(2)#initialize self-rankings to 2
			else:
				row.append(0)#initialize all other rankings to 0
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

def consistentUList(n,grid,data,ofreq):
	"""
	Iterate through possible updates, calls bigsmall to apply transitive closure, check if they are 
	consistent (contain a possible total order for each tableau that predicts every winner in the output), 
	and return a list of consistent updates
	"""
	row = ""
	col = ""
	trys = []
	conlist = []
	done = 0
	for i in range(len(grid)):#Iterate through constraint rankings
		for j in range(len(grid)):
			if (grid[i][j] == 0):#If the constraints haven't been ranked yet
				trys.append((i,j))
	if(len(trys) == 0):#If all constraints are ranked, return
		#print "all done!"
		done = 1
		return conlist, done
	else:
		random.shuffle(trys)#pick a random constraint ranking to try to add
		oldgrid = grid
		for i in range(len(trys)):
			bgrid, sgrid, testb, tests = bigsmall(trys[i][0],trys[i][1], grid)#generate grids with ranking added; apply transitive closure
			if (tests==0):#dominated ranking passes closure test
				conlist.append(sgrid)#add to consistent ranking list
			if (testb==0):#dominating ranking passes closure
				conlist.append(bgrid)#add to consistent ranking list
	winlist = []
	for c in conlist:
		TO = genGrammars(n, c)#sample total orders from partial order
		inconsist = consistent(TO,data,ofreq)#check consistency against output
		if(int(inconsist)==0):
			winlist.append(c)#add partial order that if consistent with output
	return winlist, done

##################################################################################################

def learn(grid,n,data,ofreqs,prevs):
	"""
	One generation of learning
	Calls consistentUList to generate a list of next rankings consistent with the output
	Figures out whether learning is done, needs to backtrack, or can add a new ranking
	Updates the backtrack list (prevs)
	"""
	newg = grid
	done = 0
	clist,d = consistentUList(n,grid,data,ofreqs)
	if(d==1):#If there are no unranked constraints left, quit
		done = 1
		return newg,prevs,done
	else:
		if(len(clist)==0):#If no consistent next rankings exist,
			if(len(prevs)==0):#And no backtrack possibilities exist, quit
				done = 1
				return newg,prevs,done
			else:#If there is a backtrack option, pick a random one and return
				#print "backtrack!"
				random.shuffle(prevs)
				newg = prevs[0]
				prevs.remove(newg)
				return newg,prevs,done
		else:
			random.shuffle(clist)
			prevs = clist[-5:-2]#update backtrack possibilities
			newg = clist[-1]#add new constraint ranking
			return newg,prevs,done

#################################################################################################

def bigsmall(r,c,g):
	"""
	Generate two new grids with fixed rankings for constraints r and c. 
	"""
	testb = closure(r,c,copy.deepcopy(g))#Test whether ranking is possible
	tests = closure(c,r,copy.deepcopy(g))
	new_b_grid = tabClosure(r,c,g)#rank row over column
	new_s_grid = tabClosure(c,r,g)#rank column over row
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
	preds = graph.predecessors(bignode)#get constraints ranked above dominating node
	succs = graph.successors(smallnode)#get constraints ranked below dominated node
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
			preds.append(n)#get predecessors of the dominating constraint
		if (t[s][n]==1):#get successors of the dominated constraint 
			succs.append(n)
	for pre in preds:#predecessors of the b constraint also dominate the s constraint
		for suc in succs:#successors of the s constraint are also dominated by the b constraint
			newt[pre][suc] = 1
			newt[suc][pre] = -1
	return newt

##################################################################################################

def consistent(TO,tableaux,output):
	"""
	For a given partial order (represented as a list of total orders),
	checks that for each tableau/winner pair in the output, there exists a partial order
	that predicts that winner.
	If the partial order is consistent with the output, returns 1; else returns 0
	"""
	inconsistent = 0
	for k in output.keys():
		found = 0
		if (isinstance(k, tuple)):#for each input-winner pair (ignore tableau count items):
			n = k[0]#name of tableau
			w = k[1]#winner
			if (output[k] > 0.0):#if winner is attested in the training data:
				tableau = tableaux[n]#look up tableau
				for o in TO:#search for a total order that picks that winner
					picked = winner(o,tableau)[0]
					if(picked==w):
						found = 1
						break
				if(found==0):#no total order predicting the winner is found, so constraint ranking is inconsistent
					inconsistent = 1
					return inconsistent
	return inconsistent

##################################################################################################

def makefdict(f):
	"""
	Creates a dictionary of output frequencies
	"""
	freqs = {}
	for i in f:
		dpoint = i.split()
		freqs[(dpoint[0],dpoint[1])] = float(dpoint[2])
		if (dpoint[0] not in freqs):
			freqs[dpoint[0]] = float(dpoint[2])
		else:
			newf = freqs[dpoint[0]] + float(dpoint[2])
			freqs[dpoint[0]] = newf
	return freqs

###############################################################################################

def main():
	tabs = open(sys.argv[1], 'r')#read in constraints and tableaux
	f = open(sys.argv[2],'r')#read in test frequencies
	trials = int(sys.argv[3])#number of samplings
	l = int(sys.argv[4])#number of learning iterations
	c = tabs.readline()#constraints
	n = tabs.readline()
	n = n.split()
	n = int(n[0]) #number of tableaux
	d = []
	for line in tabs:
		d.append(line.strip()) #create a list of data points
	cons = c.split()#create a list of constraints
	grid = makeGrid(cons) #create an initialized grid of pairwise constraint rankings
	data = makeData(d, n) #create a dictionary of data
	ofreq = makefdict(f)#create a list of expected frequencies
	oldgrid = grid
	prevs = []
	for i in range(l):#for l number of learning iterations
		newgrid,plist,d = learn(oldgrid,n,data,ofreq,prevs)#update with a consistent constraint ranking
		oldgrid = newgrid
		prevs = plist#backtrack list
		if(d==1):#all done, no more possible rankings to add
			break
	glist = genGrammars(l,oldgrid)
	grdict = {}
	for g in glist:#compile a list of total orders generated by the partial order
		if (str(g) not in grdict):
			grdict[str(g)] = "yes"
	return oldgrid, grdict.keys()



"""
This is a computational learner for cophonologies. Given a set of constraints and data, this program seeks to create a
grammar of ranked constraints with as many pairs of constraints ranked as possible while still correctly predicting the
frequency of the input data.

It uses the expectation driven learning algorithm proposed in Jarosz 2015 to sample a pair of constraints and attempt
to update the grammar with a new ranking.

Arguments: a text file of constraints and data 
"""
import sys

#############################################################

def makeGrid(c):
	"""
	Given a list of n constraints, builds an n-by-n grid of pairwise constraint rankings
	Self-rankings are set automatically to 2; unranked pairs are set to 0
	1 indicates that the row constraint dominates the column constraint; -1 indicates the reverse
	"""
	grid = []
	for n in range(len(c)):
		row = []
		for m in range(len(c)):
			if m==n:
				row.append(2)
			else:
				row.append(0)
		grid.append(row)
	return grid

#####################################################################################################################

def makeData(d):
	"""
	Given a list of n data, build a dictionary of data and a list representing data frequency
	Data: a dictionary of data : constraint violation pairs
	Dlist: a list with data points proportional to their frequency
	"""
	dlist = []
	data = {}
	for i in d:
		dpoint = i.split()
		data[dpoint[0]] = dpoint[2:len(dpoint)]
		for i in range(int(dpoint[1])):
			dlist.append(dpoint[0])
	return data, dlist

############################################################################################################

f = open(sys.argv[1], 'r')#read in constraints and data file
d = []
c = f.readline() 
for line in f:
	d.append(line) #create a list of data points
cons = c.split()#create a list of constraints
grid = makeGrid(cons) #create an initialized grid of pairwise constraint rankings
data, dlist = makeData(d) #create a dictionary of data and a list representing data frequencies




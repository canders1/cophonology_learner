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

def makeData(d,n):
	"""
	Build a dictionary of tableaux
	Data: a dictionary of data : constraint violation pairs
	"""
	data = {}
	i = 0
	
	while(i<=n):
		name = d[i]
		rows = []
		j = 1
		print j+i
		while(len(d[i+j].split())> 1):
			rows.append(d[i+j])
			j = j+1
		data[name] = rows
		i = i+j
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
print data



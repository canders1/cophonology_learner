import learner

gdict = {}
for i in range(1000):
	g, l = learner.main()
	if (str(g) not in gdict):
		gdict[str(g)] = 1
	else:
		oldc = gdict[str(g)]
		gdict[str(g)] = oldc+1
for i in gdict.keys():
	print "key: " + i
	print gdict[i]
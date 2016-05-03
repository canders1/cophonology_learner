This is a learner for cophonological approaches to variation. It adapts the Expectation Maximization algorithm in Jarosz 2015 to learn a partial order of constraints that is as consistent as possible with the input.

Run as follows:

python learner.py tableaux train n e

where:
	tableaux contains constraints and tableaus; 
	train contains the training input-winner pairs;
	n specifies the sampling size;
	e specifies the number of learning attempts

Example:

python learner.py td_tableaux.txt aave.txt 100000 100

import.py is a program that will run X number of trials of the learner, where X is a command-line argument given by the user.

It can be run as follows:

python import.py tableaux train n e m > tdults.txt

where e specifies the number of runs for the learner and the other command-line arguments are as explained above.

Example:

python import.py td_tableaux.txt aave.txt 100000 100 250

Gaja Jarosz. 2015. Expectation Driven Learning of Phonology. 
http://people.umass.edu/jarosz/edl_submitted.pdf
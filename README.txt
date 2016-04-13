This is a learner for cophonological approaches to variation. It adapts the Expectation Maximization algorithm in Jarosz 2015 to learn a partial order of constraints that is as consistent as possible with the input.

Run as follows:

python learner.py tableaus input frequencies n m e

where tableaus contains constraints and tableaus; input contains the input forms;
	  frequencies contains the frequency of each output; n specifies the sample size;
	  m specifies the threshold for adding a new constraint; and
	  e specifies the number of learning attempts

Example:

python learner.py td_tableaux.txt aave.txt td_freq.txt 1000 1 100


Gaja Jarosz. 2015. Expectation Driven Learning of Phonology. 
http://people.umass.edu/jarosz/edl_submitted.pdf
"""
Wrapper stuff to run PyCS on TDC data

We change the philosophy here: we make a clear separation between functions that draw lcs,
and functions that analyse them.

The goal is to create "once and for all" a huge amount of simulated curves, and then
run the optimizer on a limited number of simulated curves, randomly chosen.

The copied and simulated lcs are stored each into an individual pkl (one per lcs)
"""

import os, sys
import pycs
import est
import datetime
import numpy as np
from copy import copy
import glob


def createdir(estimate, path):
	
	dirpath = os.path.join(os.getcwd(),path)

	# 1) Create main directory
	if not os.path.isdir(dirpath):
		os.mkdir(dirpath)
		
	# 2) Create sub-directories
	subdirpath = os.path.join(dirpath,estimate.id)
	if not os.path.isdir(subdirpath):
		os.mkdir(subdirpath)	
	

def drawcopy(estimate, path, n=1, maxrandomshift = None, datadir=''):
	"""

	Draw n times one single copy of lcs (the ones your estimate is about) into the path directory.
	NEW: set can be the name of a COSMOGRAIL lens.
	
	@param estimates:	list of estimate objects, with id, td and tderr
	@param path:	where your copy will be written
	@param addmlfct:	If you want to add different microlensing to your obslcs
	@param n:	Number of time you will run drawobs (each run produce new copycurves)
	@param maxrandomshift:	Maximum range for the random time shift added to the copycurves
	"""

	copydir = os.path.join(os.getcwd(),path)

	if estimate.set in ['tdc0', 'tdc1']:
		lcspath = os.path.join(datadir,pycs.tdc.util.tdcfilepath(set=estimate.set, rung=estimate.rung, pair=estimate.pair))
		(lca, lcb) = pycs.tdc.util.read(lcspath, shortlabel=False)

	else:
		lcspath = os.path.join(datadir,pycs.tdc.util.tdcfilepath(set=estimate.set, rung=estimate.rung, pair=estimate.pair))
		(lca, lcb) = pycs.tdc.util.read(lcspath, pair=estimate.pair)

	# compute the vario analysis of these lcs
	if not (hasattr(lca, "vario") and hasattr(lcb, "vario")):
		lca.vario = pycs.tdc.vario.vario(lca, verbose=True)
		lcb.vario = pycs.tdc.vario.vario(lcb, verbose=True)
		print '---Vario Analysis Done---'

	ind=0
	while ind < n:

		# Reset ML and shifts (get them "as read" from scratch...)
		lca.magshift = 0.0
		lcb.magshift = 0.0	
		lca.timeshift = 0.0
		lcb.timeshift = 0.0

		lcs = [lca,lcb] 

		# Time shift around the initial value		
		tsr = np.max([3.0, estimate.tderr])

		if not maxrandomshift == None:
			if tsr >= maxrandomshift:
				tsr = maxrandomshift


		lcb.shifttime(estimate.td +float(np.random.uniform(low=-tsr, high=tsr, size=1)))


		# Now, we write that copycurve
		if not os.path.exists(os.path.join(copydir,estimate.id)):
			try:
				os.system('mkdir %s' % os.path.join(copydir,estimate.id))
				print ' \n ----- New copy/sim directory created: %s ' % os.path.join(copydir,estimate.id)

			except:
				print "I cannot create %s..." % os.path.join(copydir,estimate.id)
				print "going on..."

		find_max_ind = 'ls %s | wc -l' % os.path.join(copydir,estimate.id,'c*')
		next_copy_ind = 'c'+str(int(os.popen(find_max_ind).readline())).rjust(3,'0')+'.pkl'
		copypath = os.path.join(copydir,estimate.id,next_copy_ind)
		pycs.gen.util.writepickle(lcs,copypath)	
		ind += 1
	

	
def drawsim(estimate, path, sploptfct, n=1, maxrandomshift = None, datadir='') :
	"""

	Draw n times one single sim curves of lcs (the ones your esimate is about) into the path directory.
	
	@param estimates:	list of estimate objects, with id, td and tderr
	@param path:	where your copy will be written
	@param addmlfct:	If you want to add different microlensing to your obslcs
	@param n:	Number of time you will run drawsim (each run produce new simcurves)
	@param maxrandomshift:	Maximum range for the random "true" and "guessed" time shift added to the simcurves
	"""

	simdir = os.path.join(os.getcwd(),path)

	# get the model lightcurves
	if estimate.set in ['tdc0', 'tdc1']:
		lcspath = os.path.join(datadir,pycs.tdc.util.tdcfilepath(set=estimate.set, rung=estimate.rung, pair=estimate.pair))
		(lca, lcb) = pycs.tdc.util.read(lcspath, shortlabel=False)

	else:
		lcspath = os.path.join(datadir,pycs.tdc.util.tdcfilepath(set=estimate.set, rung=estimate.rung, pair=estimate.pair))
		(lca, lcb) = pycs.tdc.util.read(lcspath, pair = estimate.pair)
	ind=0

	# shift lcs as estimated by d3cs
	lcb.shifttime(estimate.td)

	# fit a spline on the data and save residuals
	sourcespline = sploptfct([lca, lcb])
	pycs.sim.draw.saveresiduals([lca, lcb], sourcespline)


	# define 'initial timeshifts', given by fitsourcespline
	timeshifta = lca.timeshift
	timeshiftb = lcb.timeshift

	#TODO : propagate knotstep attribute from varioanalysis to every copy, to avoid running varioanalysis on every simcurve...

	# now, draw n copycurves
	while ind < n:

		# set  a random "true" delay 
		truetsr = np.max([3.0, estimate.tderr])
		if not maxrandomshift == None:
			if truetsr >= maxrandomshift:
				truetsr = maxrandomshift

		lca.timeshift = timeshifta
		lcb.timeshift = timeshiftb + (float(np.random.uniform(low = -truetsr, high = truetsr, size=1))) 


		# Use the magic draw function to create simulated lcs
		lcssim = pycs.sim.draw.draw([lca, lcb], sourcespline, shotnoise="sigma")

		# add the vario attribues from original lcs (instead of recomputing it everytime...)
		lcssim[0].vario = lca.vario
		lcssim[1].vario = lcb.vario

		# Remove magshift, remove ML and add a new one :
		lcssim[0].magshift = 0.0
		lcssim[1].magshift = 0.0
		lcssim[0].rmml()
		lcssim[1].rmml()
		
		tsr = np.max([3.0, estimate.tderr])
		if not maxrandomshift == None:
			if tsr>=maxrandomshift:
				tsr=maxrandomshift

		# Set some wrong "initial delays" for the analysis, around the "true delays".
		lcssim[1].shifttime(float(np.random.uniform(low=-tsr, high=tsr, size=1)))

		# And write that simcurve
		if not os.path.exists(os.path.join(simdir,estimate.id)):
			try:
				os.system('mkdir %s' % os.path.join(simdir,estimate.id))
				print ' \n ----- New copy/sim directory created: %s ' % os.path.join(simdir,estimate.id)
			except:
				print "going on..."	

		find_max_ind = 'ls %s | wc -l' % os.path.join(simdir,estimate.id,'s*')
		next_sim_ind = 's'+str(int(os.popen(find_max_ind).readline())).rjust(3,'0')+'.pkl'
		simpath = os.path.join(simdir,estimate.id,next_sim_ind)

		pycs.gen.util.writepickle(lcssim,simpath)

		ind += 1	
			

def runcopy(estimate, path, optfct, n=1, clist=None):
	"""
	Run the optimizer (optfct) on n different copycurves
	Return the optimised timeshift and magnitude for each copycurves
	
	The n copycurves are chosen randomly in the copydir, unless you give a clist of numbers
	i.e. if clist = [1,3] runobs will run on c001.pkl and c003.pkl

	@param estimate: give me the estimate you want me to run on. (for the id)
	@param path: where the copycurves are written
	@param optfct: which optimisation function do you want me to use
	@param n: on how many copies do you want me to run the optimiser
	@param clist: ids of specific copycurves you want me to run on.
	"""
	
	index_list = copy(clist)
	copydir = os.path.join(os.getcwd(), path)

	# Check that there is enough copycurves in the copydir:
	find_max_ind = 'ls %s | wc -l' % os.path.join(copydir,estimate.id,'c*')
	number_of_files = int(os.popen(find_max_ind).readline())
	if number_of_files < n:
		print 'Not enough copyfiles in %s ' % os.path.join(copydir,estimate.id)		
		raise RuntimeError('not enough copycurves !!')

	if clist == None:
		mylist = np.arange(number_of_files)
		np.random.shuffle(mylist)
		index_list = mylist[:n] 	

	copytds  = []
	copymags = []
	optlcs = []
	splines = []

	for ind in index_list:
		try:
			copyfile = 'c%s' % str(ind).rjust(3,'0')+'.pkl'
			copypath = os.path.join(copydir,estimate.id,copyfile)
			lcs = pycs.gen.util.readpickle(copypath)
			spline = optfct(lcs)

			copytds.append(lcs[1].timeshift-lcs[0].timeshift)
			copymags.append(np.median(lcs[1].getmags() - lcs[1].mags) - np.median(lcs[0].getmags() - lcs[0].mags))
			optlcs.append(lcs)
			splines.append(spline)
		except:
			print 'Running on c%s.pkl' % str(ind).rjust(3,'0')+' failed !'
			#todo: how bad is this that I do not stop here when a run fails ?

	return (copytds, copymags, optlcs, splines)
		
		
def runsim(estimate, path, optfct, n=1, slist=None):		
	"""
	Run the optimizer (optfct) on n different simcurves
	Return the optimised timeshift and magnitude for each copycurves
	Also return the true delays of each simcurve
	
	The n simcurves are chosen randomly in the simdir, unless you give a slist of numbers
	i.e. if slist = [1,3] runobs will run on s001.pkl and s003.pkl

	@param estimate: give me the estimate you want me to run on. (for the id)
	@param path: where the simcurves are written
	@param optfct: which optimisation function do you want me to use
	@param n: on how many sims do you want me to run the optimiser
	@param slist: ids of specific simcurves you want me to run on.
	"""		

	index_list = copy(slist)
	simdir = os.path.join(os.getcwd(),path)		

	# Check that there is enough simcurves in the copydir:
	find_max_ind = 'ls %s | wc -l' % os.path.join(simdir,estimate.id,'s*')
	number_of_files = int(os.popen(find_max_ind).readline())
	if number_of_files < n:
		print 'Not enough simfiles in %s ' % os.path.join(simdir,estimate.id)
		raise RuntimeError('not enough simcurves !!')

	if slist == None:
		mylist = np.arange(number_of_files)
		np.random.shuffle(mylist)
		index_list = mylist[:n] 	

	simtds  = []
	simttds = []
	simmags = []
	optlcs = []
	inlcs = []
	splines = []

	# run the optimizer on each simcurve
	for ind in index_list:
		try:
			simfile = 's%s' % str(ind).rjust(3,'0')+'.pkl'
			simpath = os.path.join(simdir,estimate.id,simfile)
			lcs = pycs.gen.util.readpickle(simpath)
			inlcs.append([lcs[0].copy(), lcs[1].copy()])
			out = optfct(lcs)
			print 'TRUE DELAY: ',lcs[1].truetimeshift-lcs[0].truetimeshift
			print 'MEASURED DELAY: ',lcs[1].timeshift-lcs[0].timeshift

			simttds.append(lcs[1].truetimeshift-lcs[0].truetimeshift)
			simtds.append(lcs[1].timeshift-lcs[0].timeshift)
			simmags.append(np.median(lcs[1].getmags() - lcs[1].mags) - np.median(lcs[0].getmags() - lcs[0].mags))
			optlcs.append(lcs)
			splines.append(out)

		except:
			print 'Running on s%s.pkl' % str(ind).rjust(3,'0')+' failed'
			#todo: how bad is this that I do not stop here when a run fails ?
		
	return (simtds, simmags, simttds, inlcs, optlcs, splines)
		

def multirun(estimate, path, optfct, ncopy, nsim, clist=None, slist=None):

	"""
	Wrapper around runsim and runobs
	Run the optimizer ncopy and nsim times on the copy and sim
	Return the results in a list of estimates objects

	@param estimate: give me the estimate you want me to run on. (for the id)
	@param path: where the copycurves and simcurves are written
	@param optfct: which optimisation function do you want me to use
	@param ncopy: on how many copies do you want me to run the optimiser
	@param ncopy: on how many copies do you want me to run the optimiser
	@param slist: ids of specific copycurves you want me to run on.
	@param slist: ids of specific simcurves you want me to run on.
	"""

	copyout = runcopy(estimate, path, optfct = optfct, n=ncopy, clist=clist)
	pycs.gen.util.writepickle(copyout, os.path.join(path, "copyout_%s.pkl" % estimate.id))
	
	simout = runsim(estimate, path, optfct = optfct, n=nsim, slist=slist)
	pycs.gen.util.writepickle(simout, os.path.join(path, "simout_%s.pkl" % estimate.id))
	


def viz(estimate, path, datadir):
	"""
	Look at some light curves. change in place...
	"""
	#todo: redefine the purpose of this function
	
	copytds, copymags, copyoptlcs, copyoptsplines = pycs.gen.util.readpickle(os.path.join(path, "copyout_%s.pkl" % estimate.id))
	simtds, simmags, simttds, siminlcs, simoptlcs, simoptsplines = pycs.gen.util.readpickle(os.path.join(path, "simout_%s.pkl" % estimate.id))
	
	lcspath = os.path.join(datadir,pycs.tdc.util.tdcfilepath(set=estimate.set, rung=estimate.rung, pair=estimate.pair))

	if estimate.set in ['tdc0', 'tdc1']:
		origlcs = pycs.tdc.util.read(lcspath, shortlabel=False)
	else:
		origlcs = pycs.tdc.util.read(lcspath, pair=estimate.pair)

	for l in origlcs:  
		l.plotcolour = "black"
		
	# See the fit on the copies, and compare copies with originial curve:
	for (spline, lcs) in zip(copyoptsplines, copyoptlcs):
		pycs.gen.lc.display(lcs, [spline])

	# Compare the sims to the data
	for lcs in siminlcs:
		pycs.gen.lc.display(lcs + origlcs, figsize=(22, 10))

	# See the fit on the optimized sims:
	for (spline, lcs) in zip(simoptsplines, simoptlcs):
		pycs.gen.lc.display(lcs, [spline], figsize=(22, 10))

	
	
	
	
def summarize(estimate, path, makefig=False, skipdone=True):
	"""

	Create an Estimate instance of a pair, that contains the results from the PyCS optimisation.

	I will silently skip non-yet-ready pairs.
	If skipdone, I will silently skip those pairs that have already been summarized.

	@param estimate: give me the estimate you want me to run on. (for the id)
	@param path: where the copycurves and simcurves are written
	@param makefig: do you want me to create a summary figure
	@param skipdone: do you want me to skip the pairs that are already summarized
	"""

	resultpklpath = os.path.join(path,'%s.pkl' % estimate.id)
	if skipdone and os.path.exists(resultpklpath):
		return
	
	copyoutpklpath = os.path.join(path, "copyout_%s.pkl" % estimate.id)
	simoutpklpath = os.path.join(path, "simout_%s.pkl" % estimate.id)
	if not os.path.exists(copyoutpklpath):
		return
	if not os.path.exists(simoutpklpath):
		return

	# We start by creating Estimate objects that will contain our final result:
	method = 'PyCS'
	methodpar = 'PyCS'
	outest = pycs.tdc.est.Estimate(set=estimate.set, rung=estimate.rung, pair=estimate.pair,method=method, methodpar=methodpar)
	copytds, copymags, copyoptlcs, copyoptsplines = pycs.gen.util.readpickle(copyoutpklpath)
	simtds, simmags, simttds, siminlcs, simoptlcs, simoptsplines = pycs.gen.util.readpickle(simoutpklpath)

	# And we put the results in the output estimates, and save each individual output estimate
	print '='*30
	print outest.niceid
	outest.td = np.median(copytds)
	outest.tdvarint = np.std(copytds)
	print 'time delay:  ',outest.td
	syserr = np.fabs(np.mean([simtds[i]-simttds[i] for i in np.arange(len(simtds))]))
	ranerr = np.std([simtds[i]-simttds[i] for i in np.arange(len(simtds))])
	outest.tderr  = np.hypot(syserr, ranerr)
	outest.tdranerr = ranerr
	outest.tdsyserr = syserr
	print '   systematic error:  ',syserr
	print '       random error:  ',ranerr
	print '        total error:  ',outest.tderr		

	pycs.gen.util.writepickle(outest,resultpklpath)
	
	# We are done.
	if not makefig:	
		return
		
	# If we can, we make a fig
	try:
		import matplotlib.pyplot as plt
	except:
		print "can't import matplotlib"
		return

	mind3cs = estimate.td - estimate.tderr
	maxd3cs = estimate.td + estimate.tderr
	minrange = estimate.td - 2.0*estimate.tderr
	maxrange = estimate.td + 2.0*estimate.tderr
	
	plt.figure(figsize=(14, 5))
	
	plt.subplot(121)
	plt.hist(np.array(copytds), bins=30) # Do not specify range, so that we see outliers !
	plt.axvline(x=outest.td, linewidth=4, color='r')
	plt.axvline(x=mind3cs, linewidth=4, color='g')
	plt.axvline(x=maxd3cs, linewidth=4, color='g')
	plt.xlabel("copytds")
	plt.title(estimate.id)
	
	plt.subplot(122)
	plt.scatter(np.array(simttds), np.array(simtds)-np.array(simttds))
	plt.xlabel("simttds")
	plt.ylabel("simtds - simttds")
	#plt.xlim(minrange, maxrange) # No, do not use xlim here -- we want to see all points, if something goes wrong.
	plt.axhline(y=0, color='black')
	plt.axhline(y=outest.tderr, linewidth=4, color='red')  # The output error
	plt.axhline(y=-outest.tderr, linewidth=4, color='red')
	plt.axhline(y=estimate.tderr, linewidth=4, color='g')  # The input error
	plt.axhline(y=-estimate.tderr, linewidth=4, color='g')
	plt.axvline(x=mind3cs, linewidth=4, color='g')  # The input interval
	plt.axvline(x=maxd3cs, linewidth=4, color='g')
	plt.title("Uncertainty [d]: %.1f (%.1f ran, %.1f sys), varint: %.1f (%.0f %%)" % (outest.tderr, outest.tdranerr, outest.tdsyserr, outest.tdvarint, 100.0*outest.tdvarint/outest.tderr)  )
	
	plt.savefig(os.path.join(path, "copytds_%s.png" % estimate.id))


def collect(estimates, path):
	"""

	Gather the output estimates created by summarize and return them in a single tuple

	@param estimates: list of estimates you want me to collect
	@param path: where the summarized results are written
	"""
	
	print "You ask me to search for %i estimates" % (len(estimates))
	print "in %s" % (path)
	
	foundestimates = glob.glob(os.path.join(path, "*.pkl"))
	
	print "I have found %i files that look like estimates that are ready." % (len(foundestimates))
	
	outests = []
	for estimate in estimates:
		resultpklpath = os.path.join(path,'%s.pkl' % estimate.id)
		if resultpklpath in foundestimates:
			outest = pycs.gen.util.readpickle(resultpklpath, verbose=False)
			outests.append(outest)
	
	print "Collected %i estimates" % (len(outests))
	if len(outests) != len(estimates):
		print "WARNING, some estimates are still missing, I'm returning only %i estimates." % len(outests)
	else:
		print "OK! I found every estimate."
	
	return outests
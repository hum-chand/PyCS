import numpy as np
import pycs
import sys

def combiconf1(estimates):
	"""
	Give me a group of ests of the same pair, I return the combined confidence. Simple version
	"""
	
	(tdcset, rung, pair) = pycs.tdc.est.checkallsame(estimates)
	
	identity = estimates[0].id
	combiconfcode = 0 # the output value.
	
	idconfs = [(est.id,est.confidence) for est in estimates]
	
	
	### now we define criteria by criteria
	
	# doubtless, conflevels = 1 only
	if all(idconf[1]==1 for idconf in idconfs):
		combiconfcode = 1
	
	# plausible, conflevels = 1 or 2
	elif all(idconf[1]<=2 for idconf in idconfs):
		combiconfcode = 2
	
	# doubless+multimodal, need a manual check
	elif all(idconf[1]<=3 for idconf in idconfs) and 1 in (idconf[1] for idconf in idconfs):
		combiconfcode = 3
		
	# plausible+multimodal, no doubtless
	elif all(idconf[1]<=3 for idconf in idconfs):
		combiconfcode = 4
		
	# uninformative+doubless/plausible, need a manual check
	elif 1 in (idconf[1] for idconf in idconfs) or 2 in (idconf[1] for idconf in idconfs):
		combiconfcode = 5
	
	# uninformative and/or multimodal, to shoot
	elif 3 in (idconf[1] for idconf in idconfs) or 4 in (idconf[1] for idconf in idconfs):
		combiconfcode = 6
	
	else:
		raise RuntimeError("I didn't catch %s, should not happen !" % est.id)

	return {"code":combiconfcode, "set":tdcset, "rung":rung, "pair":pair}
	
	
def combiconf2(estimates):
	"""
	Updated version of combiconf1, now with accordance criterias between the estimates, and more weight given to Vivien/Malte estimates
	Return a new set of estimates "to be checked"
	
	"""	
	(tdcset, rung, pair) = pycs.tdc.est.checkallsame(estimates)
	
	identity = estimates[0].id
	combiconfcode = 0 # the output value.
	
	idconfs = [(est.id,est.confidence) for est in estimates]	
	
	hugefact = 0.4
	
	### First step, define "advanced" criterias

	
	# doubtless, conflevels = 1 only. They must agree between them (i.e td_i must be in td_j +- td_j_err for j!=i)
	if all(idconf[1]==1 for idconf in idconfs):
		for est in estimates:
			if combiconfcode == 11 or combiconfcode == 999:
				break
			subests = [subest for subest in estimates if subest.methodpar != est.methodpar]
			for subest in subests:
				if est.td > subest.td-subest.tderr and est.td < subest.td+subest.tderr:
					if min([subest.tderr/(subest.td+0.01) for subest in subests]) < hugefact:
						combiconfcode = 10 # then, estimates agree
						continue
					else:
						combiconfcode = 11 # they agree, but the errorbars are "huge"
						break
				else:
					combiconfcode = 999
					break														
								
		if combiconfcode == 999: 
			combiconfcode = 12 # they disagree	





	# plausible, conflevels = 1 or 2. They must agree between them (i.e td_i must be in td_j +- td_j_err for j!=i)
	elif all(idconf[1]<=2 for idconf in idconfs):
		for est in estimates:
			if combiconfcode == 21 or combiconfcode == 999:
				break
			subests = [subest for subest in estimates if subest.methodpar != est.methodpar]
			for subest in subests:
				if est.td > subest.td-subest.tderr and est.td < subest.td+subest.tderr:
					if min([subest.tderr/(subest.td+0.01) for subest in subests]) < hugefact:
						combiconfcode = 20 # then, estimates agree
						continue
					else:
						combiconfcode = 21 # they agree, but the errorbars are "huge"
						break
						
				else:
					combiconfcode = 999
					break
									
		if combiconfcode == 999: 
			combiconfcode = 22 # they disagree 
						


	
			
	# doubless+multimodal
	elif all(idconf[1]<=3 for idconf in idconfs) and 1 in (idconf[1] for idconf in idconfs):
		for est in estimates:
			if combiconfcode == 31 or combiconfcode == 999:
				break
			subests = [subest for subest in estimates if subest.methodpar != est.methodpar]
			for subest in subests:
				if est.td > subest.td-subest.tderr and est.td < subest.td+subest.tderr:
					if min([subest.tderr/(subest.td+0.01) for subest in subests]) < hugefact:
						combiconfcode = 30 # then, estimates agree
						continue
					else:
						combiconfcode = 31 # they agree, but the errorbars are "huge"
						break
				else:
					combiconfcode = 999
					break						
					
					
		if combiconfcode == 999:
		 
			if "mtewes" in (est.methodpar for est in estimates): 
				mest = [est for est in estimates if est.methodpar == 'mtewes'][0]
				vest = [est for est in estimates if est.methodpar == 'Vivien'][0]
				if vest.td > mest.td-mest.tderr and vest.td < mest.td+mest.tderr and mest.td > vest.td-vest.tderr and mest.td < vest.td+vest.tderr:
					combiconfcode = 32 # Malte and Vivien agree, someone else disagree
				else:
					combiconfcode = 33 # Malte and Vivien disagree		
			else:
				combiconfcode = 34 # No Malte, only Vivien, disagree with someone else	
			
										
	# plausible+multimodal, no doubtless
	elif all(idconf[1]<=3 for idconf in idconfs):
		for est in estimates:
			if combiconfcode == 41 or combiconfcode == 999:
				break
			subests = [subest for subest in estimates if subest.methodpar != est.methodpar]
			for subest in subests:
				if est.td > subest.td-subest.tderr and est.td < subest.td+subest.tderr:
					if min([subest.tderr/(subest.td+0.01) for subest in subests]) < hugefact:
						combiconfcode = 40 # then, estimates agree
						continue
					else:
						combiconfcode = 41 # they agree, but the errorbars are "huge"
						break
				else:
					combiconfcode = 999
					break			
					
		if combiconfcode == 999: 
			if "mtewes" in (est.methodpar for est in estimates): 
				mest = [est for est in estimates if est.methodpar == 'mtewes'][0]
				vest = [est for est in estimates if est.methodpar == 'Vivien'][0]
				if vest.td > mest.td-mest.tderr and vest.td < mest.td+mest.tderr and mest.td > vest.td-vest.tderr and mest.td < vest.td+vest.tderr:
					combiconfcode = 42 # Malte and Vivien agree, someone else disagree
				else:
					combiconfcode = 43 # Malte and Vivien disagree		
			else:
				combiconfcode = 44 # No Malte, only Vivien, disagree with someone else

				
	# uninformative+doubless/plausible
	elif 1 in (idconf[1] for idconf in idconfs) or 2 in (idconf[1] for idconf in idconfs):
		for est in estimates:
			if combiconfcode == 51 or combiconfcode == 999:
				break
			subests = [subest for subest in estimates if subest.methodpar != est.methodpar]
			for subest in subests:
				if est.td > subest.td-subest.tderr and est.td < subest.td+subest.tderr:
					if min([subest.tderr/(subest.td+0.01) for subest in subests]) < hugefact:
						combiconfcode = 50 # then, estimates agree
						continue
					else:
						combiconfcode = 51 # they agree, but the errorbars are "huge"
						break
				else:
					combiconfcode = 999
					break							
				

					
					
		if combiconfcode == 999:
		 	vest = [est for est in estimates if est.methodpar == 'Vivien'][0]
			if "mtewes" in (est.methodpar for est in estimates): 
				mest = [est for est in estimates if est.methodpar == 'mtewes'][0]
				if vest.td > mest.td-mest.tderr and vest.td < mest.td+mest.tderr and mest.td > vest.td-vest.tderr and mest.td < vest.td+vest.tderr:
					if mest.confidence < 4 or vest.confidence < 4: 
						combiconfcode = 51 # Malte or Vivien tagged plausible/doubtless and both agree
					else:
						combiconfcode = 52 # Malte and Vivien tagged uninformative (but agreed...) 
				else:
					if mest.confidence < 4 or vest.confidence < 4:
						combiconfcode = 53 # Malte or Vivien tagged plausible/doubtless, but both disagree 
					else:
						combiconfcode = 54 # Malte and Vivien tagged uninformative and disagree				
				
				
										
			else:
				if vest.confidence < 4:
					combiconfcode = 55 # ests disagree, but Vivien flagged plausible/doubtless.
				else:
					combiconfcode = 56 # ests disagree, Vivien flagged uninformative						
					

					
	# uninformative and/or multimodal
	elif 3 in (idconf[1] for idconf in idconfs) or 4 in (idconf[1] for idconf in idconfs):
		combiconfcode = 60					
										
	else:
		raise RuntimeError("WARNING -- I didn't catch %s, should not happen !" % est.id)

	if combiconfcode == 0:
		raise RuntimeError("WARNING -- combiconfcode for %s is 0, should not happen" % est.id)
		
	return {"code":combiconfcode, "set":tdcset, "rung":rung, "pair":pair}					
					
					
					
					
					
					
					
													

	

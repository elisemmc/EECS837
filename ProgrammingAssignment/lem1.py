import os.path
import numpy
import copy

class conceptualVariable:
	def __init__(self, name, array):
		self.name = name
		self.array = array

	def printVar(self):
		print self.name + ' ' + str(self.array)

class globalCovering:
	def __init__(self, name, globalCovering, cases):
		self.name = name
		self.globalCovering = globalCovering
		self.cases = cases

class ruleComponent:
	def __init__(self, name, value):
		self.name = name
		self.value = value
	
	def __str__(self):
		return '(' + str(self.name) + ', ' + str(self.value) + ')'

class rule:
	def __init__(self, attributes, decision):
		self.attributes = attributes
		self.decision = decision
	
	def __str__(self):
		out = ''
		for i, v in enumerate(self.attributes):
			out += str (v)
			if i < ( len(self.attributes)-1):
				out += ' & '
		out += ' -> '
		out += str(self.decision)
		return out

class ruleSet:
	def __init__(self, globalCoverings, array, attributeNames):
		self.ruleSet = []
		self.globalCoverings = globalCoverings
		self.array = array
		self.attributeNames = attributeNames

	def generateRules(self):
		# for gc in self.globalCoverings:
		# 	print str(gc.name) + ' : ' + str(gc.globalCovering) + ' : ' + str(gc.cases)

		for i, gc in enumerate(self.globalCoverings):
			for j in gc.cases:
				attributes = [ ruleComponent(self.attributeNames[index], self.array[j,index]) for index in gc.globalCovering ]
				decision = ruleComponent(self.attributeNames[-1], gc.name)
				newRule = rule(attributes, decision)

				indexList = range(len(newRule.attributes))
				for index, a in enumerate(newRule.attributes):
					tempList = copy.copy(indexList)
					tempList.remove(index)
					tempRule = rule( numpy.array(newRule.attributes)[[tempList]], newRule.decision)
					if set(self.matchRule(tempRule)) <= set(gc.cases):
						indexList.remove(index)

				finalRule = rule( numpy.array(newRule.attributes)[[indexList]], newRule.decision )
				self.ruleSet.append(finalRule)

		out = numpy.unique(numpy.array([str(r) for r in self.ruleSet]))
		return out
	
	def matchRule(self, rule):
		matchingCases = []
		for i, case in enumerate(self.array):
			if all( [ case[self.attributeNames.tolist().index(a.name)] == a.value for a in rule.attributes ] ):
				matchingCases.append(i)		
		return matchingCases

class lem1:
	def __init__(self):
		self.filename = ''
		pass

	def getDataFile(self):
		file_not_found = True

		while file_not_found:
			filename = raw_input('Enter path for data file: ')

			if os.path.exists(filename):
				file_not_found = False
			else:
				print 'Error'

		self.filename = filename
		file = open(filename, 'r')
		return file

	def parseFile(self, file):
		array = [ self.parseLine(line) for line in file if self.parseLine(line) is not None ]
		return (numpy.array(array[0]), numpy.array(array[1::]))

	def parseLine(self, line):
		#check for comments
		if '!' in line:
			line = line.split('!')[0]

		#remove all leading and trailing whitespace
		line = line.strip()

		#split on whitespace
		array = line.split()

		#check for special lines
		if len(array) == 0:
			return None
		elif array[0] == '<' and array[-1] == '>':
			return None
		elif array[0] == '[' and array[-1] == ']':
			return array[1:-1]
		else:
			return array

	def isSymbolic(self, line):
		if all( self.testCast(item) for item in line ):
			return False
		else:
			return True

	def testCast(self, item):
		try:
			float(item)
			return True
		except ValueError:
			return False

	def discretize(self, array):
		output = numpy.empty(array.shape, dtype=object)
		for i in range(array.shape[1]):
			output[:,i] = self.discretizeLine(array[:,i])
		return output

	def discretizeLine(self, line):
		if not self.isSymbolic(line):
			numLine = line.astype(float)
			sortedVals = numpy.unique(numLine)

			cutPoints = [ round(sortedVals[0],3) ]
			cutPoints += [ round((sortedVals[i]+sortedVals[i+1] )/2, 3) for i in range(len(sortedVals)-1) ]
			cutPoints += [ round(sortedVals[-1], 3) ]

			return [ self.discretizeElement(item, cutPoints) for item in numLine ]
		else:
			return line

	def discretizeElement(self, item, cutPoints):
		for i in range(len(cutPoints)-1):
			if item <= cutPoints[i+1]:
				return str(cutPoints[i]) + '..' + str(cutPoints[i+1])

	def concatLine(self, line):
		output = ''
		for i in line:
			output = str(output) + str(i) + ' '
		return output

	def getStar(self, array):
		cases = array

		if(len(array.shape) > 1):
			cases = [ self.concatLine(array[i,:]) for i in range(array.shape[0]) ]

		values = numpy.unique( cases )
		return [ [ i for i in range(len(cases)) if cases[i] == v ] for v in values ]

	def getConceptualVariables(self, decisions):
		uniqueDecisions = numpy.unique(decisions)
		conceptualVariables = [ conceptualVariable( d, numpy.array([ elem == d for elem in decisions ]) ) for d in uniqueDecisions ]
		return conceptualVariables

	def leqArray(self, d, a):
		return all( any([ (set(d_elem) <= set(a_elem)) for a_elem in a ]) for d_elem in d )

	def upperApproximation(self, conceptStar, aStar):
		approx = []
		for c in conceptStar:
			for a in aStar:
				if c in a:
					approx = approx + a
		return numpy.unique(approx)
	
	def lowerApproximation(self, conceptStar, aStar):
		approx = []
		for a in aStar:
			if set(a) <= set(conceptStar) :
				approx = approx + a
		return numpy.unique(approx)

	def singleGlobalCovering(self, array, conceptualVariableArray):
		cStar = self.getStar(conceptualVariableArray)
		dStar = self.getStar(array)
		R = []

		numCols = array.shape[1]
		indexList = range(numCols)
		if self.leqArray(dStar, cStar):
			for i in range(numCols):
				tempList = copy.copy(indexList)
				tempList.remove(i)
				dStar = self.getStar(array[:,tempList])
				if self.leqArray(dStar, cStar):
					indexList = tempList
			R = array[:, indexList]
		return indexList

	def writeToFile(self, file_ext, rules, consistent=False):
		filename = self.filename.rsplit('.',1)[0] + file_ext
		if os.path.exists(filename):
			os.remove(filename)
	
		file = open(filename, 'w')

		if consistent:
			file.write('! Possible rule set is not shown since it is identical with the certain rule set')
			return

		for r in rules:
			file.write(r + '\n')

		return

	def run(self):
		file = self.getDataFile()

		(attributeNames, cases) = self.parseFile(file)
		attributes = cases[:,0:-1]
		decisions = cases[:,-1]
		# print '\nInput attribute names:\n' + str(attributeNames)
		# print '\nInput cases:\n' + str(cases)
		# print '\nInput attributes:\n' + str(attributes)
		# print '\nInput decisions:\n' + str(decisions)

		discretizedAttributes = self.discretize(attributes)
		# print '\nDiscretized data:\n' + str(discretizedAttributes)

		#get A star by filtering the decisions by concept
		aStar = self.getStar(decisions)
		# print '\nA*:\n' + str(aStar)

		dStar = self.getStar(attributes)
		# print '\n{d}*:\n' + str(dStar)

		conceptualVariables = self.getConceptualVariables(decisions)
		# print '\nConceptual variables:\n' + str([(c.name, c.array) for c in conceptualVariables])

		# print '\n{d}* <= A*:\n' + str(self.leqArray(dStar, aStar)) + '\n'

		if self.leqArray(dStar, aStar):
			singleGlobalCoverings = [ 
				globalCovering(
					c.name, 
					self.singleGlobalCovering(discretizedAttributes, c.array),
					[i for i, x in enumerate(c.array) if x]
				) 
				for c in conceptualVariables 
			]

			rules = ruleSet(singleGlobalCoverings, discretizedAttributes, attributeNames)
			strRules = rules.generateRules()

			self.writeToFile('.certain.r', strRules)
			self.writeToFile('.possible.r', strRules, True)

		else:
			conceptTrue = [ [i for i, x in enumerate(c.array) if x] for c in conceptualVariables ]
			lowerApproximations = [ self.lowerApproximation(c, dStar) for c in conceptTrue ]
			upperApproximations = [ self.upperApproximation(c, dStar) for c in conceptTrue ]

			lowerConceptualArrays = [ [ c in la for c in range(len(decisions))] for la in lowerApproximations ]
			upperConceptualArrays = [ [ c in ua for c in range(len(decisions))] for ua in upperApproximations ]

			lowerSingleGlobalCoverings = [
				globalCovering(
					c.name,
					self.singleGlobalCovering(discretizedAttributes, numpy.array(lowerConceptualArrays[i])),
					lowerApproximations[i]
				)
				for i, c in enumerate(conceptualVariables)
			]

			upperSingleGlobalCoverings = [
				globalCovering(
					c.name,
					self.singleGlobalCovering(discretizedAttributes, numpy.array(upperConceptualArrays[i])),
					upperApproximations[i]
				)
				for i, c in enumerate(conceptualVariables)
			]

			certainRules = ruleSet(lowerSingleGlobalCoverings, discretizedAttributes, attributeNames)
			strCertainRules = certainRules.generateRules()

			self.writeToFile('.certain.r', strCertainRules)

			possibleRules = ruleSet(upperSingleGlobalCoverings, discretizedAttributes, attributeNames)
			strPossibleRules = possibleRules.generateRules()

			self.writeToFile('.possible.r', strPossibleRules)

if __name__ == "__main__":
	lem1 = lem1()
	lem1.run()
    
#!/usr/bin/env python3
# scripted by Matthew Prins, June-October 2025
'''This script performs the statistical analysis for a study examining 
   the impact of 1:1 digital device access on academic growth in mathematics and 
   English Language Arts during the COVID-19 pandemic'''

# import relevant Python libraries
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import seaborn as sns
import matplotlib.pyplot as plt
import pingouin as pg

# import data importing/processing function scripted for this ARP
import dataImportProcessingARP

# save processed data as stateDatasets
stateDatasets = dataImportProcessingARP.dataFinal()
print("data processed and imported\n-----\n")

# iterate through states
dfFiltered = {}
for state, testData in stateDatasets.items():
	for subject in ['MATH', 'ENG']:
		
		print("\n-------")
		print(state, subject, "t test:\n")
		print("n:", len(testData))
		
		# filter data for state and print n
		filteredData = [row for row in testData 
			if '3_' + subject + '_NUMBER_STUDENTS' in row
			or '5_' + subject + '_NUMBER_STUDENTS' in row
			or '3_' + subject + '_PASS' in row
			or '5_' + subject + '_PASS' in row
		]
		
		print("n, any state data:", len(filteredData))
		
		filteredData = [row for row in filteredData	
			if subject + '_ZSCORE_CHANGE' in row
			and 'RATIO_DEVICES_TO_ENROLLMENT' in row]
	
		print("n, all state data:", len(filteredData))

		filteredData = [row for row in filteredData
			if row.get('SCH_STATUS_SPED') == 'No'
			and row.get('SCH_STATUS_MAGNET') == 'No'
			and row.get('SCH_STATUS_CHARTER') == 'No'
			and row.get('SCH_STATUS_ALT') == 'No'
		]																																																																																																																																																																																		
		
		print("n, no charter etc.:", len(filteredData))
		
		filteredData = [row for row in filteredData
			if row.get('SCH_DIND_INSTRUCTIONTYPE') == 'A'
			or row.get('SCH_DIND_INSTRUCTIONTYPE') == 'C'
			or row.get('SCH_DIND_INSTRUCTIONTYPE') == 'D'
		]
		
		print("n, excluding virtual schools:", len(filteredData))
		
		filteredData = [row for row in filteredData 
			if row['3_' + subject + '_NUMBER_STUDENTS'] >= 20
			and row['5_' + subject + '_NUMBER_STUDENTS'] >= 20
		]
		
		print("n, >=20 students:", len(filteredData))		
		
		filteredData = [row for row in filteredData 
			if .75*row['3_' + subject + '_NUMBER_STUDENTS'] < row['5_' + subject + '_NUMBER_STUDENTS'] < 1.25*row['3_' + subject + '_NUMBER_STUDENTS']
		]
		
		print("n, 75%-125%:", len(filteredData), "\n")	

		# create database of schools not 1:1
		not1to1Data = [row[subject + '_ZSCORE_CHANGE'] for row in filteredData
			if row['RATIO_DEVICES_TO_ENROLLMENT'] <= .5
		]
		
		# create database of schools that are 1:1
		yes1to1Data = [row[subject + '_ZSCORE_CHANGE'] for row in filteredData
			if row['RATIO_DEVICES_TO_ENROLLMENT'] >= .90
		]
		
		# perform and print t test
		result = pg.ttest(np.array(not1to1Data), np.array(yes1to1Data), paired=False, correction='auto', alternative='two-sided')
		print(result, "\n")

		# calculate/print sample sizes, means, and SDs for 1:1/non-1:1
		n1 = len(not1to1Data)
		n2 = len(yes1to1Data)
		mean1 = np.mean(not1to1Data)
		mean2 = np.mean(yes1to1Data)
		sd1 = np.std(not1to1Data, ddof=1)
		sd2 = np.std(yes1to1Data, ddof=1)
		
		print(f"Not 1:1 Access: n={n1}, M={mean1:.3f}, SD={sd1:.3f}")
		print(f"1:1 Access:     n={n2}, M={mean2:.3f}, SD={sd2:.3f}")
		print(f"Mean Difference: {mean2-mean1:.3f}")
		
		# if state is All, save database in dfFiltered[subject] for additional analysis
		if state == "All":
				
			dfFiltered[subject] = pd.DataFrame(filteredData)
			
			# add necessary demographic/1:1 columns
			dfFiltered[subject]['OneToOne'] = dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'].apply(
				lambda x: 1 if x is not None and x >= 0.90
					else 0 if x is not None and x <= 0.5 
					else None
				)
			dfFiltered[subject]['pctBlack'] = dfFiltered[subject]['TOTAL_ENROLLMENT_BLACK'] / dfFiltered[subject]['TOTAL_ENROLLMENT']
			dfFiltered[subject]['pctHispanic'] = dfFiltered[subject]['TOTAL_ENROLLMENT_HISPANIC'] / dfFiltered[subject]['TOTAL_ENROLLMENT']

	# additional statistical tests/charts for all states
	if state == "All":
		# run statistical tests on specific attributes
		for test in ['Descriptive Characteristics', 'Multiple Linear Regression', 'RATIO_DEVICES_TO_ENROLLMENT',
					'TITLE1ELIG', "3_ENG_ZSCORE", "3_MATH_ZSCORE", "pctBlack", "pctHispanic",
					"DISTRICT_POVERTY_PERCENTAGE", "Alternate Thresholds", "Hierarchical Linear Model"]:
			for subject in ['MATH', 'ENG']:
				# skip 3_MATH_ZSCORE with ENG and 3_ENG_ZSCORE with MATH
				if test == '3_MATH_ZSCORE' and subject == 'ENG':
					continue
				if test == '3_ENG_ZSCORE' and subject == 'MATH':
					continue
				
				if test == "Descriptive Characteristics":
					# printing various descriptive characteristics for 1:1 and non-1:1
					print(f"\n{subject} descriptive characteristics:\n")
					for label, value in [("One To One", 1), ("Not One To One", 0)]:
						baselineData = dfFiltered[subject][dfFiltered[subject]['OneToOne'] == value]
						print(f"{label}:")
						print(f"n: {len(baselineData)}")
						print(f"mean pctBlack: {baselineData['pctBlack'].mean(skipna=True)}")
						print(f"mean pctHispanic: {baselineData['pctHispanic'].mean(skipna=True)}")
						print(f"fifth-grade {subject} test takers: {baselineData[f'5_{subject}_NUMBER_STUDENTS'].mean(skipna=True)}")
						print(f"third-grade {subject} z score: {baselineData[f'3_{subject}_ZSCORE'].mean(skipna=True)}")
						print(f"fifth-grade {subject} z score: {baselineData[f'5_{subject}_ZSCORE'].mean(skipna=True)}")
						print(f"{subject} z score change: {baselineData[f'{subject}_ZSCORE_CHANGE'].mean(skipna=True)}")
						print(f"mean district poverty percentage: {baselineData['DISTRICT_POVERTY_PERCENTAGE'].mean(skipna=True)}")
						print(f"percentage Title I elig.: {baselineData['TITLE1ELIG'].mean(skipna=True)}")
						print()
						
				# run multiple linear regression
				elif test == "Multiple Linear Regression":
					
					# filter data
					dfTesting = dfFiltered[subject][
						dfFiltered[subject]['OneToOne'].notna() &
						dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notna() &
						dfFiltered[subject]['pctBlack'].notna() &
						dfFiltered[subject]['pctHispanic'].notna() &
						dfFiltered[subject]['DISTRICT_POVERTY_PERCENTAGE'].notna()
					]
					
					# create OLS model and print summary results
					formula = f"""{subject}_ZSCORE_CHANGE ~ C(OneToOne) + pctBlack + pctHispanic + DISTRICT_POVERTY_PERCENTAGE + Q("3_{subject}_ZSCORE")"""
					model = smf.ols(formula, data=dfTesting).fit()
					
					print("\n-------")
					print(f"\nMultiple linear regression for {subject}_ZSCORE_CHANGE:\n")
					print(model.summary(), "\n")
					
				# linear regression on all schools, including ones with ratios between 1:1 and non-1:1	
				elif test == "RATIO_DEVICES_TO_ENROLLMENT":
					
					# filter data
					dfTesting = dfFiltered[subject][
						dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'].notna() &
						dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notna()
					]
					
					# create OLS model and print summary results
					formula = f'Q("{subject}_ZSCORE_CHANGE") ~ Q("RATIO_DEVICES_TO_ENROLLMENT")'
					model = smf.ols(formula, data=dfTesting).fit()
					
					print("\n-------")
					print(f"Linear regression for the effect of RATIO_DEVICES_TO_ENROLLMENT on {subject}_ZSCORE_CHANGE:\n")
					print(model.summary(), '\n')
					
					# additional linear regression on schools where RATIO_DEVICES_TO_ENROLLMENT <= .5
					# filter data
					dfTesting = dfFiltered[subject][
						dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'].notna() &
						(dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'] <= 0.5) &
						dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notna()
					]
					
					# create OLS model and print summary results
					formula = f'Q("{subject}_ZSCORE_CHANGE") ~ Q("RATIO_DEVICES_TO_ENROLLMENT")'
					model = smf.ols(formula, data=dfTesting).fit()
					
					print("\n-------")
					print(f"Linear regression for the effect of RATIO_DEVICES_TO_ENROLLMENT on {subject}_ZSCORE_CHANGE, only on schools where RATIO_DEVICES_TO_ENROLLMENT <= .5:\n")
					print(model.summary(), '\n')
				
				# run t-tests with various threshold combinations
				elif test == "Alternate Thresholds":
					
					print("\n-------")
					print(f"\nAlternate Threshold Analysis for {subject}:")
					
					# define threshold combos
					thresholds = [(0.4, 0.85), (0.4, 0.9), (0.4, 0.95), (0.5, 0.85), (0.5, 0.9), (0.5, 0.95), (0.6, 0.85), (0.6, 0.9), (0.6, 0.95)]
					
					for non1to1Threshold, yes1to1Threshold in thresholds:
						
						# filter at current threshold
						not1to1DataAlt = dfFiltered[subject][dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'] <= non1to1Threshold][subject + '_ZSCORE_CHANGE'].dropna().values
							
						yes1to1DataAlt = dfFiltered[subject][dfFiltered[subject]['RATIO_DEVICES_TO_ENROLLMENT'] >= yes1to1Threshold][subject + '_ZSCORE_CHANGE'].dropna().values
						
						# perform and print t test
						result = pg.ttest(np.array(not1to1DataAlt), np.array(yes1to1DataAlt), paired=False, correction='auto', alternative='two-sided')
						print(f"\n-------\nNon-1:1: <= {non1to1Threshold}, 1:1: >= {yes1to1Threshold}\n")
						print(result, "\n")
						
						# calculate/print sample sizes, means, and SDs for 1:1/non-1:1
						n1 = len(not1to1DataAlt)
						n2 = len(yes1to1DataAlt)
						mean1 = np.mean(not1to1DataAlt)
						mean2 = np.mean(yes1to1DataAlt)
						sd1 = np.std(not1to1DataAlt, ddof=1)
						sd2 = np.std(yes1to1DataAlt, ddof=1)
							
						print(f"Not 1:1 Access: n={n1}, M={mean1:.3f}, SD={sd1:.3f}")
						print(f"1:1 Access: n={n2}, M={mean2:.3f}, SD={sd2:.3f}")
						print(f"Mean Difference: {mean2-mean1:.3f}")	
				
				# run HLM
				elif test == "Hierarchical Linear Model":
					
					# filter data
					dfTesting = dfFiltered[subject][
						dfFiltered[subject]['OneToOne'].notna() &
						dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notna() &
						dfFiltered[subject]['pctBlack'].notna() &
						dfFiltered[subject]['pctHispanic'].notna() &
						dfFiltered[subject]['DISTRICT_POVERTY_PERCENTAGE'].notna() &
						dfFiltered[subject][f'3_{subject}_ZSCORE'].notna() &
						dfFiltered[subject]['LEA_STATE'].notna()
					]
					
					# create HLM/Mixed LM model and print summary results
					formula = f'Q("{subject}_ZSCORE_CHANGE") ~ OneToOne + pctBlack + pctHispanic + DISTRICT_POVERTY_PERCENTAGE + Q("3_{subject}_ZSCORE")'
					model = smf.mixedlm(formula, data=dfTesting, groups=dfTesting['LEA_STATE'], re_formula="1").fit(reml=True)
					
					print("\n-------")
					print(f"HLM Random Intercept for {subject}_ZSCORE_CHANGE:\n")
					print(model.summary(), '\n')
					
					# calculate random/residual and print results
					tau00  = float(model.cov_re.iloc[0, 0])
					sigma2 = float(model.scale)
					icc    = tau00 / (tau00 + sigma2)

					print("\nRandom/Residual:")
					print(f"  State intercept variance (tau_00): {tau00:.3f}")
					print(f"  Residual variance (sigma^2):       {sigma2:.3f}")
					print(f"  ICC (rho):                         {icc:.3f}\n")
					
				else:
					
					# for all other tests, use the test name to filter data
					dfTesting = dfFiltered[subject][
						dfFiltered[subject]['OneToOne'].notna() &
						dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notna() &
						dfFiltered[subject][test].notna()
					]
					
					# run ANOVA for TITLE1ELIG because everything's categorical
					if test == "TITLE1ELIG":
						#run AVOVA test and print summary results
						formula = f'{subject}_ZSCORE_CHANGE ~ C(OneToOne) + C({test}) + C(OneToOne):C({test})'
						model = smf.ols(formula, data=dfTesting).fit()
						anova_table = sm.stats.anova_lm(model, typ=2)
						
						print("\n-------")
						print(f"ANOVA test for effect of OneToOne, {test}, and their interaction on {subject}_ZSCORE_CHANGE:\n")
						print(anova_table, '\n')
						print(f"\nn: {len(dfTesting)}")
						
					# otherwise run linear regression
					else:
						# create OLS model and print summary results
						formula = f'Q("{subject}_ZSCORE_CHANGE") ~ C(OneToOne) + Q("{test}") + C(OneToOne):Q("{test}")'
						model = smf.ols(formula, data=dfTesting).fit()
						
						print("\n-------")
						print(f"Linear regression for the effect of OneToOne, {test}, and their interaction on {subject}_ZSCORE_CHANGE:\n")
						print(model.summary(), '\n')
				
		print("\n-------")
		
		# begin creation of boxplots 
		sns.set(style="whitegrid")
		
		# set TNR as the font for all plots
		plt.rcParams['font.family'] = 'Times New Roman'
		
		for subject in ['MATH', 'ENG']:
			
			# filter data
			dfTesting = dfFiltered[subject][
				(dfFiltered[subject]['OneToOne'].notnull()) &
				(dfFiltered[subject][f'{subject}_ZSCORE_CHANGE'].notnull())
			]
			
			# create boxplot
			fig = plt.figure(figsize=(8, 5))
			sns.boxplot(x='OneToOne', y=f'{subject}_ZSCORE_CHANGE', data=dfTesting)
			
			# define labels and other layout specs
			plt.xlabel("")
			if subject == "ENG":
				plt.ylabel("ELA z-Score Change")
			else:
				plt.ylabel("Math z-Score Change")
			plt.xticks(ticks=[0, 1], labels=["No 1:1-Device Access", "1:1-Device Access"])
			plt.tight_layout()
			
			# save boxplot as high-res PNG
			plt.savefig(f'{subject}_boxplot.png', dpi=300, bbox_inches='tight')
			
			plt.close() 
			print(f"Generated boxplot for {subject}_ZSCORE_CHANGE by 1:1-device access")
		
exit()

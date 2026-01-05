#!/usr/bin/env python3
# scripted by Matthew Prins, April-August 2025
'''This script automates the ingestion, cleaning, and merging of 
   disparate datasets for a study examining the impact of 1:1 digital 
   device access on academic growth in mathematics and English 
   Language Arts during the COVID-19 pandemic'''


# import relevant Python libraries
import csv
import re
import numpy as np
import inspect

# function imported into the data analysis Python program as dataImportProcessingARP.dataFinal
def dataFinal():

	# function for importing relevant CRDC, CCD, and SAIPE data by state
	def importCRDC (state):
		
		# open the CRDC school characteristics CSV file
		with open("2020-21-crdc-data/CRDC/School/School Characteristics.csv", mode="r", newline="") as csvFile:
			
			# import each line as dictionaries with the CSV header as the variable keys
			reader = csv.DictReader(csvFile)
			
			# make nested list of dictionaries of schools from the correct state
			data = [row for row in reader
				if row.get('LEA_STATE') == state
			]
			
		# same thing, but for the internet access and devices CSV
		with open("2020-21-crdc-data/CRDC/School/Internet Access and Devices.csv", mode="r", newline="") as csvFile:
			reader = csv.DictReader(csvFile)
			# build a lookup dictionary using COMBOKEY as the key
			internetData = {row['COMBOKEY']: row for row in reader}
			
		# if COMBOKEY is the same in both databases, add the field SCH_INTERNET_WIFIENDEV to data
		for school in data:
			if school['COMBOKEY'] in internetData:
				school['SCH_INTERNET_WIFIENDEV'] = internetData[school['COMBOKEY']].get('SCH_INTERNET_WIFIENDEV')
				
		# same thing, but for the COVID directional indicators CSV
		with open("2020-21-crdc-data/CRDC/School/COVID Directional Indicators.csv", mode="r", newline="") as csvFile:
			reader = csv.DictReader(csvFile)																																																																																																																																																																																													
			# build a lookup dictionary using COMBOKEY as the key
			covidData = {row['COMBOKEY']: row for row in reader}
			
		# if COMBOKEY is the same in both databases, add the COVID instructional mode fields to data
		for school in data:
			if school['COMBOKEY'] in covidData:
				school['SCH_DIND_INSTRUCTIONTYPE'] = covidData[school['COMBOKEY']].get('SCH_DIND_INSTRUCTIONTYPE')
				school['SCH_DIND_VIRTUALTYPE'] = covidData[school['COMBOKEY']].get('SCH_DIND_VIRTUALTYPE')
				
		# same thing, but for the enrollment CSV
		with open("2020-21-crdc-data/CRDC/School/Enrollment.csv", mode="r", newline="") as csvFile:
			reader = csv.DictReader(csvFile)
			# build a lookup dictionary using COMBOKEY as the key
			enrollmentData = {row['COMBOKEY']: row for row in reader}
			
		# if COMBOKEY is the same in both databases, add the total enrollment to data
		for school in data:
			if school['COMBOKEY'] in enrollmentData:
				
				# sum all students by gender/race breakdown to get total number of students at the school
				sum = 0
				for studentCategory in ['SCH_ENR_HI_M', 'SCH_ENR_HI_F', 'SCH_ENR_AM_M', 'SCH_ENR_AM_F', 'SCH_ENR_AS_M', 'SCH_ENR_AS_F', 'SCH_ENR_HP_M', 'SCH_ENR_HP_F', 'SCH_ENR_BL_M', 'SCH_ENR_BL_F', 'SCH_ENR_WH_M', 'SCH_ENR_WH_F', 'SCH_ENR_TR_M', 'SCH_ENR_TR_F']:
					if int(enrollmentData[school['COMBOKEY']].get(studentCategory)) > 0: #exclude error codes
						sum += int(enrollmentData[school['COMBOKEY']].get(studentCategory))
				school['TOTAL_ENROLLMENT'] = sum
				
				# create data column that is the ratio of devices to enrollment, max of 1
				if int(school['SCH_INTERNET_WIFIENDEV']) >= 0 and sum > 0: # exclude error codes and division by zero
					if int(school['SCH_INTERNET_WIFIENDEV'])/sum > 1:
						school['RATIO_DEVICES_TO_ENROLLMENT'] = 1.0
					else:	
						school['RATIO_DEVICES_TO_ENROLLMENT'] = int(school['SCH_INTERNET_WIFIENDEV'])/sum
				
				# sum Black students
				sum = 0
				for studentCategory in ['SCH_ENR_BL_M', 'SCH_ENR_BL_F']:
					if int(enrollmentData[school['COMBOKEY']].get(studentCategory)) > 0: #exclude error codes
						sum += int(enrollmentData[school['COMBOKEY']].get(studentCategory))
				school['TOTAL_ENROLLMENT_BLACK'] = sum
				
				# sum Hispanic students
				sum = 0
				for studentCategory in ['SCH_ENR_HI_M', 'SCH_ENR_HI_F']:
					if int(enrollmentData[school['COMBOKEY']].get(studentCategory)) > 0: #exclude error codes
						sum += int(enrollmentData[school['COMBOKEY']].get(studentCategory))
				school['TOTAL_ENROLLMENT_HISPANIC'] = sum
		
		# open the CCD school characteristics CSV file
		with open("ccd_sch_129_2021_w_1a_080621/ccd_sch_129_2021_w_1a_080621.csv", mode="r", newline="", encoding="ISO-8859-1") as csvFile:
			reader = csv.DictReader(csvFile)
			# build a lookup dictionary using COMBOKEY as the key
			ccdData = {row['NCESSCH']: row for row in reader}
			
		# map CRDC COMBOKEY to NCESSCH from CCD; add ST_SCHID and Title 1 eligibility
		for school in data:
			if school['COMBOKEY'] in ccdData:
				school['ST_SCHID'] = ccdData[school['COMBOKEY']].get('ST_SCHID')
				if ccdData[school['COMBOKEY']].get('TITLEI_STATUS') == 'NOTTITLE1ELIG':
					school['TITLE1ELIG'] = 0 
				elif ccdData[school['COMBOKEY']].get('TITLEI_STATUS') != 'Not reported':
					school['TITLE1ELIG'] = 1
					
		# open the SAIPE CSV file (exported from Excel)
		fieldnames = ['state', 'stateCode', 'districtCode', 'districtName', 'population', 'studentPopulation', 'studentPovertyPopulation']
		with open("SAIPE/ussd20.csv", mode="r", newline="", encoding="ISO-8859-1") as csvFile:
			reader = csv.DictReader(csvFile,  fieldnames=fieldnames)  
			# build a lookup dictionary using LEAID as the key
			saipeData = {row['stateCode'] + row['districtCode']: row for row in reader}
		
		# add DISTRICT_POVERTY_PERCENTAGE = student poverty / total students (SAIPE)
		for school in data:
			if school['LEAID'] in saipeData:
				school['DISTRICT_POVERTY_PERCENTAGE'] = int(saipeData[school['LEAID']].get('studentPovertyPopulation').replace(",", "")) / int(saipeData[school['LEAID']].get('studentPopulation').replace(",", ""))
		return data
	
	# function for merging Alabama data
	def assessmentAL ():
		# import Alabama CRDC/CCD data
		data = importCRDC ('AL')
		
		# import Alabama state assessment results
		# exported from https://www.alabamaachieves.org/reports-data/school-performance/
		resultsToMerge = [
			{'file': 'AL/AL-2019-COMBOKEY.csv', 'subject': 'Reading', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'AL/AL-2019-COMBOKEY.csv', 'subject': 'Math', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'AL/AL-2021-COMBOKEY.csv', 'subject': 'ELA', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'AL/AL-2021-COMBOKEY.csv', 'subject': 'Math', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}		
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"0{row['COMBOKEY']}": row
							for row in reader
							if row.get('Enrolled') != '*' #exclude those with no data provided
							# and row.get('Proficient Rate') != '*'
							and row.get("Subject") == test['subject']}
				
			# if COMBOKEY is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'COMBOKEY' in school and school['COMBOKEY'] in stateData:
					# derive proficiency by priority: (1) 'Proficient Rate' if present; else (2) Level3 + Level4; else (3) 100 - (Level1 + Level2)
					proficientRate = []
					if stateData[school['COMBOKEY']].get('Proficient Rate') != '*':
						proficientRate.append(float(stateData[school['COMBOKEY']].get('Proficient Rate')))
					if stateData[school['COMBOKEY']].get('Level 3 %') not in ['*', '~'] and stateData[school['COMBOKEY']].get('Level 4 %') not in ['*', '~']:
						proficientRate.append(float(stateData[school['COMBOKEY']].get('Level 3 %')) + float(stateData[school['COMBOKEY']].get('Level 4 %')))
					if stateData[school['COMBOKEY']].get('Level 1 %') not in ['*', '~'] and stateData[school['COMBOKEY']].get('Level 2 %') not in ['*', '~']:
						proficientRate.append(100 - float(stateData[school['COMBOKEY']].get('Level 1 %')) - float(stateData[school['COMBOKEY']].get('Level 2 %')))
					
					# tested count: use Tested when available; otherwise fall back to 'Enrolled' - 10
					if proficientRate:
						if stateData[school['COMBOKEY']].get('Tested') != '*':
							school[test['studentsVar']] = int(float(stateData[school['COMBOKEY']].get('Tested')))
						else:
							school[test['studentsVar']] = int(float(stateData[school['COMBOKEY']].get('Enrolled'))) - 10
						school[test['passVar']] = proficientRate[0]
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Arkansas data
	def assessmentAR ():
		# import Arkansas CRDC/CCD data
		data = importCRDC ('AR')
		
		# import Arkansas state assessment results
		# exported from https://dese.ade.arkansas.gov/Offices/public-school-accountability/assessment-test-scores
		resultsToMerge = [
			{'file': 'AR/20201203132354_ACT_Aspire_Summary_10052020.csv', 'grade': '03', 'studentsVarEng': '3_ENG_NUMBER_STUDENTS', 'passVarEng': '3_ENG_PASS', 'studentsVarMath': '3_MATH_NUMBER_STUDENTS', 'passVarMath': '3_MATH_PASS'},
			{'file': 'AR/ACT_Aspire_Summary_Post_Appeals_Spring_2021_20210930124157.csv', 'grade': '05', 'studentsVarEng': '5_ENG_NUMBER_STUDENTS', 'passVarEng': '5_ENG_PASS', 'studentsVarMath': '5_MATH_NUMBER_STUDENTS', 'passVarMath': '5_MATH_PASS'}	
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# key on "AR-{District LEA}-{School LEA}" to align with CCD ST_SCHID
				stateData = {f"AR-{row['District LEA']}-{row['School LEA']}": row
							for row in reader
							if (row.get('Grade') == test['grade'] or row.get('Grade Level') == test['grade'])
							and row.get('English N') != 'N<10'} #exclude those with no data provided
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVarEng']] = int(stateData[school['ST_SCHID']].get('English N'))
					school[test['passVarEng']] = float(stateData[school['ST_SCHID']].get('English % Met Readiness Benchmark')[:-1]) # cut % sign
					school[test['studentsVarMath']] = int(stateData[school['ST_SCHID']].get('Math N'))
					school[test['passVarMath']] = float(stateData[school['ST_SCHID']].get('Math % Met Readiness Benchmark')[:-1])
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Georgia data
	def assessmentGA ():
		# import Georgia CRDC/CCD data
		data = importCRDC ('GA')
		
		# import Georgia state assessment results
		# exported from https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data
		resultsToMerge = [
			{'file': 'GA/EOG_2019_By_Grad_FEB_24_2020.csv', 'subject': 'English Language Arts', 'grade': '03', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'GA/EOG_2019_By_Grad_FEB_24_2020.csv', 'subject': 'Mathematics', 'grade': '03', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'GA/EOG_2021_by_grade_March_7_2022.csv', 'subject': 'English Language Arts', 'grade': '05', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'GA/EOG_2021_by_grade_March_7_2022.csv', 'subject': 'Mathematics', 'grade': '05', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}		
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# key "GA-{SCHOOL_DISTRCT_CD}-{INSTN_NUMBER.zfill(4)}" to match CCD ST_SCHID format
				stateData = {f"GA-{row['SCHOOL_DISTRCT_CD']}-{row['INSTN_NUMBER'].zfill(4)}": row
							for row in reader
							# N < 10 excluded by GA
							if row.get('NUM_TESTED_CNT') != 'TFS'
							and row.get('SUBGROUP_NAME') == "All Students"
							and row.get('TEST_CMPNT_TYP_NM') == test['subject']
							and (row.get('ACDMC_LVL') == test['grade'] or row.get('ACDMC_LVL') == test['grade'][1:])
						}
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVar']] = int(stateData[school['ST_SCHID']].get('NUM_TESTED_CNT'))
					school[test['passVar']] = float(stateData[school['ST_SCHID']].get('PROFICIENT_PCT')) + float(stateData[school['ST_SCHID']].get('DISTINGUISHED_PCT')) 
					
		# add Z scores
		data = calculateZScores(data)
		
		return data

	# function for merging Indiana data
	def assessmentIN ():
		# import Georgia CRDC/CCD data
		data = importCRDC ('IN')
		
		# import Indiana state assessment results
		# exported from https://www.in.gov/doe/it/data-center-and-reports/data-reports-archive
		resultsToMerge = [
			{'file': 'IN/ilearn-2019-grade3-8-final-school-ELA.csv', 'subject': 'English Language Arts', 'grade': '03', 'testedNo': 'ELA Total Tested', 'proficient': 'ELA Proficient %', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'IN/ilearn-2019-grade3-8-final-school-math.csv', 'subject': 'Mathematics', 'grade': '03','testedNo': 'Math Total Tested', 'proficient': 'Math Proficient %', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'IN/ILEARN-2021-Grade3-8-Final-School-ELA.csv', 'subject': 'English Language Arts', 'grade': '05', 'testedNo': 'ELA Total Tested', 'proficient': 'ELA Proficient %', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'IN/ILEARN-2021-Grade3-8-Final-School-Math.csv', 'subject': 'Mathematics', 'grade': '05', 'testedNo': 'Math Total Tested', 'proficient': 'Math Proficient %', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}	
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# key on "IN-{Corp ID}-{School ID}" to align with CCD ST_SCHID
				stateData = {f"IN-{row['Corp ID']}-{row['School ID']}": row
							for row in reader
							# N < 10 excluded by IN
							if row.get(test['proficient']) != '***' 
							and row.get(test['proficient']) != ''
						}
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVar']] = int(stateData[school['ST_SCHID']].get(test['testedNo']))
					school[test['passVar']] = float(stateData[school['ST_SCHID']].get(test['proficient'])[:-1])
					
		# add Z scores
		data = calculateZScores(data)
		
		return data

	# function for merging Iowa data
	def assessmentIA ():
		# import Iowa CRDC/CCD data
		data = importCRDC ('IA')
		
		# import Iowa state assessment results
		# exported from https://www.zelma.ai/data
		
		resultsToMerge = [
			{'file': 'IA/edc-2.1-iowa-2019.csv', 'grade': 'G03', 'subject': 'math', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'IA/edc-2.1-iowa-2019.csv', 'grade': 'G03', 'subject': 'ela', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'IA/IA_AssmtData_2021.csv', 'grade': 'G05', 'subject': 'math', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'},
			{'file': 'IA/IA_AssmtData_2021.csv', 'grade': 'G05', 'subject': 'ela', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'}
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"IA-**{str(row['StateAssignedDistID']).zfill(4)} 000-**{str(row['StateAssignedDistID']).zfill(4)} {row['StateAssignedSchID'][-3:]}": row
							for row in reader
							if (row.get('GradeLevel') == test['grade'])
							and row.get('StudentGroup') == 'All Students'
							and row.get('DataLevel') == 'School'
							and row.get('Subject') == test['subject']
							and row.get('StudentSubGroup_TotalTested') != '*'
							and row.get('ProficientOrAbove_percent') != '*'
							and row.get('ProficientOrAbove_percent') != '.'
						} #exclude those with no data provided
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school:
					maskedST_SCHID = re.sub(r'(\d{2})(\d{4})', r'**\2', school['ST_SCHID'])
					if maskedST_SCHID in stateData:
						school[test['studentsVar']] = int(stateData[maskedST_SCHID].get('StudentSubGroup_TotalTested'))
						school[test['passVar']] = float(stateData[maskedST_SCHID].get('ProficientOrAbove_percent'))
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Louisiana data
	def assessmentLA ():
		# import Louisiana CRDC/CCD data
		data = importCRDC ('LA')
		
		# import Louisiana state assessment results
		# exported from https://doe.louisiana.gov/data-and-reports/elementary-and-middle-school-performance
		resultsToMerge = [
			{'file': 'LA/2019-school-leap-2025-achievement-level-summary.csv', 'studentsVarEng': '3_ENG_NUMBER_STUDENTS', 'passVarEng': '3_ENG_PASS', 'studentsVarMath': '3_MATH_NUMBER_STUDENTS', 'passVarMath': '3_MATH_PASS'},
			{'file': 'LA/2021-leap-2025-state-lea-school-achievement-level-summary.csv', 'studentsVarEng': '5_ENG_NUMBER_STUDENTS', 'passVarEng': '5_ENG_PASS', 'studentsVarMath': '5_MATH_NUMBER_STUDENTS', 'passVarMath': '5_MATH_PASS'}	
		]
		
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"LA-{row['Site Code'][:3]}-{row['Site Code']}": row
							for row in reader
							if row.get('Total Students Tested in at Least One Subject') != '<10'
							and row.get('ELA M') != 'NR'
							and row.get('ELA A') != 'NR' 
						} #exclude those with no data provided
			
			# change all "≤1" for test results to 0
			for record in stateData.values():
				for key, value in record.items():
					if value == "≤1":
						record[key] = 0
			
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVarEng']] = int(stateData[school['ST_SCHID']].get('Total Students Tested in at Least One Subject')[1:])
					school[test['passVarEng']] = int(stateData[school['ST_SCHID']].get('ELA A')) + int(stateData[school['ST_SCHID']].get('ELA M'))
					school[test['studentsVarMath']] = int(stateData[school['ST_SCHID']].get('Total Students Tested in at Least One Subject')[1:])
					school[test['passVarMath']] = int(stateData[school['ST_SCHID']].get('Math A')) + int(stateData[school['ST_SCHID']].get('Math M'))
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Mississippi data
	def assessmentMS ():
		# import Mississippi CRDC/CCD data
		data = importCRDC ('MS')
		
		# import Mississippi state assessment results
		# exported from https://mdek12.org/publicreporting/assessment/
		with open('MS/MS-All-COMBOKEY.csv', mode="r", newline="") as csvFile:
			# import each line as dictionaries with the CSV header as the variable keys
			reader = csv.DictReader(csvFile)
				
			# make nested list of dictionaries of results
			stateData = {row['COMBOKEY']: row
						for row in reader
						if row.get('Math 2019 Level 3 (PCT)') != '*' #exclude those with no data provided
						and row.get('2021 Math Level 3 (PCT)') != '*'}
		
		# if COMBOKEY is from data is the same as key from stateData, add number of students and pass rate
		for school in data:
			if 'COMBOKEY' in school and school['COMBOKEY'] in stateData:
				for subject in [['3_ENG', 'ELA 2019'], ['3_MATH', 'Math 2019'],['5_ENG', '2021 ELA'],['5_MATH', '2021 Math']]:
					school[f"{subject[0]}_NUMBER_STUDENTS"] = int(float(stateData[school['COMBOKEY']].get(f"{subject[1]} Test-Takers")))
					# proficiency = Level 3 + 4 + 5
					school[f"{subject[0]}_PASS"] = float(stateData[school['COMBOKEY']].get(f"{subject[1]} Level 3 (PCT)")[:-1]) + float(stateData[school['COMBOKEY']].get(f"{subject[1]} Level 4 (PCT)")[:-1]) + float(stateData[school['COMBOKEY']].get(f"{subject[1]} Level 5 (PCT)")[:-1])
	
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Nebraska data
	def assessmentNE ():
		# import NE CRDC/CCD data
		data = importCRDC ('NE')
		
		# import NE state assessment results
		# exported from https://nep.education.ne.gov/#/data-downloads
		resultsToMerge = [
			{'file': 'NE/NSCAS_ELA_Proficient_20202021.csv', 'school year': '2018-2019', 'grade': '03', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'NE/NSCAS_Math_Proficient_20202021.csv', 'school year': '2018-2019', 'grade': '03','studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'NE/NSCAS_ELA_Proficient_20202021.csv', 'school year': '2020-2021', 'grade': '05', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'NE/NSCAS_Math_Proficient_20202021.csv', 'school year': '2020-2021', 'grade': '05', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}		
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# key "NE-{County}{District}000-{County}{District}{School}" matches CCD ST_SCHID
				stateData = {f"NE-{row['County']}{row['District']}000-{row['County']}{row['District']}{row['School']}": row
							for row in reader
							if row.get('Proficient Pct') != '-1' 
							and row.get('Advanced Pct') != '-1' #exclude those with no data provided
							and row.get('Category') == "All Students"
							and row.get('School Year') == test['school year']
							and row.get('Grade') == test['grade']} 
				
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVar']] = int(stateData[school['ST_SCHID']].get('Student Count'))
					school[test['passVar']] = float(stateData[school['ST_SCHID']].get('Proficient Pct')) + float(stateData[school['ST_SCHID']].get('Advanced Pct')) 
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging South Carolina data
	def assessmentSC ():
		# import South Carolina CRDC/CCD data
		data = importCRDC ('SC')
		
		# import South Carolina state assessment results
		# exported from https://ed.sc.gov/data/test-scores/state-assessments/sc-ready/
		
		resultsToMerge = [
			{'file': 'SC/SCREADY 2018-2019 Press Release v2.csv', 'grade': '03', 'studentsVarEng': '3_ENG_NUMBER_STUDENTS', 'passVarEng': '3_ENG_PASS', 'studentsVarMath': '3_MATH_NUMBER_STUDENTS', 'passVarMath': '3_MATH_PASS'},
			{'file': 'SC/SCREADY 2020-2021 Press Release V3.csv', 'grade': '05', 'studentsVarEng': '5_ENG_NUMBER_STUDENTS', 'passVarEng': '5_ENG_PASS', 'studentsVarMath': '5_MATH_NUMBER_STUDENTS', 'passVarMath': '5_MATH_PASS'}
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"SC-{row['schoolid'][:4]}-{row['schoolid'][4:]}": row
							for row in reader
							if (row.get('testgrade') == test['grade'])
							and row.get('demoID') == '01ALL'
							and row.get('ELAN') != ''
							and row.get('ELApct34') != ''
							and row.get('MathN') != ''
							and row.get('Mathpct34') != ''
						} #exclude those with no data provided
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVarEng']] = int(stateData[school['ST_SCHID']].get('ELAN'))
					school[test['passVarEng']] = float(stateData[school['ST_SCHID']].get('ELApct34'))
					school[test['studentsVarMath']] = int(stateData[school['ST_SCHID']].get('MathN'))
					school[test['passVarMath']] = float(stateData[school['ST_SCHID']].get('Mathpct34'))
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging South Dakota data
	def assessmentSD ():
		# import South Dakota CRDC/CCD data
		data = importCRDC ('SD')
		
		# import South Dakota state assessment results
		# exported from https://www.zelma.ai/data
		
		resultsToMerge = [
			{'file': 'SD/edc-2.1-south dakota-2019.csv', 'grade': 'G03', 'subject': 'math', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'SD/edc-2.1-south dakota-2019.csv', 'grade': 'G03', 'subject': 'ela', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'SD/edc-2.1-south dakota-2021.csv', 'grade': 'G05', 'subject': 'math', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'},
			{'file': 'SD/edc-2.1-south dakota-2021.csv', 'grade': 'G05', 'subject': 'ela', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'}
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"SD-{row['StateAssignedSchID']}": row
							for row in reader
							if (row.get('GradeLevel') == test['grade'])
							and row.get('StudentGroup') == 'All Students'
							and row.get('DataLevel') == 'School'
							and row.get('Subject') == test['subject']
							and row.get('StudentSubGroup_TotalTested') != '*'
							and row.get('ProficientOrAbove_percent') != '*'
						} #exclude those with no data provided

			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVar']] = int(stateData[school['ST_SCHID']].get('StudentSubGroup_TotalTested'))
					school[test['passVar']] = float(stateData[school['ST_SCHID']].get('ProficientOrAbove_percent'))
						
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Texas data
	def assessmentTX ():
		# import Texas CRDC/CCD data
		data = importCRDC ('TX')
		
		# import Texas state assessment results
		# exported from https://txresearchportal.com/
		resultsToMerge = [
			{'file': 'TX/TX-Reading-3.csv', 'testType': 'STAAR - Reading', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'TX/TX-Math-3.csv', 'testType': 'STAAR - Mathematics', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'TX/TX-Reading-5.csv', 'testType': 'STAAR - Reading', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'TX/TX-Math-5.csv', 'testType': 'STAAR - Mathematics', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}		
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"TX-{row['ID/CDC'][:-3]}-{row['ID/CDC']}": row
							for row in reader
							if row.get(test['testType'] + '|Performance Levels|Meets and Above|Percentage') != ''
							and row.get(test['testType'] + '|Tests Taken') != '' #exclude those with no data provided
							and row.get('Student Group') == "All Students"}
				
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID' in school and school['ST_SCHID'] in stateData:
					school[test['studentsVar']] = int(stateData[school['ST_SCHID']].get(test['testType'] + '|Tests Taken'))
					school[test['passVar']] = float(stateData[school['ST_SCHID']].get(test['testType'] + '|Performance Levels|Meets and Above|Percentage'))
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Utah data
	def assessmentUT ():
		# import Utah CRDC/CCD data
		data = importCRDC ('UT')
		
		# import Utah state assessment results
		# exported from https://schools.utah.gov/datastatistics/reports
		# COMBOKEY added to CSV via VLOOKUP and manually
		with open('UT/UT-all-COMBOKEY.csv', mode="r", newline="") as csvFile:
			# import each line as dictionaries with the CSV header as the variable keys
			reader = csv.DictReader(csvFile)
			
			# make nested list of dictionaries of results that are of the relevant test
			stateData = {f"{row['Combokey']}-{row['School Year']}-{row['Grade']}-{row['Subject']}": row
							for row in reader
							if row.get('Percent Proficient') != 'N<10' } # exclude those with no data provided
			
			for utTest in [
				{'school year': '2019', 'testType': 'English Language Arts', 'grade': '3rd Grade Language Arts', 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
				{'school year': '2019', 'testType': 'Mathematics', 'grade': '3rd Grade Math', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
				{'school year': '2021', 'testType': 'English Language Arts', 'grade': '5th Grade Language Arts', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
				{'school year': '2021', 'testType': 'Mathematics', 'grade': '5th Grade Math', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}	
			]:
				# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
				for school in data:
					if 'COMBOKEY' in school:
						matchingKey = f"{school['COMBOKEY']}-{utTest['school year']}-{utTest['grade']}-{utTest['testType']}"
						if matchingKey in stateData:
							school[utTest['studentsVar']] = int(stateData[matchingKey].get('Number Students'))
							# if a range for percent proficient/advanced, average the smallest and largest
							if stateData[matchingKey].get('Percent Proficient')[:2] == '<=':
								school[utTest['passVar']] = int(stateData[matchingKey].get('Percent Proficient')[2:][:-1])/2
							elif stateData[matchingKey].get('Percent Proficient')[:2] == '>=':
								school[utTest['passVar']] = (int(stateData[matchingKey].get('Percent Proficient')[2:][:-1]) + 100)/2
							elif '-' in stateData[matchingKey].get('Percent Proficient', ''):
								range_str = stateData[matchingKey].get('Percent Proficient', '').replace('%', '')
								low, high = map(int, range_str.split('-'))
								school[utTest['passVar']] = (low + high) / 2
							else:
								school[utTest['passVar']] = float(stateData[matchingKey].get('Percent Proficient')[:-1])
								
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Vermont data
	def assessmentVT ():
		# import Vermont CRDC/CCD data
		data = importCRDC ('VT')
		
		# make shorter ST_SCHID for VT, e.g. VT-T151-PS223 to VT-PS223
		for school in data:
			if 'ST_SCHID' in school:
				school['ST_SCHID_shortened'] = re.sub(r"^(\w+)-\w+-(\w+)$", r"\1-\2", school['ST_SCHID'])
				
		# import Vermont state assessment results
		# exported from https://education.vermont.gov/sites/aoe/files/documents/Assessment_Sept2023.zip
		resultsToMerge = [
			{'file': 'VT/Smarter Balance_Assessment_2019.csv', 'subject': 'SB English Language Arts Grade 03',  'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
			{'file': 'VT/Smarter Balance_Assessment_2019.csv', 'subject': 'SB Math Grade 03','studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS'},
			{'file': 'VT/Smarter Balance_Assessment_2021.csv', 'subject': 'SB English Language Arts Grade 05', 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
			{'file': 'VT/Smarter Balance_Assessment_2021.csv', 'subject': 'SB Math Grade 05', 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}		
		]
		for test in resultsToMerge:
			with open(test['file'], mode="r", newline="") as csvFile:
				# import each line as dictionaries with the CSV header as the variable keys
				reader = csv.DictReader(csvFile)
				
				# make nested list of dictionaries of results that are of the relevant test
				stateData = {f"VT-{row['OrganizationIdentifer']}": row
							for row in reader
							if row.get('IndicatorLabel') == "Total Proficient and Above"
							and row.get('TestName') == test['subject']
							and row.get('AssessGroup') == "All Students"
							and row.get('SchoolValue') != ""}
				
				# add number of students for each test
				csvFile.seek(0) # rewind reader
				for row in reader:
					if row.get('IndicatorLabel') == "Number of Students Tested" and row.get('TestName') == test['subject'] and row.get('AssessGroup') == "All Students" and row.get('SchoolValue') != "" and f"VT-{row['OrganizationIdentifer']}" in stateData:
						stateData[f"VT-{row['OrganizationIdentifer']}"]['NumberStudents'] = row.get('SchoolValue')
						
			# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
			for school in data:
				if 'ST_SCHID_shortened' in school and school['ST_SCHID_shortened'] in stateData:
					school[test['studentsVar']] = float(stateData[school['ST_SCHID_shortened']].get('NumberStudents'))
					school[test['passVar']] = float(stateData[school['ST_SCHID_shortened']].get('SchoolValue'))
					
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for merging Wyoming data
	def assessmentWY ():
		# import Wyoming CRDC/CCD data
		data = importCRDC ('WY')
		
		# import WY state assessment results
		# exported from https://edu.wyoming.gov/data/assessment-reports/
		# COMBOKEY added to CSV via VLOOKUP and manually
		with open('WY/WY-all-COMBOKEY.csv', mode="r", newline="") as csvFile:
			# import each line as dictionaries with the CSV header as the variable keys
			reader = csv.DictReader(csvFile)
			
			# make nested list of dictionaries of results that are of the relevant test
			stateData = {f"{row['COMBOKEY']}-{row['SCHOOL YEAR']}-{row['GRADE']}-{row['SUBJECT']}": row
							for row in reader
							if row.get('PERCENT PROFICIENT ADVANCED') != '.' } # exclude those with no data provided
			
			
			for wyTest in [
				{'school year': '2018-19', 'testType': 'English Language Arts (ELA)', 'grade': 3, 'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS'},
				{'school year': '2018-19', 'testType': 'Math', 'studentsVar': '3_MATH_NUMBER_STUDENTS', 'grade': 3, 'passVar': '3_MATH_PASS'},
				{'school year': '2020-21', 'testType': 'English Language Arts (ELA)', 'grade': 5, 'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS'},
				{'school year': '2020-21', 'testType': 'Math', 'grade': 5, 'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS'}	
			]:
				# if ST_SCHID is from data is the same as key from stateData, add number of students and pass rate
				for school in data:
					if 'COMBOKEY' in school:
						matchingKey = f"{school['COMBOKEY']}-{wyTest['school year']}-{wyTest['grade']}-{wyTest['testType']}"
						if matchingKey in stateData:
							# average the smallest and largest values from the range for number of students
							school[wyTest['studentsVar']] = sum(map(int, stateData[matchingKey].get('NUMBER OF STUDENTS TESTED').split('-'))) / 2
							# if a range for percent proficient/advanced, average the smallest and largest
							if stateData[matchingKey].get('PERCENT PROFICIENT ADVANCED')[:2] == '<=':
								school[wyTest['passVar']] = int(stateData[matchingKey].get('PERCENT PROFICIENT ADVANCED')[2:][:-1])/2
							elif stateData[matchingKey].get('PERCENT PROFICIENT ADVANCED')[:2] == '>=':
								school[wyTest['passVar']] = (int(stateData[matchingKey].get('PERCENT PROFICIENT ADVANCED')[2:][:-1]) + 100)/2
							else:
								school[wyTest['passVar']] = float(stateData[matchingKey].get('PERCENT PROFICIENT ADVANCED')[:-1])
								
		# add Z scores
		data = calculateZScores(data)
		
		return data
	
	# function for calculating Z scores and Z-score changes
	def calculateZScores (data):
		zScorestoCalculate = [
			{'studentsVar': '3_ENG_NUMBER_STUDENTS', 'passVar': '3_ENG_PASS', 'zScoreVar': '3_ENG_ZSCORE'},
			{'studentsVar': '3_MATH_NUMBER_STUDENTS', 'passVar': '3_MATH_PASS', 'zScoreVar': '3_MATH_ZSCORE'},
			{'studentsVar': '5_ENG_NUMBER_STUDENTS', 'passVar': '5_ENG_PASS', 'zScoreVar': '5_ENG_ZSCORE'},
			{'studentsVar': '5_MATH_NUMBER_STUDENTS', 'passVar': '5_MATH_PASS', 'zScoreVar': '5_MATH_ZSCORE'}	
		]
		# iterate through zScorestoCalculate
		for zScore in zScorestoCalculate:
			
			# build distribution from schools with ≥20 tested and not SPED/Magnet/Charter/Alternative
			passPercentages = [row[zScore['passVar']] for row in data if zScore['passVar'] in row 
				and row[zScore['studentsVar']] >= 20
				and row.get('SCH_STATUS_SPED') == 'No'
				and row.get('SCH_STATUS_MAGNET') == 'No'
				and row.get('SCH_STATUS_CHARTER') == 'No'
				and row.get('SCH_STATUS_ALT') == 'No']
			
			# calculate mean and standard deviation
			mean = np.mean(passPercentages)
			sd = np.std(passPercentages, ddof=1)
			
			# add Z score to data
			for school in data:
				if zScore['passVar'] in school:
					school[zScore['zScoreVar']] = (school[zScore['passVar']] - mean) / sd
					
		# add Z score changes to data
		for school in data:
			if '5_ENG_ZSCORE' in school and '3_ENG_ZSCORE' in school:
				school['ENG_ZSCORE_CHANGE'] = (school['5_ENG_ZSCORE'] - school['3_ENG_ZSCORE'])
			if '5_MATH_ZSCORE' in school and '3_MATH_ZSCORE' in school:
				school['MATH_ZSCORE_CHANGE'] = (school['5_MATH_ZSCORE'] - school['3_MATH_ZSCORE'])
				
		# print completion
		print("data imported and z scores calculated for function", inspect.stack()[1].function)
		return data
	
	# import data by state
	stateDatasets = {
		"Alabama": assessmentAL(),
		"Arkansas": assessmentAR(),
		"Georgia": assessmentGA(),
		"Indiana": assessmentIN(),
		"Iowa": assessmentIA(),
		"Louisiana": assessmentLA(),
		"Mississippi": assessmentMS(),
		"Nebraska": assessmentNE(),
		"South Carolina": assessmentSC(),
		"South Dakota": assessmentSD(),
		"Texas": assessmentTX(),
		"Utah": assessmentUT(),
		"Vermont": assessmentVT(),
		"Wyoming": assessmentWY()
	}
	
	# consolidate per-state lists into a single list of school records
	stateDatasets["All"] = [school for data in stateDatasets.values() for school in data]
	
	return stateDatasets

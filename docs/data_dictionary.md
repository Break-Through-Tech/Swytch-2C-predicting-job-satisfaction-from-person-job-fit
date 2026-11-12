# Data Dictionary: GSS 2024 & O*NET Merged Dataset

id - Unique identification number for each survey respondent
year - Survey year (2024)
ballot - GSS ballot form version assigned to the respondent
wtssps - Weight variable used for post-stratification adjustments
wtssnrps - Weight variable accounting for survey non-response and post-stratification
vpsu - Variance Primary Sampling Unit for analyzing complex survey design
vstrat - Variance stratum for complex survey design errors
satjob - Target variable: Respondent's self-reported job satisfaction level
occ10 - 2010 Census occupation code assigned to the respondent's job
indus10 - 2010 Census industry code assigned to the respondent's workplace
wrkstat - Employment status (e.g., working full-time, part-time, retired, unemployed)
wrkslf - Indicator of whether the respondent is self-employed or works for someone else
prestg10 - 2010 Occupational prestige score (social standing of the occupation)
sei10 - 2010 Socioeconomic Index score combining income, education, and occupation
realrinc - Real family income adjusted for inflation
rincom16 - Respondent's individual income category
hrs1 - Number of hours worked last week
hrs2 - Number of hours usually worked per week
weekswrk - Total number of weeks worked in the past year
age - Age of the respondent in years
sex - Biological sex of the respondent
race - Racial background category of the respondent
hispanic - Hispanic origin indicator
born - Nativity status (whether born in the United States or abroad)
educ - Highest number of years of school completed
degree - Highest educational degree attained (e.g., high school, bachelor's, graduate)
marital - Marital status of the respondent
childs - Total number of children the respondent has
region - US Census region where the interview took place
union1 - Union membership status (whether a member of a labor union)
impjob - Perceived importance of work or job
census_code - Standardized census code used for crosswalk matching
census_title - Standardized textual title for the census occupation
soc2010 - Standard Occupational Classification (SOC) 2010 code used to link with O*NET
n_onet - Diagnostic count of O*NET matches evaluated during the merge
n_with_data - Count of O*NET entries that contained valid survey/score data
n_with_job_zone - Count of entries possessing valid O*NET job zone information
match - Flag indicating the quality or status of the occupation crosswalk match
onet_no_data - Binary flag indicating if the matched O*NET occupation lacked data
partial_substantive - Flag indicating whether a partial or fallback match was used
Achievement - O*NET work value score measuring the importance of accomplishment and results
Independence - O*NET work value score measuring autonomy and independent decision-making
Recognition - O*NET work value score measuring potential for advancement and praise
Relationships - O*NET work value score measuring friendly environments and co-worker support
Support - O*NET work value score measuring supportive management and company policies
Working Conditions - O*NET work value score measuring physical environment comfort and safety
job_zone - O*NET classification score of the education, experience, and training required for the job
has_work_values - Binary flag indicating whether O*NET work values were successfully linked to the respondent

# Feature Categorization for Modeling: GSS and ONET Dataset
* Target Variable
satjob - Respondent's self-reported job satisfaction level

* Baseline Features (GSS Demographics, Economics, and Employment)
Demographics: age, sex, race, hispanic, born, educ, degree, marital, childs, region
Employment and Economics: wrkstat, wrkslf, hrs1, hrs2, weekswrk, realrinc, rincom16, union1, impjob, indus10, prestg10, sei10, occ10

* Person-Job Fit Features (ONET Work Values and Requirements)
Work Values: Achievement, Independence, Recognition, Relationships, Support, Working Conditions
Job Requirements: job_zone

* Administrative and Metadata (To Drop for Modeling)
Identifiers and Weights: id, year, ballot, wtssps, wtssnrps, vpsu, vstrat
Merge and Crosswalk Flags: census_code, census_title, soc2010, n_onet, n_with_data, n_with_job_zone, match, onet_no_data, partial_substantive, has_work_values
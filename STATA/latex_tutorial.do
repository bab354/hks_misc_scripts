/*

This file was written by Blake Barr in 2018 as a way to help others write code
that automates the production of LateX Tables. I use the core functionality
of esttab and write my own headers and footners for the table

Feel free to reach out to me to go over anything
*/
clear all
* PUT YOUR DIRECTORY HERE
global directory "C:/Users/blabarr/hks_misc_scripts"
/*******************************************************************************
* 							PROGRAM REG TABLES
	
	Parameters:
		
		Varlist - Put the dependent Variable that you want to put in the regression
		tex_file (str) - path name to the Latex File you plan on writing
		year_range(int)
				0 - All years (1968 - 1988 in this data)
				1 - 1980 - 1988
*******************************************************************************/			
capture program drop reg_tables
program define reg_tables
	syntax varlist(max = 1), tex_file(str) year_range(int)
	token `varlist'
	local depvar `1'
	***********************************
	* SET UP DEPENDENT VARIABLE LABEL
	***********************************
	local var_title "Wage"
	if regexm("`depvar'", "ln") local var_title "Log(`var_title')"
	*********************
	* SET UP YEAR RANGES
	*********************
	if `year_range' == 0 {
		local year_text "1968-1988"
		local year_cond
	}
	else if `year_range' == 1 {
		local year_text "1980 - 1988"
		local year_cond & year >= 1980
	}
	***********************************************
	* SET TITLE OF TABLE BASED ON CRITERIA ABOVE
	***********************************************
	local title "Regressions for `var_title', years: `year_text'"
	/***********************************************
	RUN 3 PERMUTATIONS:
		- NO EXCLUSIONS
		- COLLEGE GRADS ONLY
		- UNION MEMBERS ONLY
	************************************************/
	forval excl = 0 / 2 {
		* No Exclusion
		if  `excl' == 0      local exclude_cond if inlist(collgrad, 0, 1)
		* College Grads Only
		else if `excl' == 1  local exclude_cond if collgrad == 1
		* Union Members only
		else if `excl' == 2  local exclude_cond if union == 1
		
		* RUN DIFFERENT FIXED EFFECTS
		forval f = 0 / 2 {
			if `f' == 0       local fe i.year i.race i.birth_yr
			else if `f' == 1  local fe i.year i.birth_yr
			else              local fe i.birth_yr race
	
			* Joe also wants F-statistic from first state regression
			qui reghdfe `depvar' tenure hours wks_work ttl_exp `exclude_cond' `year_cond', absorb(`fe') cluster(idcode)
			estimates store regs`excl'_`f'
		}
	}
	***************************
	* REGRESSION TABLE HEADER
	***************************
	file open tex using "`tex_file'", append write
	file write tex  "\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}" _n ///
				    "\begin{table}" _n "\caption{`title'}" _n ///
					"\resizebox{\textwidth}{!} {" _n ///
				    "\begin{tabular}{l*{9}{c}}" _n "\toprule[1.5pt]" _n
	file close tex
	
	************************************
	* FILL TABLE WITH REGRESSIONS ABOVE
	************************************
	esttab regs0* regs1* regs2* using "`tex_file'", append label star(* 0.05 ** 0.01)  b se r2 ///
	fragment nolines nodepvar nomtitles compress
	************************************
	* DENOTE WHICH SAMPLES WE HAVE USED
	************************************
    local sample_lines "Sample & All & All & All & College & College & College & Union & Union & Union \\"
	*******************************************************************
	* CLOSE TABLE WITH Samples used in each regressions along with FE
	*******************************************************************
	file open tex using "`tex_file'", append write
	file write tex      "`sample_lines'" _n ///
						"\cmidrule{1-1}"  _n "Fixed Effects\\" _n "\cmidrule{1-1}" _n ///
						"Year &\checkmark &\checkmark & &\checkmark &\checkmark & &\checkmark &\checkmark & \\" _n ///
						"Race  &\checkmark & &\checkmark &\checkmark & &\checkmark &\checkmark & &\checkmark \\" _n ///
						"Birth Year  &\checkmark &\checkmark &\checkmark &\checkmark &\checkmark &\checkmark &\checkmark &\checkmark  \\" _n ///
						"\hline" _n ///
						"\multicolumn{9}{l}{\footnotesize * p$<$0.05   ** p$<$0.01. Standard errors clustered by person ID} \\" _n ///
						"\end{tabular}" _n   "}" _n "\end{table}" _n
	file close tex
end
********************************************************************************
* 		NOW I WILL USE ABOVE PROGRAM TO CREATE A LATEX FILE WITH TABLE
********************************************************************************
use http://www.stata-press.com/data/r13/nlswork, clear
replace year = year + 1900 //currently year is two digit
tsset idcode year
gen wage = exp(ln_wage)

****************************************
* CREATE LATEX FILE AND DOCUMENT HEADER
****************************************
capture file close tex
local tex_file "$directory/latex_tables.tex"
file open tex using "`tex_file'", replace write
file write  tex  "\documentclass[11pt]{article}" _n  ///
		         "\usepackage{palatino,fullpage,setspace,lscape,rotating,amssymb,booktabs,multirow,hyperref,caption}" _n ///
			     "\begin{document}" _n "\begin{landscape}"
file close tex

************************************************
* Use program to create tables
* Each call of program produces a single table
************************************************
foreach depvar in wage ln_wage {
	* Do all years and 1980s only
	forval y = 0 / 1 {
		reg_tables `depvar', tex_file("`tex_file'") year_range(`y')
	}
}
**************
* CLOSE LATEX
**************
file open tex using "`tex_file'", append write
file write tex  "\end{landscape}"  _n "\end{document}"
file close tex


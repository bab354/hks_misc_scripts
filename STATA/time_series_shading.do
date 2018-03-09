/*
Time - series shading example. Plotting in STATA can be a war. I wanted
to write script in case others want to do time-series plots where some portion
of the graph is shading (ie shading during a recession period etc)
*/
clear all
* PUT YOUR DIRECTORY HERE
global directory "C:/Users/blabarr/hks_misc_scripts"

* GRAPH OPTIONS I ALWAYS USE SINCE STATA DEFAULTS ARE UGLY
global graph_opts scheme(s2gcolor) graphregion(color(white)) plotregion(ilwidth(vthick)) 
/* Going to plot a time-series using a STATA data-set and let's say we 
   want to shade a period that we are on a diet
   
   Let's say we go on a diet from April 15 to June 15
*/

sysuse tsline2, clear
tsset day

local diet_start = td(15apr2002)
local diet_end   = td(15jun2002)
* Need to get the max calories so that our shading goes up to top
* Going to institue a variable only for that range
qui gen on_diet = 4400 if inrange(day, `diet_start', `diet_end')

twoway area on_diet day, bcolor(gs15) astyle(outline) || ///
tsline calories, ///
$graph_opts ytitle("Number of Calories") title("Calories Consumed in 2002") ///
tlabel(, format(%dm)) plotregion(margin(zero)) ylabel(3400 (200) 4400) legend(off)
qui graph export "$directory/STATA/timeseries_shading.png", replace

